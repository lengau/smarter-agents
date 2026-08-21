#!/usr/bin/env python3
"""
verify.py - Automated Polyglot Test & Lint Diagnostic Runner

Automatically discovers and executes test and lint suites across ecosystems
(Python, Node/TypeScript, Rust, Go, Java/Kotlin, C/C++), captures output,
filters verbose passing noise, and formats structured, low-token failure summaries
with targeted re-run commands.
"""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple


class TestResult:
    def __init__(
        self,
        name: str,
        category: str,
        command: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        summary: Optional[str] = None,
        failures: Optional[List[Dict[str, str]]] = None,
        rerun_cmd: Optional[str] = None,
    ):
        self.name = name
        self.category = category  # "test" or "lint"
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.summary = summary or ""
        self.failures = failures or []
        self.rerun_cmd = rerun_cmd or ""

    @property
    def passed(self) -> bool:
        return self.exit_code == 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "command": self.command,
            "exit_code": self.exit_code,
            "passed": self.passed,
            "summary": self.summary,
            "failures": self.failures,
            "rerun_cmd": self.rerun_cmd,
        }


# ---------------------------------------------------------------------------
# Output Parsers & Noise Filters
# ---------------------------------------------------------------------------

def parse_pytest_output(stdout: str, stderr: str) -> Tuple[str, List[Dict[str, str]], str]:
    """Extract failed tests, error messages, and rerun command from pytest output."""
    failures = []
    combined = stdout + "\n" + stderr
    
    # Extract FAILURES / ERRORS blocks
    fail_sections = re.findall(r"_{3,}\s+([^\n]+)\s+_{3,}\n(.*?)(?=\n_{3,}|\n={3,}|\Z)", combined, re.DOTALL)
    for title, body in fail_sections:
        clean_title = title.strip()
        lines = [line.strip() for line in body.strip().splitlines() if line.strip()]
        last_error = lines[-1] if lines else "Test failed"
        # Find file/line location if available
        location_match = re.search(r"([\w/\\.-]+\.py):(\d+):", body)
        loc = f"{location_match.group(1)}:{location_match.group(2)}" if location_match else clean_title
        failures.append({
            "test": clean_title,
            "location": loc,
            "message": last_error,
            "snippet": "\n".join(lines[-5:]) if len(lines) > 5 else "\n".join(lines),
        })

    # Summary line
    summary_match = re.search(r"=+\s+([0-9]+ (?:failed|passed|error)[^=\n]*)=+", combined)
    summary = summary_match.group(1) if summary_match else "Pytest execution finished"

    # Targeted rerun command suggestion
    rerun_cmd = ""
    if failures:
        first_fail = failures[0]["test"].split()[0]
        rerun_cmd = f"pytest -k '{first_fail}'"

    return summary, failures, rerun_cmd


def parse_jest_output(stdout: str, stderr: str) -> Tuple[str, List[Dict[str, str]], str]:
    """Extract failed tests and rerun command from Jest / Vitest output."""
    failures = []
    combined = stdout + "\n" + stderr

    # Look for FAIL test patterns
    fail_matches = re.findall(r"●\s+([^\n]+)\n\n(.*?)(?=\n\s*●|\n\s*Tests:|\Z)", combined, re.DOTALL)
    for title, body in fail_matches:
        clean_title = title.strip()
        lines = [line.strip() for line in body.strip().splitlines() if line.strip()]
        last_error = lines[0] if lines else "Test failed"
        failures.append({
            "test": clean_title,
            "location": clean_title,
            "message": last_error,
            "snippet": "\n".join(lines[:6]),
        })

    # Summary line: Tests: X failed, Y passed, Z total
    summary_match = re.search(r"Tests:\s+([^\n]+)", combined)
    summary = summary_match.group(0) if summary_match else "Jest/Vitest execution finished"

    rerun_cmd = ""
    if failures:
        first_test = failures[0]["test"].replace("›", "").strip()
        rerun_cmd = f"npm test -- -t '{first_test}'"

    return summary, failures, rerun_cmd


