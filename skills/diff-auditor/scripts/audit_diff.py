#!/usr/bin/env python3
"""
audit_diff.py - Git Diff Boundary & Semantic Change Auditor

Audits git diffs for common agent and developer pitfalls before committing or PR creation:
- Unintentional docstring and comment deletions
- Stray debug statements (print, console.log, debugger, pdb, breakpoint, etc.)
- Out-of-scope file modifications
- Excessive line churn / whole-file replacement patterns
- Accidental staging of secret / sensitive files (.env, keys, credentials)
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Color output helpers
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Patterns for stray debug statements by file extension
DEBUG_PATTERNS = {
    r"\.(py|pyi)$": [
        (
            re.compile(r"^\+\s*print\(.*?\)", re.IGNORECASE),
            "Stray Python `print(...)` statement",
        ),
        (
            re.compile(
                r"^\+\s*(import\s+pdb|pdb\.set_trace\(\)|breakpoint\(\))", re.IGNORECASE
            ),
            "Python breakpoint/debugger statement",
        ),
        (
            re.compile(r"^\+\s*ic\(.*?\)", re.IGNORECASE),
            "IceCream `ic(...)` debug statement",
        ),
    ],
    r"\.(js|jsx|ts|tsx|mjs|cjs)$": [
        (
            re.compile(r"^\+\s*console\.(log|debug|trace|dir)\(.*?\)", re.IGNORECASE),
            "Stray JS/TS `console.log(...)` statement",
        ),
        (
            re.compile(r"^\+\s*debugger\s*;?", re.IGNORECASE),
            "JavaScript `debugger;` statement",
        ),
    ],
    r"\.(go)$": [
        (
            re.compile(
                r"^\+\s*(fmt\.Print|fmt\.Println|fmt\.Printf)\(.*?\)", re.IGNORECASE
            ),
            "Stray Go `fmt.Print*` statement",
        ),
    ],
    r"\.(rb)$": [
        (
            re.compile(r"^\+\s*(puts|p|pp)\s+", re.IGNORECASE),
            "Stray Ruby `puts/p/pp` statement",
        ),
        (
            re.compile(r"^\+\s*binding\.(pry|irb)", re.IGNORECASE),
            "Ruby `binding.pry/irb` statement",
        ),
    ],
    r"\.(rs)$": [
        (
            re.compile(r"^\+\s*println!\s*\(.*?\)", re.IGNORECASE),
            "Stray Rust `println!` statement",
        ),
        (
            re.compile(r"^\+\s*dbg!\s*\(.*?\)", re.IGNORECASE),
            "Stray Rust `dbg!` statement",
        ),
    ],
    r"\.(php)$": [
        (
            re.compile(r"^\+\s*(var_dump|print_r|dd)\(.*?\)", re.IGNORECASE),
            "Stray PHP dump statement",
        ),
    ],
}

# Sensitive or out-of-scope file patterns
SENSITIVE_PATTERNS = [
    re.compile(r"(^|/)\.env(\.[a-zA-Z0-9_-]+)?$"),
    re.compile(r"\.(key|pem|pkcs12|pfx)$", re.IGNORECASE),
    re.compile(r"(^|/)(id_rsa|id_ed25519)$", re.IGNORECASE),
    re.compile(
        r"(^|/)(secrets|credentials|service-account|auth_token)\.(json|yaml|yml|txt)$",
        re.IGNORECASE,
    ),
]

# Patterns representing docstrings / comments in diff deletion lines (starting with '-')
DOCSTRING_DELETION_PATTERNS = [
    re.compile(r"^-\s*('''|\"\"\")"),  # Python docstring triple-quotes
    re.compile(r"^-\s*\*\s+.*"),  # JSDoc / C-style multi-line comment body
    re.compile(r"^-\s*/\*\*"),  # JSDoc start
    re.compile(r"^-\s*///\s+.*"),  # Rust / C# doc comments
    re.compile(r"^-\s*#\s+.*"),  # Python/Shell/Ruby comments
    re.compile(r"^-\s*//\s+.*"),  # JS/TS/Go/C++ single line comments
]


def run_cmd(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Execute a subprocess command and return (exit_code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd else None,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except (OSError, subprocess.SubprocessError) as e:
        return 1, "", str(e)


def get_git_diff(
    staged: bool = False,
    base: str | None = None,
    commit_range: str | None = None,
    paths: list[str] | None = None,
) -> str:
    """Retrieve git diff based on provided targeting options."""
    cmd = ["git", "diff", "--no-color"]
    if staged:
        cmd.append("--cached")
    elif commit_range:
        cmd.append(commit_range)
    elif base:
        cmd.append(f"{base}...HEAD")

    if paths:
        cmd.append("--")
        cmd.extend(paths)

    code, out, err = run_cmd(cmd)
    if code != 0:
        raise RuntimeError(f"Failed to get git diff: {err.strip()}")
    return out


def get_git_numstat(
    staged: bool = False,
    base: str | None = None,
    commit_range: str | None = None,
    paths: list[str] | None = None,
) -> dict[str, tuple[int, int]]:
    """Get insertion and deletion counts per file using git diff --numstat."""
    cmd = ["git", "diff", "--numstat"]
    if staged:
        cmd.append("--cached")
    elif commit_range:
        cmd.append(commit_range)
    elif base:
        cmd.append(f"{base}...HEAD")

    if paths:
        cmd.append("--")
        cmd.extend(paths)

    code, out, _err = run_cmd(cmd)
    if code != 0:
        return {}

    stats = {}
    for line in out.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            added, deleted, filepath = parts[0], parts[1], parts[2]
            try:
                stats[filepath] = (int(added), int(deleted))
            except ValueError:
                stats[filepath] = (0, 0)
    return stats


from typing import TypedDict


class ParsedDiffFile(TypedDict):
    old_path: str
    new_path: str
    lines: list[str]
    added_lines: list[str]
    deleted_lines: list[str]


def parse_diff_files(raw_diff: str) -> list[ParsedDiffFile]:
    """Parse unified diff output into structured per-file records."""
    files: list[ParsedDiffFile] = []
    current_file: ParsedDiffFile | None = None
    file_header_pattern = re.compile(r"^diff --git a/(.*?) b/(.*)$")

    for line in raw_diff.splitlines():
        m_file = file_header_pattern.match(line)
        if m_file:
            if current_file:
                files.append(current_file)
            current_file = {
                "old_path": m_file.group(1),
                "new_path": m_file.group(2),
                "lines": [],
                "added_lines": [],
                "deleted_lines": [],
            }
            continue

        if current_file is not None:
            current_file["lines"].append(line)
            if line.startswith("+") and not line.startswith("+++"):
                current_file["added_lines"].append(line)
            elif line.startswith("-") and not line.startswith("---"):
                current_file["deleted_lines"].append(line)

    if current_file:
        files.append(current_file)

    return files


def is_test_or_cli_file(filepath: str) -> bool:
    """Check if the file is a test suite or dedicated CLI executable where console output is standard."""
    test_patterns = [
        r"(^|/)(test_|tests/|_test\.(py|js|ts|rb|go|rs|php)$|\.test\.|\.spec\.)",
    ]
    cli_patterns = [
        r"(^|/)(cli/|bin/|scripts/.*cli.*\.py$)",
    ]
    return any(
        re.search(pat, filepath, re.IGNORECASE) for pat in test_patterns + cli_patterns
    )


def audit_diff(
    diff_text: str,
    numstat: dict[str, tuple[int, int]],
    allowed_patterns: list[re.Pattern] | None = None,
    max_churn_lines: int = 500,
    check_docstrings: bool = True,
    check_debug: bool = True,
    check_churn: bool = True,
    check_sensitive: bool = True,
) -> dict:
    """Run all audit checks against the parsed git diff."""
    parsed_files = parse_diff_files(diff_text)
    issues = []
    warnings = []

    total_added = sum(stat[0] for stat in numstat.values())
    total_deleted = sum(stat[1] for stat in numstat.values())

    for f in parsed_files:
        filepath = f["new_path"] if f["new_path"] != "/dev/null" else f["old_path"]
        added_count, deleted_count = numstat.get(
            filepath, (len(f["added_lines"]), len(f["deleted_lines"]))
        )

        # 1. Check sensitive files
        if check_sensitive:
            for pat in SENSITIVE_PATTERNS:
                if pat.search(filepath):
                    issues.append(
                        {
                            "file": filepath,
                            "type": "SENSITIVE_FILE",
                            "severity": "ERROR",
                            "message": f"Sensitive or credential file staged/modified: {filepath}",
                        }
                    )

        # 2. Check scope restrictions (if allowed patterns provided)
        if allowed_patterns:
            matched = any(pat.search(filepath) for pat in allowed_patterns)
            if not matched:
                warnings.append(
                    {
                        "file": filepath,
                        "type": "OUT_OF_SCOPE",
                        "severity": "WARNING",
                        "message": f"File modification outside allowed scope: {filepath}",
                    }
                )

        # 3. Check excessive line churn
        if check_churn and (added_count + deleted_count > max_churn_lines):
            warnings.append(
                {
                    "file": filepath,
                    "type": "EXCESSIVE_CHURN",
                    "severity": "WARNING",
                    "message": f"High line churn in {filepath} (+{added_count}/-{deleted_count} lines > threshold {max_churn_lines}). Ensure you did not overwrite the entire file unintentionally.",
                }
            )

        # 4. Check stray debug statements in added lines
        if check_debug and not is_test_or_cli_file(filepath):
            for ext_pat, rules in DEBUG_PATTERNS.items():
                if re.search(ext_pat, filepath, re.IGNORECASE):
                    for line in f["added_lines"]:
                        # Allow explicit suppression comments
                        if any(
                            tag in line
                            for tag in (
                                "# noqa",
                                "# debug-ok",
                                "// noqa",
                                "// debug-ok",
                                "/* noqa */",
                            )
                        ):
                            continue
                        for pattern, desc in rules:
                            if pattern.search(line):
                                issues.append(
                                    {
                                        "file": filepath,
                                        "type": "DEBUG_STATEMENT",
                                        "severity": "ERROR",
                                        "line": line.lstrip("+").strip(),
                                        "message": f"Found stray debug statement in {filepath}: '{line.lstrip('+').strip()}' ({desc})",
                                    }
                                )

        # 5. Check unintentional docstring or comment mass deletion
        if check_docstrings:
            deleted_doc_lines = []
            in_multiline_docstring = False
            docstring_delimiter = None

            for line in f["deleted_lines"]:
                stripped = line.lstrip("-").strip()

                # Check if we're starting a multi-line docstring
                if not in_multiline_docstring:
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        delimiter = '"""' if stripped.startswith('"""') else "'''"
                        deleted_doc_lines.append(stripped)
                        # Check if this is a one-line docstring (opening and closing on same line)
                        if stripped.count(delimiter) >= 2 and len(stripped) > len(delimiter):
                            # One-line docstring, don't enter multi-line mode
                            pass
                        else:
                            # Multi-line docstring started
                            in_multiline_docstring = True
                            docstring_delimiter = delimiter
                        continue

                # If we're inside a multi-line docstring, count every deleted line
                if in_multiline_docstring:
                    deleted_doc_lines.append(stripped)
                    # Check if this line closes the docstring
                    if docstring_delimiter in stripped:
                        in_multiline_docstring = False
                        docstring_delimiter = None
                    continue

                # Otherwise, check against other comment patterns
                for pat in DOCSTRING_DELETION_PATTERNS:
                    if pat.search(line):
                        deleted_doc_lines.append(stripped)
                        break

            # If more than 3 docstring/comment lines were deleted, or a high ratio
            if (
                len(deleted_doc_lines) >= 3
                and len(deleted_doc_lines) > len(f["added_lines"]) * 0.5
            ):
                warnings.append(
                    {
                        "file": filepath,
                        "type": "DOCSTRING_DELETION",
                        "severity": "WARNING",
                        "deleted_count": len(deleted_doc_lines),
                        "message": f"Possible accidental deletion of {len(deleted_doc_lines)} docstring/comment lines in {filepath}. Verify comments were not stripped accidentally.",
                    }
                )

    return {
        "summary": {
            "files_changed": len(parsed_files),
            "total_added": total_added,
            "total_deleted": total_deleted,
            "error_count": len(issues),
            "warning_count": len(warnings),
            "passed": len(issues) == 0,
        },
        "errors": issues,
        "warnings": warnings,
    }


def print_report(audit_result: dict, verbose: bool = False, use_color: bool = True):
    """Print human-readable formatted report."""
    summary = audit_result["summary"]
    errors = audit_result["errors"]
    warnings = audit_result["warnings"]

    c_green = GREEN if use_color else ""
    c_red = RED if use_color else ""
    c_yellow = YELLOW if use_color else ""
    c_bold = BOLD if use_color else ""
    c_reset = RESET if use_color else ""

    sys.stdout.write(f"\n{c_bold}=== Git Diff Audit Report ==={c_reset}\n")
    sys.stdout.write(
        f"Files Modified: {summary['files_changed']} (+{summary['total_added']} / -{summary['total_deleted']} lines)\n"
    )
    sys.stdout.write(f"Errors: {len(errors)} | Warnings: {len(warnings)}\n\n")

    if errors:
        sys.stdout.write(f"{c_red}{c_bold}❌ ERRORS (Must Fix):{c_reset}\n")
        for err in errors:
            sys.stdout.write(f"  {c_red}• [{err['type']}] {err['message']}{c_reset}\n")
        sys.stdout.write("\n")

    if warnings:
        sys.stdout.write(
            f"{c_yellow}{c_bold}⚠️  WARNINGS (Review Carefully):{c_reset}\n"
        )
        for w in warnings:
            sys.stdout.write(f"  {c_yellow}• [{w['type']}] {w['message']}{c_reset}\n")
        sys.stdout.write("\n")

    if summary["passed"]:
        if len(warnings) == 0:
            sys.stdout.write(
                f"{c_green}{c_bold}✅ Diff Audit PASSED: Clean changes with no boundary violations or stray artifacts.{c_reset}\n\n"
            )
        else:
            sys.stdout.write(
                f"{c_green}{c_bold}✅ Diff Audit PASSED with {len(warnings)} warning(s). Check warnings before finalizing PR.{c_reset}\n\n"
            )
    else:
        sys.stdout.write(
            f"{c_red}{c_bold}❌ Diff Audit FAILED: Please fix identified error(s) before committing or creating a PR.{c_reset}\n\n"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Audit git diff for boundary violations, stray debug calls, and accidental deletions."
    )
    parser.add_argument(
        "--staged",
        "--cached",
        action="store_true",
        help="Audit staged changes (git diff --cached)",
    )
    parser.add_argument(
        "--base",
        type=str,
        default=None,
        help="Compare working tree/branch against base ref (e.g. main, origin/main, HEAD~1)",
    )
    parser.add_argument(
        "--range",
        type=str,
        default=None,
        help="Compare specific commit range (e.g. main..HEAD or HEAD~2..HEAD)",
    )
    parser.add_argument(
        "--max-churn",
        type=int,
        default=500,
        help="Maximum allowed lines changed in a single file before warning (default: 500)",
    )
    parser.add_argument(
        "--allowed-scope",
        action="append",
        dest="allowed_scope",
        help="Regex pattern(s) or paths for allowed files (e.g. 'src/' 'tests/'). Can be specified multiple times.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail (exit code 1) on warnings in addition to errors",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored ANSI terminal output",
    )
    parser.add_argument(
        "--ignore-debug",
        action="store_true",
        help="Skip stray debug statement check",
    )
    parser.add_argument(
        "--ignore-docstrings",
        action="store_true",
        help="Skip docstring/comment deletion check",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional pathspec filters to limit diff inspection",
    )

    args = parser.parse_args()

    # Validate mutually exclusive target options
    target_options = [args.staged, args.base is not None, args.range is not None]
    if sum(target_options) > 1:
        conflicting = []
        if args.staged:
            conflicting.append("--staged/--cached")
        if args.base is not None:
            conflicting.append("--base")
        if args.range is not None:
            conflicting.append("--range")
        error_msg = (
            f"Conflicting target options: {', '.join(conflicting)}. Use only one."
        )
        if args.json:
            sys.stdout.write(json.dumps({"error": error_msg, "passed": False}) + "\n")
        else:
            sys.stderr.write(f"{RED}Error: {error_msg}{RESET}\n")
        sys.exit(1)

    try:
        raw_diff = get_git_diff(
            staged=args.staged,
            base=args.base,
            commit_range=args.range,
            paths=args.paths if args.paths else None,
        )
        numstat = get_git_numstat(
            staged=args.staged,
            base=args.base,
            commit_range=args.range,
            paths=args.paths if args.paths else None,
        )
    except (OSError, subprocess.SubprocessError, RuntimeError) as e:
        if args.json:
            sys.stdout.write(json.dumps({"error": str(e), "passed": False}) + "\n")
        else:
            sys.stderr.write(f"{RED}Error fetching git diff: {e}{RESET}\n")
        sys.exit(1)

    # Compile allowed scope patterns with error handling
    allowed_patterns = None
    if args.allowed_scope:
        try:
            allowed_patterns = [re.compile(p) for p in args.allowed_scope]
        except re.error as e:
            error_msg = f"Invalid regex pattern in --allowed-scope: {e}"
            if args.json:
                sys.stdout.write(
                    json.dumps({"error": error_msg, "passed": False}) + "\n"
                )
            else:
                sys.stderr.write(f"{RED}Error: {error_msg}{RESET}\n")
            sys.exit(1)

    result = audit_diff(
        diff_text=raw_diff,
        numstat=numstat,
        allowed_patterns=allowed_patterns,
        max_churn_lines=args.max_churn,
        check_docstrings=not args.ignore_docstrings,
        check_debug=not args.ignore_debug,
        check_churn=True,
        check_sensitive=True,
    )

    if args.json:
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
    else:
        use_color = not args.no_color and sys.stdout.isatty()
        print_report(result, use_color=use_color)

    # Determine exit code
    if not result["summary"]["passed"]:
        sys.exit(1)
    if args.strict and result["summary"]["warning_count"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
