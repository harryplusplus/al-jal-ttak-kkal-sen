# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml",
# ]
# ///
"""Comprehensive review of an Agent Skill directory.

Runs spec validation, code quality checks, and quality assessment.
Outputs structured JSON review results.

Usage:
    uv run scripts/review.py <skill_dir> [--skip-typecheck]

Exit codes:
    0: Review passed (may have suggestions)
    1: Critical issues found
    2: Usage error
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import yaml

# --- Local parsing utilities (self-contained) ---


def find_skill_md(skill_dir: Path) -> Path | None:
    """Find SKILL.md in a skill directory. Prefers uppercase."""
    for name in ("SKILL.md", "skill.md"):
        path = skill_dir / name
        if path.exists():
            return path
    return None


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from SKILL.md content."""
    if not content.startswith("---"):
        raise ValueError("SKILL.md must start with YAML frontmatter (---)")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("SKILL.md frontmatter not properly closed with ---")

    frontmatter_str = parts[1]
    body = parts[2].strip()

    try:
        raw_metadata: Any = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}") from e

    if raw_metadata is None:
        raise ValueError("SKILL.md frontmatter is empty")

    if not isinstance(raw_metadata, dict):
        raise ValueError("SKILL.md frontmatter must be a YAML mapping")

    metadata = cast(dict[str, Any], raw_metadata)

    meta_field = metadata.get("metadata")
    if isinstance(meta_field, dict):
        typed_meta = cast(dict[str, Any], meta_field)
        metadata["metadata"] = {str(k): str(v) for k, v in typed_meta.items()}

    return metadata, body


def read_skill_md(skill_dir: Path) -> tuple[dict[str, Any], str, Path]:
    """Find and parse SKILL.md from a skill directory."""
    skill_dir = Path(skill_dir).resolve()
    skill_md = find_skill_md(skill_dir)

    if skill_md is None:
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

    content = skill_md.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(content)
    return metadata, body, skill_md


