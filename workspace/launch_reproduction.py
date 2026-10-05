#!/usr/bin/env python3
"""Launch the four unified-games SFT arms in parallel, one GPU each.

Reproduces the official 4-arm experiment (target variant x learning rate) from
TRAINING_RECIPE.md with identical flags; the only addition is --log-every 1
(logging-only, lets the live dashboard show every step).

Usage:
  venv/bin/python launch_reproduction.py --dry-run   # show commands only
  venv/bin/python launch_reproduction.py             # launch all four arms
  venv/bin/python launch_reproduction.py --arms hard_lr1e5 soft_lr1e5
  venv/bin/python launch_reproduction.py --status
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = ROOT / "venv/bin/python"
TRAINER = ROOT / "NanoJev/scripts/train_unified_games.py"
DATA = ROOT / "data/NanoJev-unified"
INIT = ROOT / "checkpoints/NanoJev-unified/training_initialization"
OUT_ROOT = ROOT / "runs/unified_repro"
REGISTRY = OUT_ROOT / "registry.json"

# Official arms. GPUs 1/2/4/6 host another user's vLLM service; only 0/3/5/7 are ours.
ARMS = {
    "hard_lr1e5": {"variant": "hard", "backbone_lr": "1e-5", "head_lr": "1e-4", "gpu": 0},
    "hard_lr2e5": {"variant": "hard", "backbone_lr": "2e-5", "head_lr": "2e-4", "gpu": 3},
    "soft_lr1e5": {"variant": "soft", "backbone_lr": "1e-5", "head_lr": "1e-4", "gpu": 5},
    "soft_lr2e5": {"variant": "soft", "backbone_lr": "2e-5", "head_lr": "2e-4", "gpu": 7},
}


def build_command(name, spec):
    out = OUT_ROOT / name
    cmd = [
        str(PY), str(TRAINER),
        "--input", str(DATA / "unified" / spec["variant"]),
        "--init-checkpoint", str(INIT),
        "--output-dir", str(out),
        "--stage", "sft", "--loss", "ce", "--balance", "task",
        "--policy-pool-weights", str(DATA / "configs/sonic_policy_pool_weights.json"),
        "--steps", "600", "--head-steps", "0", "--seed", "17",
        "--batch-questions", "24", "--microbatch-questions", "8",
        "--max-microbatch-tokens", "32768", "--max-length", "8192",
        "--eval-every", "100", "--backbone-lr", spec["backbone_lr"],
        "--head-lr", spec["head_lr"], "--weight-decay", "0.01",
        "--precision", "bf16", "--gradient-checkpointing",
        "--disable-native-triton",
        "--log-every", "1",
    ]
    return cmd, out


def load_registry():
    if REGISTRY.is_file():
        return json.loads(REGISTRY.read_text())
    return {"runs": {}}


def save_registry(reg):
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(reg, indent=2))


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def cmd_status():
    reg = load_registry()
    if not reg["runs"]:
        print("no runs registered")
        return
    for name, info in sorted(reg["runs"].items()):
        state = "alive" if pid_alive(info["pid"]) else "exited"
        print(f"{name:14s} gpu={info['gpu']} pid={info['pid']:>7} {state:6s} log={info['log']}")
        if state == "exited":
            summary = Path(info["dir"]) / "summary.json"
            print(f"{'':14s} summary={'present' if summary.is_file() else 'MISSING'}")


def cmd_stop(names):
    reg = load_registry()
    for name in names or list(reg["runs"]):
        info = reg["runs"].get(name)
        if not info:
            print(f"{name}: not registered")
            continue
        if pid_alive(info["pid"]):
            os.kill(info["pid"], signal.SIGTERM)
            print(f"{name}: SIGTERM -> {info['pid']}")
        else:
            print(f"{name}: not running")


def cmd_launch(names, dry_run=False):
    reg = load_registry()
    (OUT_ROOT / "logs").mkdir(parents=True, exist_ok=True)
    for name in names:
        spec = ARMS[name]
        cmd, out = build_command(name, spec)
        if out.exists() and any(out.iterdir()):
            print(f"{name}: output dir not empty, skip: {out}")
            continue
        log_path = OUT_ROOT / "logs" / f"{name}.log"
        if dry_run:
            print(f"[dry-run] gpu={spec['gpu']} out={out}")
            print("  " + " ".join(cmd))
            continue
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(spec["gpu"]), PYTHONUNBUFFERED="1")
        with log_path.open("ab") as log_fh:
            proc = subprocess.Popen(cmd, stdout=log_fh, stderr=subprocess.STDOUT,
                                    env=env, cwd=str(ROOT), start_new_session=True)
        reg["runs"][name] = {
            "name": name, "dir": str(out), "gpu": spec["gpu"],
            "cuda_visible_devices": str(spec["gpu"]), "pid": proc.pid,
            "log": str(log_path), "cmd": cmd,
            "launched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        print(f"{name}: launched pid={proc.pid} gpu={spec['gpu']} log={log_path}")
        time.sleep(2)  # stagger startup; dataset validation is CPU-heavy
    if not dry_run:
        save_registry(reg)
        print(f"registry: {REGISTRY}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--arms", nargs="+", choices=sorted(ARMS), help="subset of arms to launch")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--stop", nargs="*", help="stop all, or list arm names")
    args = ap.parse_args()
    if args.status:
        cmd_status()
    elif args.stop is not None:
        cmd_stop(args.stop or None)
    else:
        cmd_launch(args.arms or list(ARMS), args.dry_run)


if __name__ == "__main__":
    main()