def parse_cargo_output(stdout: str, stderr: str) -> Tuple[str, List[Dict[str, str]], str]:
    """Extract failed tests from cargo test output."""
    failures = []
    combined = stdout + "\n" + stderr

    # Look for "failures:" list
    fail_block = re.search(r"failures:\n((?:\s+[\w:]+\n)+)", combined)
    if fail_block:
        for line in fail_block.group(1).strip().splitlines():
            test_name = line.strip()
            if test_name:
                failures.append({
                    "test": test_name,
                    "location": test_name,
                    "message": "Cargo test assertion failed",
                    "snippet": f"Test {test_name} failed",
                })

    summary_match = re.search(r"test result: (FAILED|ok)\. ([^\n]+)", combined)
    summary = summary_match.group(0) if summary_match else "Cargo execution finished"

    rerun_cmd = ""
    if failures:
        rerun_cmd = f"cargo test {failures[0]['test']}"

    return summary, failures, rerun_cmd


def parse_go_output(stdout: str, stderr: str) -> Tuple[str, List[Dict[str, str]], str]:
    """Extract failed tests from go test output."""
    failures = []
    combined = stdout + "\n" + stderr

    # --- FAIL: TestName (0.00s)
    fail_matches = re.findall(r"--- FAIL:\s+([^\s]+)\s+\(([^)]+)\)\n(.*?)(?=\n---|\nFAIL|\Z)", combined, re.DOTALL)
    for test_name, duration, body in fail_matches:
        lines = [line.strip() for line in body.strip().splitlines() if line.strip()]
        msg = lines[0] if lines else f"Failed in {duration}"
        failures.append({
            "test": test_name,
            "location": test_name,
            "message": msg,
            "snippet": "\n".join(lines[:5]),
        })

    summary_match = re.search(r"(FAIL|PASS)\s+([^\n]+)", combined)
    summary = summary_match.group(0) if summary_match else "Go test finished"

    rerun_cmd = ""
    if failures:
        rerun_cmd = f"go test -run ^{failures[0]['test']}$ ./..."

    return summary, failures, rerun_cmd


def parse_generic_output(stdout: str, stderr: str) -> Tuple[str, List[Dict[str, str]], str]:
    """Fallback parser extracting error/fail lines from command output."""
    failures = []
    combined = stdout + "\n" + stderr
    lines = combined.splitlines()

    error_lines = []
    for line in lines:
        if re.search(r"\b(error|fail|exception|fatal|traceback|syntaxerror)\b", line, re.IGNORECASE):
            error_lines.append(line.strip())

    if error_lines:
        failures.append({
            "test": "Command execution error",
            "location": "stderr/stdout",
            "message": error_lines[0],
            "snippet": "\n".join(error_lines[:5]),
        })

    # Summary: last non-empty line or first error
    non_empty = [l.strip() for l in lines if l.strip()]
    summary = non_empty[-1] if non_empty else "Command finished"
    return summary, failures, ""


def analyze_test_output(name: str, runner: str, stdout: str, stderr: str, exit_code: int) -> Tuple[str, List[Dict[str, str]], str]:
    """Route output to specific ecosystem parser or generic fallback."""
    if exit_code == 0:
        return "All tests/checks passed cleanly.", [], ""

    r = runner.lower()
    if "pytest" in r or "unittest" in r:
        return parse_pytest_output(stdout, stderr)
    elif "jest" in r or "vitest" in r or "npm test" in r or "yarn test" in r or "pnpm test" in r or "bun test" in r:
        return parse_jest_output(stdout, stderr)
    elif "cargo" in r:
        return parse_cargo_output(stdout, stderr)
    elif "go test" in r:
        return parse_go_output(stdout, stderr)
    else:
        return parse_generic_output(stdout, stderr)


# ---------------------------------------------------------------------------
# Project Discovery
# ---------------------------------------------------------------------------

