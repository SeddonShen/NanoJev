#!/usr/bin/env python3
"""Live training dashboard: multi-run loss/dev-CE charts, progress, GPU state.

Stdlib only. Watches run directories (registry from launch_reproduction.py plus
any extra dirs), tails train_log.json / initial_dev_metrics.json / summary.json,
samples nvidia-smi, and serves one HTML page + a JSON API.

Usage:
  venv/bin/python dashboard/live_dashboard.py --port 8799
  # optional: --extra-dir runs/smoke_hard_lr1e5 --extra-dir <any run dir>
"""
import argparse
import json
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "runs/unified_repro/registry.json"
HERE = Path(__file__).resolve().parent

PALETTE = ["#4f8ef7", "#f7944f", "#4ff7a0", "#f76fb0", "#b44ff7", "#f7e34f"]


class RunWatcher:
    """Parses one run directory; re-reads files only when their mtime changes."""

    def __init__(self, name, run_dir, gpu=None, pid=None, log=None):
        self.name, self.dir = name, Path(run_dir)
        self.gpu, self.pid, self.log = gpu, pid, log
        self.color = None  # assigned by the server in registry order
        self._mtime = {}
        self._cache = {"config": None, "log": None, "initial": None, "summary": None}

    def _read(self, key, rel, expect_type=dict):
        path = self.dir / rel
        try:
            mtime = path.stat().st_mtime
        except OSError:
            self._mtime[rel] = None
            return None
        if self._mtime.get(rel) == mtime:
            return self._cache[key]
        try:
            with path.open(encoding="utf-8") as fh:
                value = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return self._cache[key]  # mid-write; keep previous parse
        if not isinstance(value, expect_type):
            value = None
        self._mtime[rel] = mtime
        self._cache[key] = value
        return value

    def _log_tail(self, limit=4000):
        if not self.log:
            return ""
        try:
            data = Path(self.log).read_bytes()
            return data[-limit:].decode("utf-8", errors="replace")
        except OSError:
            return ""

    def state(self):
        config = self._read("config", "config.json") or {}
        entries = self._read("log", "train_log.json", expect_type=list) or []
        initial = self._read("initial", "initial_dev_metrics.json")
        summary = self._read("summary", "summary.json")
        total = int(config.get("steps", 0)) + int(config.get("head_steps", 0))
        last = entries[-1] if entries else None
        loss_series = [[e["step"], round(e["loss"], 5)] for e in entries if "loss" in e]
        step_times = [(e["step"], e["elapsed_seconds"]) for e in entries if "elapsed_seconds" in e]
        sec_per_step = None
        if len(step_times) >= 2:
            head = step_times[-min(len(step_times), 25):-1] or step_times[:1]
            first_s, first_t = head[0]
            last_s, last_t = step_times[-1]
            if last_s > first_s and last_t > first_t:
                sec_per_step = (last_t - first_t) / (last_s - first_s)
        dev_points = []
        if initial and isinstance(initial.get("selection_ce"), (int, float)):
            dev_points.append({"step": 0, "selection_ce": initial["selection_ce"]})
        for e in entries:
            dev = e.get("dev")
            if dev and isinstance(dev.get("selection_ce"), (int, float)):
                point = {"step": e["step"], "selection_ce": dev["selection_ce"]}
                by_task = dev.get("by_task_role") or {}
                point["by_task"] = {k: round(v.get("ce"), 4) for k, v in by_task.items()
                                    if isinstance(v.get("ce"), (int, float))}
                by_pool = dev.get("by_selection_pool") or {}
                point["by_pool"] = {k: round(v.get("ce"), 4) for k, v in by_pool.items()
                                    if isinstance(v.get("ce"), (int, float))}
                dev_points.append(point)
        best = min(dev_points, key=lambda p: p["selection_ce"]) if dev_points else None
        elapsed = last.get("elapsed_seconds") if last else None
        step = last["step"] if last else 0
        eta = None
        if sec_per_step and total:
            eta = max(0.0, (total - step) * sec_per_step)
        alive = False
        if self.pid:
            try:
                os.kill(self.pid, 0)
                alive = True
            except (ProcessLookupError, PermissionError):
                alive = False
        variant = "hard" if "/hard" in str(config.get("input", "")) else \
                  ("soft" if "/soft" in str(config.get("input", "")) else "?")
        return {
            "name": self.name, "dir": str(self.dir), "gpu": self.gpu, "pid": self.pid,
            "alive": alive, "finished": summary is not None,
            "variant": variant,
            "backbone_lr": config.get("backbone_lr"), "head_lr": config.get("head_lr"),
            "loss": last.get("loss") if last else None,
            "grad_norm": last.get("gradient_norm_before_clip") if last else None,
            "phase": last.get("phase") if last else "starting",
            "step": step, "total_steps": total,
            "loss_series": loss_series,
            "dev_points": dev_points,
            "best": best, "sec_per_step": sec_per_step,
            "elapsed_s": elapsed, "eta_s": eta,
            "summary": {"best_step": summary.get("best_step"),
                        "best_dev_selection_ce": summary.get("best_dev_selection_ce"),
                        "training_seconds": summary.get("training_seconds"),
                        "max_gpu_allocated_gb": summary.get("max_gpu_allocated_gb")}
                       if summary else None,
            "log_tail": self._log_tail(),
        }


