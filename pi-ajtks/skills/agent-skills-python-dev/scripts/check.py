# /// script
# requires-python = ">=3.10"
# ///
"""Check Agent Skill Python scripts with ruff and pyright.

Uses configuration bundled in the skill's assets/ directory — works
independently of any project-level pyproject.toml or ruff.toml.
Requires uv (uvx) to be available.

Usage:
    uv run scripts/check.py <path>... [--fix] [--format-only] [--lint-only] [--typecheck-only]

Exit codes:
    0: All checks pass
    1: One or more checks fail
    2: Usage error
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

# Resolve skill directory relative to this script
SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"


def _output_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _error_exit(message: str, code: int = 1) -> None:
    print(json.dumps({"error": message}, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command, capturing stdout and stderr."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        _error_exit(f"Command not found: {cmd[0]}. Is uv/uvx installed and on PATH?")
        raise  # unreachable, but satisfies type checker


def check_format(paths: list[str], fix: bool, config_path: str) -> dict[str, Any]:
    """Run ruff format check or fix."""
    cmd = ["uvx", "ruff", "format", "--config", config_path]
    if not fix:
        cmd.append("--check")
    cmd.extend(paths)

    proc = _run(cmd)

    changed: list[str] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line and not line.startswith("--") and "files" not in line:
            changed.append(line)

    return {
        "status": "pass" if proc.returncode == 0 else "fail",
        "changed": changed,
    }


def check_lint(paths: list[str], fix: bool, config_path: str) -> dict[str, Any]:
    """Run ruff lint check or fix."""
    cmd = [
        "uvx",
        "ruff",
        "check",
        "--config",
        config_path,
        "--output-format",
        "json",
    ]
    if fix:
        cmd.append("--fix")
    cmd.extend(paths)

    proc = _run(cmd)

    errors: list[dict[str, Any]] = []
    if proc.stdout:
        try:
            diagnostics: list[dict[str, Any]] = json.loads(proc.stdout)
            for d in diagnostics:
                code_raw: Any = d.get("code", "")
                if isinstance(code_raw, dict):
                    code_dict = cast(dict[str, Any], code_raw)
                    code_str = str(code_dict.get("value", ""))
                else:
                    code_str = str(code_raw)
                errors.append(
                    {
                        "file": d.get("filename", ""),
                        "line": d.get("location", {}).get("row", 0),
                        "col": d.get("location", {}).get("column", 0),
                        "code": code_str,
                        "message": d.get("message", ""),
                        "fixable": d.get("fix") is not None,
                    }
                )
        except json.JSONDecodeError:
            if proc.returncode != 0:
                errors.append(
                    {
                        "file": "",
                        "line": 0,
                        "col": 0,
                        "code": "parse-error",
                        "message": proc.stdout.strip(),
                        "fixable": False,
                    }
                )

    fixable = sum(1 for e in errors if e.get("fixable"))

    return {
        "status": "pass" if proc.returncode == 0 else "fail",
        "errors": errors,
        "fixable": fixable,
    }


def check_types(paths: list[str], project_dir: str) -> dict[str, Any]:
    """Run pyright type check."""
    cmd = [
        "uvx",
        "--with",
        "types-PyYAML",
        "pyright",
        "--project",
        project_dir,
        "--outputjson",
    ]
    cmd.extend(paths)

    proc = _run(cmd)

    errors: list[dict[str, Any]] = []
    if proc.stdout:
        try:
            data: dict[str, Any] = json.loads(proc.stdout)
            for d in data.get("generalDiagnostics", []):
                errors.append(
                    {
                        "file": d.get("file", ""),
                        "line": (d.get("range", {}).get("start", {}).get("line", 0) + 1),
                        "col": (d.get("range", {}).get("start", {}).get("character", 0) + 1),
                        "code": d.get("rule", ""),
                        "message": d.get("message", ""),
                        "severity": d.get("severity", ""),
                    }
                )
        except json.JSONDecodeError:
            pass

    return {
        "status": "pass" if proc.returncode == 0 else "fail",
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check Agent Skill Python scripts with ruff and pyright.",
        epilog=(
            "Examples:\n"
            "  uv run scripts/check.py scripts/\n"
            "  uv run scripts/check.py scripts/validate.py --fix\n"
            "  uv run scripts/check.py scripts/ --typecheck-only\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to check")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix issues where possible",
    )
    parser.add_argument(
        "--format-only",
        action="store_true",
        help="Only check formatting",
    )
    parser.add_argument(
        "--lint-only",
        action="store_true",
        help="Only run lint checks",
    )
    parser.add_argument(
        "--typecheck-only",
        action="store_true",
        help="Only run type checks",
    )
    args = parser.parse_args()

    run_format = not args.lint_only and not args.typecheck_only
    run_lint = not args.format_only and not args.typecheck_only
    run_typecheck = not args.format_only and not args.lint_only

    # Verify asset configs exist
    ruff_config = ASSETS_DIR / "ruff.toml"
    pyright_config = ASSETS_DIR / "pyrightconfig.json"
    if not ruff_config.exists():
        _error_exit(f"Missing ruff config: {ruff_config}")
    if run_typecheck and not pyright_config.exists():
        _error_exit(f"Missing pyright config: {pyright_config}")

    results: dict[str, Any] = {"paths": args.paths}
    overall_pass = True

    if run_format:
        results["format"] = check_format(args.paths, args.fix, str(ruff_config))
        if results["format"]["status"] == "fail":
            overall_pass = False

    if run_lint:
        results["lint"] = check_lint(args.paths, args.fix, str(ruff_config))
        if results["lint"]["status"] == "fail":
            overall_pass = False

    if run_typecheck:
        # pyright --project needs a directory containing pyrightconfig.json
        # We dynamically add extraPaths so pyright can resolve sibling imports
        with tempfile.TemporaryDirectory() as tmpdir:
            pyright_dir = Path(tmpdir) / "project"
            pyright_dir.mkdir()
            base_config: dict[str, Any] = json.loads(pyright_config.read_text(encoding="utf-8"))
            # Collect unique directories containing the target .py files
            script_dirs: list[str] = list({str(Path(p).resolve().parent) for p in args.paths if Path(p).is_file()})
            if not script_dirs:
                # If paths are directories, add them directly
                script_dirs = [str(Path(p).resolve()) for p in args.paths]
            existing_extra: list[str] = base_config.get("extraPaths", [])
            base_config["extraPaths"] = list(dict.fromkeys(existing_extra + script_dirs))
            (pyright_dir / "pyrightconfig.json").write_text(json.dumps(base_config, indent=2), encoding="utf-8")
            results["typecheck"] = check_types(args.paths, str(pyright_dir))
            if results["typecheck"]["status"] == "fail":
                overall_pass = False

    results["overall"] = "pass" if overall_pass else "fail"
    _output_json(results)
    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