class SuiteDiscovery:
    """Discovers project ecosystems and configured test/lint commands."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def discover(self) -> List[Tuple[str, str, str]]:
        """
        Returns list of tuples: (name, category, command)
        category is 'test' or 'lint'
        """
        suites: List[Tuple[str, str, str]] = []

        # 1. Python ecosystem
        has_py_indicators = (
            (self.root / "pyproject.toml").exists()
            or (self.root / "setup.py").exists()
            or (self.root / "setup.cfg").exists()
            or (self.root / "requirements.txt").exists()
            or (self.root / "pytest.ini").exists()
            or (self.root / "Pipfile").exists()
            or (self.root / "tox.ini").exists()
            or any(self.root.glob("test_*.py"))
            or (self.root / "tests").is_dir()
        )
        if has_py_indicators:
            if shutil.which("pytest") or (self.root / "pytest.ini").exists() or (self.root / "pyproject.toml").exists():
                suites.append(("pytest", "test", "pytest -q"))
            elif shutil.which("python3"):
                suites.append(("unittest", "test", "python3 -m unittest discover -s tests -q"))

            if shutil.which("ruff"):
                suites.append(("ruff", "lint", "ruff check ."))
            elif shutil.which("flake8"):
                suites.append(("flake8", "lint", "flake8 ."))

        # 2. Node / JS / TS ecosystem
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            pkg_mgr = "npm"
            if (self.root / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
                pkg_mgr = "pnpm"
            elif (self.root / "yarn.lock").exists() and shutil.which("yarn"):
                pkg_mgr = "yarn"
            elif (self.root / "bun.lockb").exists() and shutil.which("bun"):
                pkg_mgr = "bun"

            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                scripts = data.get("scripts", {})
                if "test" in scripts:
                    suites.append((f"{pkg_mgr}-test", "test", f"{pkg_mgr} test"))
                if "lint" in scripts:
                    suites.append((f"{pkg_mgr}-lint", "lint", f"{pkg_mgr} run lint"))
                elif "check" in scripts:
                    suites.append((f"{pkg_mgr}-check", "lint", f"{pkg_mgr} run check"))
            except Exception:
                if shutil.which(pkg_mgr):
                    suites.append((f"{pkg_mgr}-test", "test", f"{pkg_mgr} test"))

        # 3. Rust ecosystem
        if (self.root / "Cargo.toml").exists() and shutil.which("cargo"):
            suites.append(("cargo-test", "test", "cargo test"))
            suites.append(("cargo-clippy", "lint", "cargo clippy -- -D warnings"))

        # 4. Go ecosystem
        if (self.root / "go.mod").exists() or any(self.root.glob("*_test.go")):
            if shutil.which("go"):
                suites.append(("go-test", "test", "go test ./..."))
            if shutil.which("golangci-lint"):
                suites.append(("golangci-lint", "lint", "golangci-lint run"))

        # 5. Java / Kotlin (Maven / Gradle)
        if (self.root / "pom.xml").exists() and shutil.which("mvn"):
            suites.append(("maven-test", "test", "mvn test -q"))
        elif (self.root / "build.gradle").exists() or (self.root / "build.gradle.kts").exists():
            gradle_cmd = "./gradlew" if (self.root / "gradlew").exists() else "gradle"
            if (self.root / "gradlew").exists() or shutil.which("gradle"):
                suites.append(("gradle-test", "test", f"{gradle_cmd} test -q"))

        # 6. C/C++ CMake / Makefile
        if (self.root / "CMakeLists.txt").exists() and shutil.which("ctest"):
            suites.append(("ctest", "test", "ctest --output-on-failure"))
        elif (self.root / "Makefile").exists() and shutil.which("make"):
            try:
                res = subprocess.run(["make", "-n", "test"], cwd=str(self.root), capture_output=True, text=True)
                if res.returncode == 0:
                    suites.append(("make-test", "test", "make test"))
            except Exception:
                pass

        return suites


# ---------------------------------------------------------------------------
# Runner & Formatter
# ---------------------------------------------------------------------------

def run_command(command: str, cwd: Path) -> Tuple[int, str, str]:
    """Execute command in directory, capturing stdout, stderr, and exit code."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "Error: Command timed out after 300 seconds."
    except Exception as e:
        return 1, "", f"Error executing command '{command}': {e}"