class Monitor:
    def __init__(self, extra_dirs=()):
        self.watchers = []
        self._lock = threading.Lock()
        self.gpu_state = []
        self.pid_gpu = {}
        reg = {}
        try:
            reg = json.loads(REGISTRY.read_text()) if REGISTRY.is_file() else {}
        except (OSError, json.JSONDecodeError):
            pass
        for name, info in (reg.get("runs") or {}).items():
            self.watchers.append(RunWatcher(name, info["dir"], info.get("gpu"),
                                            info.get("pid"), info.get("log")))
        for extra in extra_dirs:
            path = Path(extra)
            if (path / "train_log.json").exists() or (path / "config.json").exists():
                self.watchers.append(RunWatcher(path.name, path))
        for i, watcher in enumerate(self.watchers):
            watcher.color = PALETTE[i % len(PALETTE)]
        threading.Thread(target=self._gpu_loop, daemon=True).start()

    def _gpu_loop(self):
        while True:
            try:
                self.gpu_state, self.pid_gpu = self._sample_gpus()
            except Exception:
                pass
            time.sleep(2)

    @staticmethod
    def _sample_gpus():
        query = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5)
        gpus = []
        for line in query.stdout.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 4:
                gpus.append({"index": int(parts[0]), "util": int(parts[1]),
                             "mem_used": int(parts[2]), "mem_total": int(parts[3])})
        apps = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,gpu_uuid,used_memory",
             "--format=csv,noheader"], capture_output=True, text=True, timeout=5)
        uuid_index = {}
        uuids = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5)
        for line in uuids.stdout.strip().splitlines():
            idx, _, uuid = line.partition(",")
            uuid_index[uuid.strip()] = int(idx)
        pid_gpu = {}
        for line in apps.stdout.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2 and parts[1] in uuid_index:
                mem = None
                if len(parts) > 2:
                    digits = "".join(ch for ch in parts[2] if ch.isdigit())
                    mem = int(digits) if digits else None
                pid_gpu[int(parts[0])] = {"index": uuid_index[parts[1]], "mem_used": mem}
        return gpus, pid_gpu

    def state(self):
        with self._lock:
            runs = []
            for watcher in self.watchers:
                run = watcher.state()
                run["color"] = watcher.color
                live = self.pid_gpu.get(watcher.pid) if watcher.pid else None
                if live and live["index"] == watcher.gpu:
                    run["gpu_live"] = {"mem_used": live["mem_used"]}
                runs.append(run)
            ours = {run["gpu"] for run in runs if run["gpu"] is not None}
            for gpu in self.gpu_state:
                gpu["ours"] = gpu["index"] in ours
            return {"server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "gpus": self.gpu_state, "runs": runs}


class Handler(BaseHTTPRequestHandler):
    monitor = None

    def do_GET(self):
        if self.path.startswith("/api/state"):
            body = json.dumps(self.monitor.state()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        elif self.path in ("/", "/index.html"):
            body = (HERE / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            body = b"not found"
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8799)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--extra-dir", action="append", default=[])
    args = ap.parse_args()
    Handler.monitor = Monitor(args.extra_dir)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"dashboard: http://127.0.0.1:{args.port}  (watching {len(Handler.monitor.watchers)} runs)")
    server.serve_forever()


if __name__ == "__main__":
    main()
