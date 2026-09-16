#!/usr/bin/env python3
"""
check_pyqt_pylance.py - Deterministic static pattern and syntax scanner
for PyQt (PyQt5/PyQt6/PySide) and QFluentWidgets codebases.

Detects common Pylance / Pyright type-stub pitfalls:
- Chained .horizontalHeader() or .verticalHeader() without None guards
- Chained .item(row, col).text() without None guards
- Legacy flat Qt.Align* instead of scoped Qt.AlignmentFlag.*
- Known hallucinated FluentIcon attributes
- Syntax check via py_compile
"""
import os
import sys
import re
import py_compile
import argparse

# Force UTF-8 on Windows console if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PATTERNS = [
    {
        "id": "UNGUARDED_HEADER",
        "regex": re.compile(r'\.(horizontalHeader|verticalHeader)\(\)\.[a-zA-Z_]'),
        "severity": "ERROR",
        "message": "Chained header access on Optional[QHeaderView]. Narrow with 'header = table.horizontalHeader(); if header is not None:'"
    },
    {
        "id": "UNGUARDED_TABLE_ITEM_TEXT",
        "regex": re.compile(r'\.item\([^)]+\)\.text\(\)'),
        "severity": "ERROR",
        "message": "Chained .item().text() on Optional[QTableWidgetItem]. Narrow with 'item = table.item(r, c); if item is not None:'"
    },
    {
        "id": "UNSCOPED_QT_ALIGN",
        "regex": re.compile(r'\bQt\.(Align(Left|Right|HCenter|Justify|Top|Bottom|VCenter|Center))\b'),
        "severity": "WARNING",
        "message": "Flat Qt.Align* may trigger reportAttributeAccessIssue in Pylance. Use Qt.AlignmentFlag.Align*."
    },
    {
        "id": "INVALID_FIF_POWER",
        "regex": re.compile(r'\bFIF\.POWER\b'),
        "severity": "ERROR",
        "message": "FluentIcon has no 'POWER' attribute. Use FIF.PAUSE, FIF.SYNC, FIF.CLOSE, or FIF.CANCEL."
    }
]


def check_file(filepath: str) -> list:
    issues = []
    
    # 1. Syntax Check
    try:
        py_compile.compile(filepath, doraise=True)
    except py_compile.PyCompileError as e:
        issues.append({
            "file": filepath,
            "line": 0,
            "id": "SYNTAX_ERROR",
            "severity": "FATAL",
            "message": str(e)
        })
        return issues

    # 2. Pattern Scans
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
            lines = fp.readlines()
    except Exception as e:
        issues.append({
            "file": filepath,
            "line": 0,
            "id": "FILE_READ_ERROR",
            "severity": "FATAL",
            "message": str(e)
        })
        return issues

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        for pat in PATTERNS:
            if pat["regex"].search(line):
                # Avoid false positives if already scoped
                if pat["id"] == "UNSCOPED_QT_ALIGN" and "AlignmentFlag" in line:
                    continue
                issues.append({
                    "file": filepath,
                    "line": idx,
                    "id": pat["id"],
                    "severity": pat["severity"],
                    "message": pat["message"],
                    "code": stripped
                })

    return issues


def scan_directory(target_dir: str) -> list:
    all_issues = []
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.endswith(".py"):
                p = os.path.join(root, f)
                issues = check_file(p)
                all_issues.extend(issues)
    return all_issues


def main():
    parser = argparse.ArgumentParser(description="Scan PyQt/QFluentWidgets files for Pylance pitfalls.")
    parser.add_argument("target", help="File or directory path to inspect.")
    args = parser.parse_args()

    target = os.path.abspath(args.target)
    if os.path.isfile(target):
        issues = check_file(target)
    elif os.path.isdir(target):
        issues = scan_directory(target)
    else:
        print(f"Error: Target path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    if not issues:
        print(f"[PASSED] No Pylance/PyQt common pitfalls detected in {target}")
        sys.exit(0)

    print(f"[WARNING] Found {len(issues)} issue(s) in {target}:\n")
    for issue in issues:
        loc = f"{issue['file']}:{issue['line']}"
        print(f"[{issue['severity']}] {loc} ({issue['id']})")
        print(f"    Message: {issue['message']}")
        if "code" in issue:
            print(f"    Code:    {issue['code']}")
        print()

    sys.exit(1 if any(i['severity'] in ('ERROR', 'FATAL') for i in issues) else 0)


if __name__ == "__main__":
    main()
