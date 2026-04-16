# /// script
# requires-python = ">=3.10"
# dependencies = []
#
# ///

"""Check Pi extension TypeScript files for format, lint, and type errors.

Outputs JSON with format, lint, and typecheck results.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], label: str) -> dict[str, Any]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {"label": label, "exitCode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except FileNotFoundError:
        return {"label": label, "error": f"{cmd[0]} not found"}


def check_format(paths: list[Path], fix: bool) -> dict[str, Any]:
    cmd = ["oxfmt"]
    if fix:
        cmd.append("--write")
    else:
        cmd.append("--check")
    cmd.extend(str(p) for p in paths)

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr

    if result.returncode == 0:
        files = []
        for line in output.strip().splitlines():
            if line.startswith("Would reformat:") or line.startswith("Reformatted:"):
                files.append(line.split(": ", 1)[1].strip())
        return {"status": "pass", "changed": files}
    else:
        changed = []
        for line in output.strip().splitlines():
            if line.startswith("Would reformat:") or line.startswith("Reformatted:"):
                changed.append(line.split(": ", 1)[1].strip())
        return {"status": "fail", "changed": changed}


def check_lint(paths: list[Path]) -> dict[str, Any]:
    cmd = ["oxlint"]
    cmd.extend(str(p) for p in paths)

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr

    errors = []
    for line in output.strip().splitlines():
        stripped = line.strip()
        if " error:" in stripped or " warning:" in stripped:
            parts = stripped.split(":", 3)
            if len(parts) >= 4:
                errors.append({
                    "file": parts[0].strip(),
                    "line": int(parts[1].strip()) if parts[1].strip().isdigit() else 0,
                    "col": int(parts[2].strip()) if parts[2].strip().isdigit() else 0,
                    "message": parts[3].strip(),
                })

    if result.returncode != 0 or errors:
        return {"status": "fail", "errors": errors}
    return {"status": "pass", "errors": []}


def check_typecheck(paths: list[Path]) -> dict[str, Any]:
    cmd = ["tsgo", "--noEmit", "--skipLibCheck"]
    cmd.extend(str(p) for p in paths)

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr

    errors = []
    for line in output.strip().splitlines():
        stripped = line.strip()
        if stripped and "error TS" in stripped:
            parts = stripped.split(":", 2)
            if len(parts) >= 3:
                file_part = parts[0].strip()
                line_col = parts[1].strip()
                line_num = 0
                if "(" in line_col and ")" in line_col:
                    num_part = line_col.split(",")[0].replace("(", "").strip()
                    line_num = int(num_part) if num_part.isdigit() else 0
                errors.append({
                    "file": file_part,
                    "line": line_num,
                    "message": parts[2].strip(),
                })

    if result.returncode != 0:
        return {"status": "fail", "errors": errors}
    return {"status": "pass", "errors": []}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Pi extension TypeScript files")
    parser.add_argument("paths", nargs="+", help="TypeScript files or directories to check")
    parser.add_argument("--fix", action="store_true", help="Auto-fix format issues (oxfmt --write)")
    parser.add_argument("--format-only", action="store_true", help="Run only format check")
    parser.add_argument("--lint-only", action="store_true", help="Run only lint check")
    parser.add_argument("--typecheck-only", action="store_true", help="Run only typecheck")
    args = parser.parse_args()

    paths = [Path(p).resolve() for p in args.paths]

    result: dict[str, Any] = {"paths": [str(p) for p in paths]}

    run_format = not args.lint_only and not args.typecheck_only
    run_lint = not args.format_only and not args.typecheck_only
    run_typecheck = not args.format_only and not args.lint_only

    if run_format:
        result["format"] = check_format(paths, args.fix)
    if run_lint:
        result["lint"] = check_lint(paths)
    if run_typecheck:
        result["typecheck"] = check_typecheck(paths)

    has_fail = any(
        result.get(k, {}).get("status") == "fail"
        for k in ("format", "lint", "typecheck")
    )
    result["overall"] = "fail" if has_fail else "pass"

    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1 if has_fail else 0)


if __name__ == "__main__":
    main()