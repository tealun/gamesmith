#!/usr/bin/env python3
"""Check the evolution ledger and the compliance log.

Evolution ledger (docs/98_evolution/evolution-ledger.md): unique IDs,
well-formed rows. append_evolution_ledger.py rejects a duplicate ID only at
append time; two branches can each append the same ID and the merge brings
both in.

Compliance log (docs/98_evolution/compliance-log.md): every record row has 7
columns and allowed values, so rows appended by hand or by the weekly audit
cannot drift from the format the statistics depend on.

CI runs this on every push and pull request.

Usage: python3 scripts/check_ledger.py [path-to-ledger]
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

EVOLUTION_DIR = Path(__file__).resolve().parent.parent / "docs" / "98_evolution"
DEFAULT = EVOLUTION_DIR / "evolution-ledger.md"
COMPLIANCE = EVOLUTION_DIR / "compliance-log.md"
ID_PATTERN = re.compile(r"EV-\d{8}-\d{3}")
COLUMNS = 8

COMPLIANCE_COLUMNS = 7
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
GATES = {"G1", "G2", "G3", "G4", "G5"}
APPLICABLE = {"是", "不适用"}
COMPLIED = {"是", "部分", "否", "—"}
RECORDED_BY = {"自评", "独立"}


def cells(row: str) -> list[str]:
    """Split a markdown table row on unescaped pipes."""
    inner = row.strip()[1:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", inner)]


def check_ledger(path: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    ids: list[str] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("| EV-"):
            continue
        row = cells(line)
        if len(row) != COLUMNS:
            errors.append(f"{path.name} line {n}: {len(row)} columns, expected {COLUMNS}")
        if not ID_PATTERN.fullmatch(row[0]):
            errors.append(f"{path.name} line {n}: malformed ID {row[0]!r}")
        ids.append(row[0])
    for dup, count in Counter(ids).items():
        if count > 1:
            errors.append(f"{path.name}: duplicate ID {dup} appears {count} times")
    return errors, len(ids)


def check_compliance(path: Path) -> tuple[list[str], int]:
    """Validate record rows: lines in a table that start with a date cell."""
    errors: list[str] = []
    rows = 0
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not re.match(r"^\| \d{4}-", line):
            continue
        rows += 1
        where = f"{path.name} line {n}"
        row = cells(line)
        if len(row) != COMPLIANCE_COLUMNS:
            errors.append(f"{where}: {len(row)} columns, expected {COMPLIANCE_COLUMNS}")
            continue
        date, _cycle, gate, applicable, complied, evidence, recorded_by = row
        if not DATE_PATTERN.fullmatch(date):
            errors.append(f"{where}: date {date!r} is not YYYY-MM-DD")
        if gate not in GATES:
            errors.append(f"{where}: gate {gate!r} not in {sorted(GATES)}")
        if applicable not in APPLICABLE:
            errors.append(f"{where}: 适用 {applicable!r} not in {sorted(APPLICABLE)}")
        if complied not in COMPLIED:
            errors.append(f"{where}: 遵守 {complied!r} not in {sorted(COMPLIED)}")
        if applicable == "不适用" and complied != "—":
            errors.append(f"{where}: 不适用 rows must have 遵守 '—'")
        if applicable == "是" and complied == "—":
            errors.append(f"{where}: applicable rows need a verdict, not '—'")
        if not evidence:
            errors.append(f"{where}: empty evidence")
        if recorded_by not in RECORDED_BY:
            errors.append(f"{where}: 记录方式 {recorded_by!r} not in {sorted(RECORDED_BY)}")
    return errors, rows


def main() -> int:
    ledger = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    errors, ledger_rows = check_ledger(ledger)
    compliance_rows = 0
    if len(sys.argv) == 1 and COMPLIANCE.exists():
        more, compliance_rows = check_compliance(COMPLIANCE)
        errors += more
    if errors:
        print("ledger check failed:\n  " + "\n  ".join(errors))
        return 1
    print(f"ok: {ledger_rows} ledger rows, IDs unique; {compliance_rows} compliance rows well-formed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