def format_markdown_report(results: List[TestResult]) -> str:
    """Format compact markdown summary with low token footprint."""
    lines = []
    total = len(results)
    passed_count = sum(1 for r in results if r.passed)
    failed_count = total - passed_count

    lines.append("## 🧪 Verification & Lint Diagnostic Summary\n")
    if failed_count == 0:
        lines.append(f"✅ **All {total} checks passed successfully.**\n")
        for r in results:
            lines.append(f"- **{r.name}** (`{r.command}`): PASSED (exit code 0)")
        return "\n".join(lines)

    lines.append(f"❌ **{failed_count} of {total} checks failed.**\n")

    for r in results:
        status_icon = "✅" if r.passed else "❌"
        lines.append(f"### {status_icon} `{r.name}` ({r.category.upper()})")
        lines.append(f"- **Command**: `{r.command}`")
        lines.append(f"- **Status**: {'PASSED' if r.passed else f'FAILED (Exit code {r.exit_code})'}")
        if r.summary:
            lines.append(f"- **Summary**: {r.summary}")
        if r.rerun_cmd:
            lines.append(f"- **Targeted Re-run**: `{r.rerun_cmd}`")

        if not r.passed:
            if r.failures:
                lines.append("\n**Failures / Diagnostics:**")
                for f in r.failures:
                    loc = f.get("location", "")
                    lines.append(f"\n> **{f.get('test', 'Failure')}** ({loc})")
                    lines.append(f"> ```text")
                    for s_line in f.get("snippet", f.get("message", "")).splitlines():
                        lines.append(f"> {s_line}")
                    lines.append(f"> ```")
            else:
                err_text = (r.stderr or r.stdout).strip()
                err_lines = err_text.splitlines()
                snippet = "\n".join(err_lines[-12:]) if len(err_lines) > 12 else err_text
                if snippet:
                    lines.append("\n**Diagnostic Output:**")
                    lines.append("```text")
                    lines.append(snippet)
                    lines.append("```")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Automated polyglot test & lint diagnostic runner."
    )
    parser.add_argument(
        "--path",
        "-p",
        type=str,
        default=".",
        help="Root directory of the project to verify (default: current dir).",
    )
    parser.add_argument(
        "--test-only",
        "--test",
        action="store_true",
        help="Run only test suites, skipping lint checks.",
    )
    parser.add_argument(
        "--lint-only",
        "--lint",
        action="store_true",
        help="Run only lint checks, skipping test suites.",
    )
    parser.add_argument(
        "--cmd",
        "-c",
        type=str,
        action="append",
        help="Execute custom test/lint command (can be specified multiple times).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON instead of human/markdown summary.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Preserve verbose output instead of filtering noise.",
    )

    args = parser.parse_args()
    root_path = Path(args.path).resolve()

    if not root_path.exists():
        print(f"Error: Path '{root_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    commands_to_run: List[Tuple[str, str, str]] = []

    if args.cmd:
        for idx, custom_cmd in enumerate(args.cmd, 1):
            commands_to_run.append((f"custom-cmd-{idx}", "custom", custom_cmd))
    else:
        discovery = SuiteDiscovery(root_path)
        discovered = discovery.discover()

        for name, category, cmd in discovered:
            if args.test_only and category != "test":
                continue
            if args.lint_only and category != "lint":
                continue
            commands_to_run.append((name, category, cmd))

    if not commands_to_run:
        if not args.json:
            print(f"⚠️ No test or lint suites discovered in '{root_path}'.")
            print("Specify commands explicitly using `--cmd '<command>'`.")
        else:
            print(json.dumps({"status": "no_suites_found", "results": []}))
        sys.exit(0)

    results: List[TestResult] = []
    overall_exit = 0

    for name, category, cmd in commands_to_run:
        exit_code, stdout, stderr = run_command(cmd, root_path)
        if exit_code != 0:
            overall_exit = exit_code

        summary, failures, rerun_cmd = analyze_test_output(name, cmd, stdout, stderr, exit_code)

        result = TestResult(
            name=name,
            category=category,
            command=cmd,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            summary=summary,
            failures=failures,
            rerun_cmd=rerun_cmd,
        )
        results.append(result)

    if args.json:
        payload = {
            "passed": overall_exit == 0,
            "exit_code": overall_exit,
            "total": len(results),
            "passed_count": sum(1 for r in results if r.passed),
            "failed_count": sum(1 for r in results if not r.passed),
            "results": [r.to_dict() for r in results],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_markdown_report(results))

    sys.exit(overall_exit)


if __name__ == "__main__":
    main()
