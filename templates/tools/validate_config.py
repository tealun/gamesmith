#!/usr/bin/env python3
"""Validate config/ (template). Run after every config change; exit code 1 lists every error at once.

    python3 tools/validate_config.py [--build-template <path to project.config.json>]

Groups: structure (schema, unique ids) → references → ranges → content rules → teaching pace → build template.
Add a rule every time a playtest bug can be described statically, and prove it: it must report the bad data first.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = ROOT / "config"
GRID = 32
errors = []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def load(rel):
    try:
        return json.loads((CFG / rel).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        err(rel, f"cannot read ({e})")
        return {}


def schema_ok(data, where, version=1):
    if data.get("schema") != version:
        err(where, f"schema must be {version}")


def unique(items, where):
    seen = set()
    for it in items:
        i = it.get("id")
        if not i:
            err(where, f"item without id: {it}")
        elif i in seen:
            err(where, f"duplicate id {i}")
        seen.add(i)
    return seen


# ---- structure
player, entities, levels, solver = load("player.json"), load("entities.json"), load("levels.json"), load("solver.json")
for name, data in (("player.json", player), ("entities.json", entities), ("levels.json", levels), ("solver.json", solver)):
    schema_ok(data, name)
kinds = {e["id"]: e for e in entities.get("entities", [])}
unique(entities.get("entities", []), "entities.json")
chunk_files = sorted((CFG / "chunks").glob("*.json"))
chunks = {}
for f in chunk_files:
    lib = load(f"chunks/{f.name}")
    schema_ok(lib, f"chunks/{f.name}")
    for c in lib.get("chunks", []):
        if c.get("id") in chunks:
            err(f"chunks/{f.name}", f"duplicate chunk id {c.get('id')}")
        chunks[c.get("id")] = c

# ---- ranges (player feel)
RANGES = {"speed": (100, 3000), "gravity": (500, 20000), "jumpVelocity": (100, 5000), "holdGravityFactor": (0, 1),
          "maxJumps": (1, 3), "airJumpRatio": (0, 1.5), "coyoteMs": (0, 200), "inputBufferMs": (0, 300), "hp": (1, 10)}
for k, (lo, hi) in RANGES.items():
    v = player.get(k)
    if not isinstance(v, (int, float)) or not lo <= v <= hi:
        err("player.json", f"{k}={v} outside {lo}..{hi}")

# ---- chunks: references, grid, safe zones, standing rules
for cid, c in chunks.items():
    where = f"chunk {cid}"
    if not re.fullmatch(r"[a-z]+_d\d_\d{2}", cid or ""):
        err(where, "id must look like <scene>_d<difficulty>_<nn>")
    if f"_d{c.get('difficulty')}_" not in (cid or ""):
        err(where, "difficulty does not match the id")
    length, head, tail = c.get("lengthPx", 0), c.get("safeHeadPx", 0), c.get("safeTailPx", 0)
    if length % GRID:
        err(where, f"lengthPx {length} not on the {GRID} px grid")
    blocks = [e for e in c.get("entities", []) if kinds.get(e.get("ref"), {}).get("kind") == "block"]
    for e in c.get("entities", []):
        k = kinds.get(e.get("ref"))
        if not k:
            err(where, f"unknown ref {e.get('ref')}")
            continue
        x, y = e.get("x", 0), e.get("y", 0)
        if k["kind"] != "coin" and (x % GRID or y % GRID):
            err(where, f"{e['ref']} at x={x} y={y} not on the grid")
        if k["kind"] != "coin" and (x < head or x + e.get("w", k.get("w", 0)) > length - tail):
            err(where, f"{e['ref']} at x={x} inside a safe zone (head {head}, tail {tail})")
        # a spike above the ground must stand on a block that rises from the ground (no hazards on floating platforms)
        if k["kind"] == "spike" and y > 0:
            under = [b for b in blocks if b["x"] <= x and x + k.get("w", 0) <= b["x"] + b["w"] and b.get("y", 0) + b["h"] == y]
            if not any(b.get("y", 0) == 0 for b in under):
                err(where, f"{e['ref']} at x={x} is not standing on a block rising from the ground")

# ---- levels: references + teaching pace (at most maxNewPerLevel new teaching units per level)
seen_new = set()
max_new = levels.get("maxNewPerLevel", 2)
unique(levels.get("levels", []), "levels.json")
for lv in levels.get("levels", []):
    where = f"level {lv.get('id')}"
    new_here = set()
    for cid in lv.get("chunks", []):
        if cid not in chunks:
            err(where, f"unknown chunk {cid}")
            continue
        for e in chunks[cid].get("entities", []):
            k = kinds.get(e.get("ref"), {})
            if k.get("counts_as_new") and e["ref"] not in seen_new:
                new_here.add(e["ref"])
    if len(new_here) > max_new:
        err(where, f"{len(new_here)} new teaching units ({', '.join(sorted(new_here))}) > {max_new}")
    seen_new |= new_here
    sp = lv.get("savePointAfter")
    if sp is not None and not 0 < sp < len(lv.get("chunks", [])):
        err(where, f"savePointAfter {sp} outside the level")

# ---- solver lines: every difficulty used by a chunk has its lines
for cid, c in chunks.items():
    d = str(c.get("difficulty"))
    for line in ("speed", "minActionsPerSec", "minWindowMs"):
        if d not in solver.get(line, {}):
            err("solver.json", f"{line} has no value for difficulty {d} (used by {cid})")

# ---- build template (WeChat example): an empty appid puts DevTools in tourist mode; orientation must match the design
if "--build-template" in sys.argv:
    p = pathlib.Path(sys.argv[sys.argv.index("--build-template") + 1])
    try:
        tpl = json.loads(p.read_text(encoding="utf-8"))
        if not re.fullmatch(r"wx[0-9a-f]{16}", tpl.get("appid", "")):
            err(str(p), f"appid {tpl.get('appid')!r} is not wx + 16 hex digits")
    except (OSError, json.JSONDecodeError) as e:
        err(str(p), f"cannot read ({e})")

for e in errors:
    print("ERROR", e)
print(f"validate_config: {len(chunks)} chunks, {len(levels.get('levels', []))} levels, {len(errors)} error(s)")
sys.exit(1 if errors else 0)
