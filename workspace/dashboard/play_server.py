#!/usr/bin/env python3
"""Live game play: run a trained checkpoint inside the unified game envs.

Each decision: env observation (exact training-format state text + candidates)
goes to one deployed serve_decisions instance; the returned distribution picks
the action (greedy by default). The full episode is returned for animated
playback in play.html. Maze/Snake render client-side; ViZDoom frames come back
as base64 PNG.

Usage: venv/bin/python dashboard/play_server.py --port 8821
"""
import argparse
import base64
import io
import json
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "NanoJev/scripts"))

INSTRUCTIONS = ("Choose the next action that maximizes the probability of completing "
                "the stated task successfully before its deadline. Use the visible "
                "state, action descriptions, remaining time, and recorded history.")

GAMES = {
    "maze": {"label": "迷宫", "spec": {"task": "maze", "size": 12, "max_steps": 160}},
    "snake": {"label": "贪吃蛇", "spec": {"task": "snake", "size": 8, "max_steps": 96, "target_food": 2}},
    "basic": {"label": "射击 Basic", "spec": {"task": "shooting", "scenario": "basic"}},
    "predict_position": {"label": "射击 Predict Position", "spec": {"task": "shooting", "scenario": "predict_position"}},
}


def ask_model(port, state, candidates):
    body = json.dumps({"states": [{"id": "play", "state": state,
                                   "questions": {"action": {"type": "choice",
                                                            "instructions": INSTRUCTIONS,
                                                            "criteria": candidates}}}]}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/evaluate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
    return data["states"][0]["answers"]["action"]["probabilities"]


def doom_frame(env):
    state = env._game.get_state()
    if state is None:
        return None
    from PIL import Image
    img = Image.fromarray(state.screen_buffer)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def play_episode(model_port, game, seed, epsilon):
    if game in ("maze", "snake"):
        from unified_grid_envs import UnifiedMazeEnv, UnifiedSnakeEnv
        spec = dict(GAMES[game]["spec"])
        env = (UnifiedMazeEnv if game == "maze" else UnifiedSnakeEnv)(spec)
    else:
        from unified_doom_env import UnifiedDoomEnv
        env = UnifiedDoomEnv(dict(GAMES[game]["spec"]))
    is_doom = game in ("basic", "predict_position")
    try:
        obs, info = env.reset(seed)
        import random
        rng = random.Random(seed + 999)
        steps, done, trunc = [], False, False
        while not done and not trunc and obs.get("candidates"):
            offered = dict(obs["candidates"])
            seen_state = obs["state"]
            if len(offered) >= 2:  # server rejects Choice with fewer than 2 candidates
                probs = ask_model(model_port, seen_state, offered)
                if epsilon and rng.random() < epsilon:
                    chosen = rng.choice(sorted(offered))
                else:
                    chosen = max(sorted(probs), key=lambda k: probs.get(k, 0))
            else:
                probs, chosen = {a: 1.0 for a in offered}, next(iter(offered))
            frame = doom_frame(env) if is_doom else None
            obs, reward, done, trunc, step_info = env.step(chosen)
            steps.append({
                "decision": len(steps) + 1,
                "state": seen_state,
                "candidates": offered,
                "probs": probs, "chosen": chosen,
                "success": step_info.get("success", (step_info.get("episode_metrics") or {}).get("success")),
                "outcome": step_info.get("outcome") or (step_info.get("episode_metrics") or {}).get("outcome"),
                "events": step_info.get("physical_events", [])[:3],
                "metrics": step_info.get("episode_metrics"),
                "frame": frame,
            })
        final = steps[-1] if steps else {}
        outcome = final.get("outcome") or (final.get("metrics") or {}).get("outcome")
        return {"ok": True, "game": game, "seed": seed,
                "n_decisions": len(steps),
                "success": bool(final.get("success") or (final.get("metrics") or {}).get("success")),
                "outcome": outcome or "no_step",
                "steps": steps}
    finally:
        env.close()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html", "/play"):
            self._send(200, (Path(__file__).parent / "play.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/games":
            self._send(200, json.dumps(GAMES, ensure_ascii=False).encode())
        else:
            self._send(404, b"not found")

    def do_POST(self):
        if self.path != "/api/play":
            self._send(404, b"not found")
            return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        try:
            result = play_episode(int(body["model_port"]), body["game"],
                                  int(body.get("seed", 17)), float(body.get("epsilon", 0)))
            self._send(200, json.dumps(result, ensure_ascii=False).encode())
        except Exception as exc:
            import traceback
            self._send(500, json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}",
                                        "trace": traceback.format_exc()[-1500:]}).encode())

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8821)
    args = ap.parse_args()
    print(f"play server: http://127.0.0.1:{args.port}")
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