def output_json(data: dict[str, Any]) -> None:
    """Print data as JSON to stdout."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def error_exit(message: str, code: int = 1) -> None:
    """Print error as JSON to stderr and exit."""
    print(json.dumps({"error": message}, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


# --- Quality checks ---


def check_description_quality(description: str) -> list[dict[str, Any]]:
    """Assess description quality beyond spec compliance."""
    findings: list[dict[str, Any]] = []

    if len(description) < 30:
        findings.append(
            {
                "severity": "critical",
                "category": "description",
                "message": (
                    "Description is too short to be effective for agent "
                    "discovery. Aim for at least 50 characters with "
                    "specific keywords and trigger conditions."
                ),
            }
        )
    elif len(description) < 80:
        findings.append(
            {
                "severity": "warning",
                "category": "description",
                "message": (
                    "Description may be too brief. Effective descriptions "
                    "include what the skill does AND when to use it, with "
                    "specific keywords for agent matching."
                ),
            }
        )

    # Check for imperative phrasing
    imperative_patterns = [
        r"use this skill when",
        r"use when",
        r"activate when",
        r"~할 때 사용",
        r"사용하세요",
    ]
    has_imperative = any(re.search(p, description, re.IGNORECASE) for p in imperative_patterns)
    if not has_imperative:
        findings.append(
            {
                "severity": "suggestion",
                "category": "description",
                "message": (
                    "Consider using imperative phrasing like 'Use this "
                    "skill when...' to help agents decide when to activate."
                ),
            }
        )

    # Check for trigger conditions
    if not re.search(r"when|if|때|경우|시", description, re.IGNORECASE):
        findings.append(
            {
                "severity": "warning",
                "category": "description",
                "message": (
                    "Description lacks trigger conditions. Agents need to "
                    "know WHEN to activate this skill, not just what it does."
                ),
            }
        )

    # Check for implementation-only description
    impl_patterns = [
        r"^(a |an |the )?[a-z]+ (that |which |to )?"
        r"(uses|runs|calls|executes|invokes)",
    ]
    if any(re.search(p, description, re.IGNORECASE) for p in impl_patterns):
        findings.append(
            {
                "severity": "warning",
                "category": "description",
                "message": (
                    "Description focuses on implementation rather than "
                    "user intent. Describe what the user wants to achieve, "
                    "not how the skill works internally."
                ),
            }
        )

    return findings


def check_body_quality(body: str) -> list[dict[str, Any]]:
    """Assess SKILL.md body quality."""
    findings: list[dict[str, Any]] = []

    if not body.strip():
        findings.append(
            {
                "severity": "critical",
                "category": "body",
                "message": "SKILL.md body is empty — add instructions.",
            }
        )
        return findings

    lines = body.splitlines()
    line_count = len(lines)

    has_when_to_use = any(
        re.search(
            r"when to use|사용.*때|사용 시|전제 조건",
            line,
            re.IGNORECASE,
        )
        for line in lines
    )
    has_instructions = any(
        re.search(
            r"instruction|지시|사용법|워크플로우|workflow|step",
            line,
            re.IGNORECASE,
        )
        for line in lines
    )
    has_gotchas = any(
        re.search(
            r"gotcha|주의|주의사항|caveat|pitfall",
            line,
            re.IGNORECASE,
        )
        for line in lines
    )

    if not has_when_to_use:
        findings.append(
            {
                "severity": "suggestion",
                "category": "body",
                "message": (
                    "Consider adding a 'When to use this skill' section "
                    "to help agents understand activation conditions."
                ),
            }
        )

    if not has_instructions:
        findings.append(
            {
                "severity": "warning",
                "category": "body",
                "message": (
                    "No clear instructions section found. Agents need "
                    "step-by-step guidance when the skill is activated."
                ),
            }
        )

    if not has_gotchas:
        findings.append(
            {
                "severity": "suggestion",
                "category": "body",
                "message": (
                    "Consider adding a 'Gotchas' section for non-obvious "
                    "facts that agents might get wrong. This is often the "
                    "highest-value section in a skill."
                ),
            }
        )

    if line_count > 500:
        findings.append(
            {
                "severity": "warning",
                "category": "body",
                "message": (
                    f"SKILL.md body is {line_count} lines (recommended: "
                    "under 500). Move detailed content to references/ "
                    "or assets/ for progressive disclosure."
                ),
            }
        )

    # Check for placeholder text
    placeholders: list[tuple[str, str]] = [
        (r"\[describe", "description placeholder"),
        (r"\[list", "list placeholder"),
        (r"\[step", "step placeholder"),
        (r"todo\b", "TODO marker"),
        (r"fixme\b", "FIXME marker"),
        (r"xxx\b", "XXX marker"),
    ]
    for pattern, label in placeholders:
        if re.search(pattern, body, re.IGNORECASE):
            findings.append(
                {
                    "severity": "critical",
                    "category": "body",
                    "message": f"SKILL.md contains unfilled {label}.",
                }
            )

    return findings


def check_scripts(skill_dir: Path) -> list[dict[str, Any]]:
    """Check scripts/ directory quality."""
    findings: list[dict[str, Any]] = []
    scripts_dir = skill_dir / "scripts"

    if not scripts_dir.exists():
        findings.append(
            {
                "severity": "info",
                "category": "scripts",
                "message": "No scripts/ directory — skill is text-only.",
            }
        )
        return findings

    py_files = list(scripts_dir.glob("*.py"))
    if not py_files:
        findings.append(
            {
                "severity": "info",
                "category": "scripts",
                "message": "No Python scripts found in scripts/.",
            }
        )
        return findings

    for py_file in py_files:
        if py_file.name.startswith("_"):
            continue  # Skip private modules like _common.py
        content = py_file.read_text(encoding="utf-8")

        # Check PEP 723 inline metadata
        if not re.search(r"# /// script\n", content):
            findings.append(
                {
                    "severity": "warning",
                    "category": "scripts",
                    "message": (
                        f"{py_file.name}: Missing PEP 723 inline script "
                        "metadata. Add `# /// script` block for `uv run`."
                    ),
                }
            )

        # Check for interactive input (anti-pattern)
        if re.search(r"input\(", content):
            findings.append(
                {
                    "severity": "critical",
                    "category": "scripts",
                    "message": (
                        f"{py_file.name}: Uses input() — agents cannot "
                        "respond to interactive prompts. Use CLI arguments "
                        "or environment variables instead."
                    ),
                }
            )

        # Check for JSON output
        has_json_output = bool(re.search(r"json\.dumps", content))
        if not has_json_output:
            findings.append(
                {
                    "severity": "suggestion",
                    "category": "scripts",
                    "message": (
                        f"{py_file.name}: Consider outputting results as JSON for programmatic consumption by agents."
                    ),
                }
            )

        # Check for argparse
        has_argparse = bool(re.search(r"argparse", content))
        has_sys_argv = bool(re.search(r"sys\.argv", content))
        if not has_argparse and not has_sys_argv:
            findings.append(
                {
                    "severity": "suggestion",
                    "category": "scripts",
                    "message": (
                        f"{py_file.name}: No CLI argument parsing detected. Consider using argparse for clear --help."
                    ),
                }
            )

    return findings


def check_structure(skill_dir: Path) -> list[dict[str, Any]]:
    """Check directory structure conventions."""
    findings: list[dict[str, Any]] = []

    skill_md = skill_dir / "SKILL.md"
    skill_md_lower = skill_dir / "skill.md"
    if skill_md_lower.exists() and not skill_md.exists():
        findings.append(
            {
                "severity": "suggestion",
                "category": "structure",
                "message": ("Using skill.md (lowercase). SKILL.md (uppercase) is the preferred convention."),
            }
        )

    evals_dir = skill_dir / "evals"
    if not evals_dir.exists():
        findings.append(
            {
                "severity": "info",
                "category": "structure",
                "message": (
                    "No evals/ directory. Consider adding evals/evals.json "
                    "with test cases for evaluating skill quality."
                ),
            }
        )

    return findings


# --- External tool integration ---


def run_external_checks(skill_dir: Path, skip_typecheck: bool) -> list[dict[str, Any]]:
    """Run validate.py and check.py from agent-skills-dev via subprocess."""
    findings: list[dict[str, Any]] = []

    # Find agent-skills-python-dev scripts directory
    review_skill_dir = Path(__file__).resolve().parent.parent
    skills_root = review_skill_dir.parent
    dev_scripts = skills_root / "agent-skills-dev" / "scripts"
    python_dev_scripts = skills_root / "agent-skills-python-dev" / "scripts"

    if not dev_scripts.exists():
        findings.append(
            {
                "severity": "info",
                "category": "tooling",
                "message": (
                    f"agent-skills-dev scripts not found at {dev_scripts}."
                    " Skipping validate."
                ),
            }
        )
        return findings

    # Run validate
    validate_proc = subprocess.run(
        ["uv", "run", str(dev_scripts / "validate.py"), str(skill_dir)],
        capture_output=True,
        text=True,
    )
    if validate_proc.returncode != 0:
        try:
            val_result: dict[str, Any] = json.loads(validate_proc.stdout)
            for err in val_result.get("errors", []):
                findings.append(
                    {
                        "severity": "critical",
                        "category": "spec",
                        "message": f"Validation: {err}",
                    }
                )
            for warn in val_result.get("warnings", []):
                findings.append(
                    {
                        "severity": "warning",
                        "category": "spec",
                        "message": f"Validation: {warn}",
                    }
                )
        except json.JSONDecodeError:
            pass

    if not python_dev_scripts.exists():
        findings.append(
            {
                "severity": "info",
                "category": "tooling",
                "message": (
                    f"agent-skills-python-dev scripts not found at"
                    f" {python_dev_scripts}. Skipping check."
                ),
            }
        )
        return findings

    # Run check (format + lint, optionally typecheck)
    # Pass scripts/ subdirectory if it exists for correct import resolution
    check_target = str(skill_dir)
    scripts_subdir = skill_dir / "scripts"
    if scripts_subdir.exists():
        check_target = str(scripts_subdir)

    check_cmd = ["uv", "run", str(python_dev_scripts / "check.py"), check_target]
    if skip_typecheck:
        check_cmd.extend(["--format-only", "--lint-only"])

    check_proc = subprocess.run(
        check_cmd,
        capture_output=True,
        text=True,
    )
    if check_proc.returncode != 0:
        try:
            chk_result: dict[str, Any] = json.loads(check_proc.stdout)
            fmt = chk_result.get("format", {})
            if fmt.get("status") == "fail":
                findings.append(
                    {
                        "severity": "warning",
                        "category": "format",
                        "message": ("Code formatting issues found. Run `uv run scripts/check.py --fix` to auto-fix."),
                    }
                )
            lint = chk_result.get("lint", {})
            for err in lint.get("errors", []):
                findings.append(
                    {
                        "severity": "warning",
                        "category": "lint",
                        "message": (
                            f"Lint: {err.get('file', '')}:{err.get('line', 0)} "
                            f"[{err.get('code', '')}] {err.get('message', '')}"
                        ),
                    }
                )
            tc = chk_result.get("typecheck", {})
            for err in tc.get("errors", []):
                findings.append(
                    {
                        "severity": "warning",
                        "category": "typecheck",
                        "message": (
                            f"Type: {err.get('file', '')}:{err.get('line', 0)} "
                            f"[{err.get('code', '')}] {err.get('message', '')}"
                        ),
                    }
                )
        except json.JSONDecodeError:
            pass

    return findings


# --- Main review ---


def review(skill_dir: Path, skip_typecheck: bool = False) -> dict[str, Any]:
    """Run comprehensive review of a skill directory."""
    skill_dir = Path(skill_dir).resolve()
    all_findings: list[dict[str, Any]] = []
    counts: dict[str, int] = {
        "critical": 0,
        "warning": 0,
        "suggestion": 0,
        "info": 0,
    }

    def _add(findings: list[dict[str, Any]]) -> None:
        for f in findings:
            all_findings.append(f)
            sev = f.get("severity", "info")
            if sev in counts:
                counts[sev] += 1

    # 1. Parse SKILL.md
    try:
        metadata, body, _skill_md_path = read_skill_md(skill_dir)
    except (FileNotFoundError, ValueError) as e:
        return {
            "skill_dir": str(skill_dir),
            "status": "fail",
            "findings": [
                {
                    "severity": "critical",
                    "category": "spec",
                    "message": str(e),
                }
            ],
            "summary": {"critical": 1, "warning": 0, "suggestion": 0, "info": 0},
        }

    # 2. Description quality
    desc = metadata.get("description", "")
    if isinstance(desc, str):
        _add(check_description_quality(desc))

    # 3. Body quality
    _add(check_body_quality(body))

    # 4. Scripts quality
    _add(check_scripts(skill_dir))

    # 5. Structure conventions
    _add(check_structure(skill_dir))

    # 6. External tool checks (validate + check)
    _add(run_external_checks(skill_dir, skip_typecheck))

    status = "fail" if counts["critical"] > 0 else "pass"

    return {
        "skill_dir": str(skill_dir),
        "status": status,
        "findings": all_findings,
        "summary": counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Comprehensive review of an Agent Skill directory.",
        epilog=(
            "Examples:\n  uv run scripts/review.py ./my-skill\n  uv run scripts/review.py ./my-skill --skip-typecheck\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "skill_path",
        help="Path to the skill directory (or SKILL.md file)",
    )
    parser.add_argument(
        "--skip-typecheck",
        action="store_true",
        help="Skip pyright type checking (faster review)",
    )
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if skill_path.is_file() and skill_path.name.lower() == "skill.md":
        skill_path = skill_path.parent

    result = review(skill_path, skip_typecheck=args.skip_typecheck)
    output_json(result)
    sys.exit(0 if result["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
