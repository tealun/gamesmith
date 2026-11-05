#!/usr/bin/env python3
"""Build the WorkBuddy package of gamesmith: one skill folder with exactly one SKILL.md.

Usage:
    python3 scripts/build_suite.py            # build dist/gamesmith-workbuddy.zip and dist/gamesmith-workbuddy/
    python3 scripts/build_suite.py --check    # validate the sources and the package, write nothing

Output (dist/ is never committed; release.yml attaches the zips to the GitHub Release):
    dist/gamesmith-workbuddy.zip               folder gamesmith/ inside; upload this to WorkBuddy
    dist/gamesmith-workbuddy/                  unpacked package (inspect before uploading); dist/gamesmith/ belongs
                                               to build_plugin.py, so the two builds never overwrite each other
    dist/gamesmith-workbuddy-<version>-flat.zip  SKILL.md at the zip root, for platforms that need it

gamesmith is a single skill, so unlike dev-pdca there is no suite entry: the package is the skill folder, and its
SKILL.md gets WorkBuddy's display fields (workbuddy/frontmatter.json) and the version (.claude-plugin/plugin.json,
the only source of the version). Every known WorkBuddy rule is listed in docs/workbuddy-rules.md with the check
below that enforces it, or the reason it is not checked. The build is deterministic (sorted entries, fixed
timestamps, LF line endings).
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "gamesmith"
PLUGIN_JSON = REPO / ".claude-plugin" / "plugin.json"
WORKBUDDY_FIELDS = REPO / "workbuddy" / "frontmatter.json"
DIST = REPO / "dist"
NAME = "gamesmith"
ZIP = DIST / f"{NAME}-workbuddy.zip"
UNPACKED = DIST / f"{NAME}-workbuddy"
TEXT_SUFFIXES = {".md", ".py", ".mjs", ".js", ".ts", ".yaml", ".yml", ".json", ".txt", ""}
FIXED_TIME = (2020, 1, 1, 0, 0, 0)
DESCRIPTION_LIMIT = 1024                      # Agent Skills spec
NAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
WORKBUDDY_TEXT_LIMITS = {"display_name_en": 60, "description_zh": 500, "description_en": 1000}
REQUIRED = ("display_name", "display_name_en", "description_zh", "description_en", "examples_zh", "examples_en")
MAX_EXAMPLES = 3
# The SKILL.md fields Claude reads; anything else belongs in workbuddy/frontmatter.json.
SKILL_FIELDS = {"name", "description"}

# Files that serve repository maintenance or local runs, not the agent.
EXCLUDE_PATTERNS = [re.compile(p) for p in (r"^__pycache__$", r"\.pyc$", r"^\.DS_Store$", r"^Thumbs\.db$",
                                            r"^node_modules$", r"^preview_out$")]


def excluded(name: str) -> bool:
    return any(p.search(name) for p in EXCLUDE_PATTERNS)


def read_normalized(src: Path) -> bytes:
    data = src.read_bytes()
    if src.suffix in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return data


def split_frontmatter(text: str) -> tuple[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise SystemExit("gamesmith/SKILL.md: missing YAML frontmatter")
    return m.group(1), text[m.end():]


def parse_frontmatter(block: str) -> dict:
    """A small reader for the frontmatter we write: `key: "json string"`, `key: plain`, and `key:` followed by
    `  - "json string"` items. Used to read the source SKILL.md and to read the generated one back."""
    fields: dict = {}
    key = None
    for line in block.splitlines():
        km = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if km:
            key, value = km.group(1), km.group(2).strip()
            if value == "":
                fields[key] = []
            elif value.startswith('"'):
                fields[key] = json.loads(value)
            else:
                fields[key] = value
        elif key is not None and re.match(r"^\s+- ", line):
            item = line.strip()[2:].strip()
            fields[key].append(json.loads(item) if item.startswith('"') else item)
        elif line.strip():
            raise SystemExit(f"frontmatter line not understood: {line!r}")
    return fields


def version() -> str:
    return json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]


def package_frontmatter() -> dict:
    src, _ = split_frontmatter((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
    fm = parse_frontmatter(src)
    extra = {k: v for k, v in json.loads(WORKBUDDY_FIELDS.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    # WorkBuddy uses `description` for its list and recall and expects it to equal description_zh
    # (docs/workbuddy-rules.md); Claude keeps the bilingual trigger description in gamesmith/SKILL.md
    return {"name": fm.get("name"), "description": extra.get("description_zh"), **extra, "version": version()}


def render_frontmatter(fields: dict) -> str:
    lines = []
    for k, v in fields.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            lines += [f"  - {json.dumps(x, ensure_ascii=False)}" for x in v]
        else:
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    return "---\n" + "\n".join(lines) + "\n---\n"


def validate() -> str:
    errors: list[str] = []
    src, _ = split_frontmatter((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
    src_fields = parse_frontmatter(src)
    if set(src_fields) != SKILL_FIELDS:
        errors.append(f"gamesmith/SKILL.md frontmatter fields {sorted(src_fields)}, expected {sorted(SKILL_FIELDS)} "
                      f"(version lives in plugin.json, WorkBuddy fields in workbuddy/frontmatter.json)")
    fm = package_frontmatter()
    if fm.get("name") != NAME:
        errors.append(f"name must be {NAME!r}, got {fm.get('name')!r}")
    if not NAME_PATTERN.fullmatch(fm.get("name") or ""):
        errors.append("name must match ^[a-z0-9][a-z0-9-]{0,39}$")
    if (fm.get("name") or "").startswith("workbuddy-"):
        errors.append("name must not start with workbuddy- (reported as reserved by the platform)")
    if fm.get("description") != fm.get("description_zh"):
        errors.append("package description must equal description_zh")
    if re.search(r"\s", fm.get("display_name") or ""):
        errors.append("display_name must not contain spaces (a paid listing rejects them; keep it valid from the start)")
    src_desc = src_fields.get("description") or ""
    if not 1 <= len(src_desc) <= DESCRIPTION_LIMIT:
        errors.append(f"gamesmith/SKILL.md description is {len(src_desc)} chars, limit {DESCRIPTION_LIMIT}")
    desc = fm.get("description") or ""
    if not 1 <= len(desc) <= DESCRIPTION_LIMIT:
        errors.append(f"description is {len(desc)} chars, limit {DESCRIPTION_LIMIT}")
    for field in REQUIRED:
        if not fm.get(field):
            errors.append(f"WorkBuddy field {field} is missing")
    for field, limit in WORKBUDDY_TEXT_LIMITS.items():
        if len(fm.get(field) or "") > limit:
            errors.append(f"{field} is {len(fm[field])} chars, WorkBuddy allows {limit}")
    for field in ("examples_zh", "examples_en"):
        items = fm.get(field) or []
        if not isinstance(items, list) or not 1 <= len(items) <= MAX_EXAMPLES:
            errors.append(f"{field} must be a list of 1-{MAX_EXAMPLES} items")
    if not re.fullmatch(r"\d+\.\d+\.\d+", fm.get("version") or ""):
        errors.append(f"version must be MAJOR.MINOR.PATCH, got {fm.get('version')!r}")
    if errors:
        raise SystemExit("validation failed:\n  " + "\n  ".join(errors))
    return fm["version"]


def package_files() -> list[tuple[str, Path]]:
    """(path inside the package, source file), sorted. root/second-level/file at most (the zip adds gamesmith/)."""
    entries = []
    for f in sorted(SKILL_DIR.rglob("*")):
        inner = f.relative_to(SKILL_DIR)
        if not f.is_file() or any(excluded(part) for part in inner.parts):
            continue
        entries.append((inner.as_posix(), f))
    entries.append(("LICENSE", REPO / "LICENSE"))
    return sorted(entries)


def content(rel: str, src: Path) -> bytes:
    data = read_normalized(src)
    if rel == "SKILL.md":
        _, body = split_frontmatter(data.decode("utf-8"))
        data = (render_frontmatter(package_frontmatter()) + body).encode("utf-8")
    return data


def validate_package(entries: list[tuple[str, Path]]) -> None:
    errors = []
    for rel, _ in entries:
        if rel.count("/") > 1:
            errors.append(f"{NAME}/{rel}: deeper than root/second-level/file")
    skill_files = [rel for rel, _ in entries if rel.rsplit("/", 1)[-1].lower() == "skill.md"]
    if skill_files != ["SKILL.md"]:
        errors.append(f"package must hold exactly one SKILL.md at its root, found {skill_files}")
    for rel, src in entries:
        data = content(rel, src)
        if data.startswith(b"\xef\xbb\xbf"):
            errors.append(f"{rel} starts with a UTF-8 BOM")
        if src.suffix in TEXT_SUFFIXES:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                errors.append(f"{rel} is not UTF-8")
                continue
            if rel != "SKILL.md" and rel.endswith(".md") and re.match(r"\A---\n(?:.*\n)*?name:", text):
                errors.append(f"{rel} carries skill frontmatter; WorkBuddy would read it as a second skill")
    # the generated frontmatter must read back as the same fields (valid YAML: every value is a JSON string)
    block, _ = split_frontmatter(content("SKILL.md", SKILL_DIR / "SKILL.md").decode("utf-8"))
    if parse_frontmatter(block) != package_frontmatter():
        errors.append("generated SKILL.md frontmatter does not read back as the intended fields")
    try:
        import yaml  # optional: a second, independent YAML reader when it is installed
        if yaml.safe_load(block) != package_frontmatter():
            errors.append("generated SKILL.md frontmatter is not the same under a YAML parser")
    except ImportError:
        pass
    if errors:
        raise SystemExit("package check failed:\n  " + "\n  ".join(errors))


def make_zip(entries: list[tuple[str, Path]], prefix: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, src in entries:
            info = zipfile.ZipInfo(prefix + rel, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, content(rel, src))
    return buf.getvalue()


def check_builds(entries: list[tuple[str, Path]]) -> None:
    data = make_zip(entries, f"{NAME}/")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        if zf.testzip() is not None or len(zf.namelist()) != len(entries):
            raise SystemExit("WorkBuddy package did not build cleanly")
    print(f"ok: {NAME} WorkBuddy package builds ({len(data) // 1024} KB, {len(entries)} files)")


def build(ver: str, entries: list[tuple[str, Path]]) -> None:
    DIST.mkdir(exist_ok=True)
    ZIP.write_bytes(make_zip(entries, f"{NAME}/"))
    out = UNPACKED
    if out.exists():
        shutil.rmtree(out)
    for rel, src in entries:
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content(rel, src))
    flat = DIST / f"{NAME}-workbuddy-{ver}-flat.zip"
    flat.write_bytes(make_zip(entries, ""))
    print(f"wrote {ZIP.relative_to(REPO).as_posix()}, {flat.relative_to(REPO).as_posix()} and {out.relative_to(REPO).as_posix()}/ ({len(entries)} files, version {ver})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    args = ap.parse_args()
    ver = validate()
    fm = package_frontmatter()
    print(f"ok: {NAME} {ver}, description {len(fm['description'])}/{DESCRIPTION_LIMIT}, "
          f"description_zh {len(fm['description_zh'])}/500, description_en {len(fm['description_en'])}/1000")
    entries = package_files()
    validate_package(entries)
    if args.check:
        check_builds(entries)
    else:
        build(ver, entries)
    return 0


if __name__ == "__main__":
    sys.exit(main())
