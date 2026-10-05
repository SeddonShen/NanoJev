#!/usr/bin/env python3
"""Build episodes.json for the dataset viewer: parse dev.jsonl states per task.

Extracts, per episode step, a compact render description (maze grid, snake
board, shooting boxes), the offered choices, and the training target
(Jev teacher distribution or expert gold action). First N episodes per task.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "static" / "episodes.json"
EPISODES_PER_TASK = 4


def parse_maze(state):
    goal = re.search(r"reach goal \[(\d+),(\d+)\]", state)
    agent = re.search(r"Agent coordinate: \((\d+),(\d+)\)", state)
    local = re.search(r"Local map:\n(.{5}\n.{5}\n.{5}\n.{5}\n.{5})", state)
    rows = re.findall(r"^(\d+):\S+", state, re.M)
    cols = re.search(r"x(\d+)", state)
    events = re.search(r"Recent physical events: (.*)$", state, re.M)
    used = re.search(r"Used: (\d+)\. Remaining: (\d+)", state)
    return {
        "goal": [int(goal.group(1)), int(goal.group(2))] if goal else None,
        "agent": [int(agent.group(1)), int(agent.group(2))] if agent else None,
        "local_map": local.group(1).split("\n") if local else [],
        "rows": len(rows),
        "cols": int(cols.group(1)) if cols else 8,
        "events": events.group(1)[:160] if events else "",
        "used": int(used.group(1)) if used else None,
    }


def parse_snake(state):
    body = re.search(r"Body head first: (\[\[.*?\]\])", state)
    food = re.search(r"Current food: \[(\d+),(\d+)\]", state)
    board = re.search(r"Snake on a (\d+)x(\d+) board", state)
    direction = re.search(r"Direction: (\w+)", state)
    collected = re.search(r"Food collected this episode: (\d+)", state)
    remaining = re.search(r"Remaining: (\d+)", state)
    return {
        "body": json.loads(body.group(1)) if body else [],
        "food": [int(food.group(1)), int(food.group(2))] if food else None,
        "rows": int(board.group(1)) if board else 8,
        "cols": int(board.group(2)) if board else 8,
        "direction": direction.group(1) if direction else "",
        "collected": int(collected.group(1)) if collected else 0,
        "remaining": int(remaining.group(1)) if remaining else None,
    }


def parse_shooting(state):
    s = json.loads(state)
    history = s.get("observed_history", [])
    frames = [{
        "tick": f.get("episode_tick"), "health": f.get("health"), "ammo": f.get("ammo"),
        "labels": [{"name": l["name"], "bbox": l["bbox"]} for l in f.get("visible_labels", [])],
    } for f in history[-3:]]
    return {
        "scenario": s.get("scenario"),
        "screen": s.get("screen_size", [320, 240]),
        "remaining_decisions": s.get("remaining_decisions"),
        "remaining_ticks": s.get("remaining_ticks"),
        "history_len": len(history),
        "frames": frames,
        "terminal": s.get("terminal"),
    }


def main(src=None):
    if src is None:
        src = next((a for a in sys.argv[1:] if not a.startswith("-")),
                   ROOT / "data/NanoJev-unified/unified/hard/dev.jsonl")
    rows = [json.loads(line) for line in open(src, encoding="utf-8") if line.strip()]
    by_task = defaultdict(lambda: defaultdict(list))
    for row in rows:
        meta = row["metadata"]
        task = f"{meta['task']}_{meta.get('spec', {}).get('scenario')}" if meta["task"] == "shooting" else meta["task"]
        episode = meta.get("episode_id") or row["state_id"]
        qid, q = next(iter(row["questions"].items()))
        target = None
        if row.get("teacher") and qid in (row["teacher"].get("native_probs") or {}):
            target = {"kind": "jev_probs", "probs": row["teacher"]["native_probs"][qid]}
        elif row.get("gold") and qid in row["gold"]:
            target = {"kind": "expert_gold", "gold": row["gold"][qid]}
        elif row.get("gold_probs") and qid in (row["gold_probs"] or {}):
            target = {"kind": "soft_probs", "probs": row["gold_probs"][qid]}
        executed = meta.get("executed_action")
        step = {
            "i": meta.get("decision_index", 0),
            "state_id": row["state_id"][:12],
            "choices": [{"id": cid, "text": txt} for cid, txt in (q.get("criteria") or {}).items()],
            "target": target,
            "executed": executed if isinstance(executed, str) else json.dumps(executed),
            "episode_success": meta.get("episode_success"),
            "raw_state": row["state"],
        }
        parser = {"maze": parse_maze, "snake": parse_snake}.get(meta["task"])
        if meta["task"] == "shooting":
            step["render"] = parse_shooting(row["state"])
        elif parser:
            step["render"] = parser(row["state"])
        by_task[task][episode].append(step)
    out = {}
    for task, episodes in sorted(by_task.items()):
        kept = []
        for episode_id, steps in sorted(episodes.items(), key=lambda kv: min(s["i"] for s in kv[1]))[:EPISODES_PER_TASK]:
            steps.sort(key=lambda s: s["i"])
            kept.append({
                "episode_id": episode_id[:16],
                "n_steps": len(steps),
                "success": steps[-1].get("episode_success"),
                "steps": steps,
            })
        out[task] = kept
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False))
    print(f"wrote {OUT}: " + ", ".join(f"{t}={len(v)}局" for t, v in out.items()))


if __name__ == "__main__":
    main()
