#!/usr/bin/env python3
"""
verify.py - Automated Polyglot Test & Lint Diagnostic Runner

Automatically discovers workspace test & lint runners, executes tests with targeted
filters, captures exit codes, suppresses verbose passing noise, and outputs concise,
low-token failure summaries and stack traces.

Supported Ecosystems:
- Python: pytest, unittest, poetry, uv, ruff, flake8, mypy
- JavaScript/TypeScript: vitest, jest, npm/pnpm/yarn/bun test, eslint, biome, tsc
- Rust: cargo test, cargo clippy, cargo check
- Go: go test, golangci-lint
- C/C++: ctest, make test, make check
- Java/Kotlin: ./gradlew test, gradle test, mvn test
- Ruby: rspec, bundle exec rspec, rake test
- PHP: phpunit, composer test
- Elixir: mix test
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class FailureDetail:
    name: str
    message: str
    location: Optional[str] = None
    stack_trace: List[str] = field(default_factory=list)


@dataclass
class RunnerResult:
    tool: str
    category: str  # "test" or "lint"
    command: List[str]
    exit_code: int
    passed: bool
    summary: str
    failures: List[FailureDetail] = field(default_factory=list)
    raw_output: str = ""
    duration_sec: float = 0.0


def is_tool_available(tool_name: str) -> bool:
    """Check if a CLI tool or executable is available in PATH."""
    return shutil.which(tool_name) is not None


class PolyglotDetector:
    """Detects available test and lint frameworks in a directory."""

    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()

    def has_file(self, *patterns: str) -> bool:
        """Check if any matching file exists in workspace."""
        for pattern in patterns:
            if "/" in pattern:
                if (self.workspace / pattern).exists():
                    return True
            else:
                if list(self.workspace.glob(pattern)):
                    return True
        return False

    def detect_runners(self, runner_type: str = "all") -> List[Tuple[str, str, List[str]]]:
        """
        Detect test and lint runners.
        Returns list of tuples: (category, tool_name, default_command)
        """
        runners: List[Tuple[str, str, List[str]]] = []

        # --- Python ---
        has_py_files = self.has_file("*.py", "tests/*.py", "test/*.py")
        has_pyproject = self.has_file("pyproject.toml")
        has_setup_py = self.has_file("setup.py", "setup.cfg")
        has_requirements = self.has_file("requirements.txt", "requirements-dev.txt", "Pipfile")

        if has_py_files or has_pyproject or has_setup_py or has_requirements:
            if runner_type in ("all", "test"):
                # Check for pytest first
                if is_tool_available("pytest") or self.has_file("conftest.py", "pytest.ini"):
                    if is_tool_available("uv"):
                        runners.append(("test", "pytest", ["uv", "run", "pytest", "-q", "--tb=short"]))
                    elif is_tool_available("poetry") and self.has_file("poetry.lock"):
                        runners.append(("test", "pytest", ["poetry", "run", "pytest", "-q", "--tb=short"]))
                    elif is_tool_available("pytest"):
                        runners.append(("test", "pytest", ["pytest", "-q", "--tb=short"]))
                    else:
                        runners.append(("test", "pytest", [sys.executable, "-m", "pytest", "-q", "--tb=short"]))
                elif self.has_file("tests", "test"):
                    runners.append(("test", "unittest", [sys.executable, "-m", "unittest", "discover", "-s", "tests"]))

            if runner_type in ("all", "lint"):
                if is_tool_available("ruff") or self.has_file("ruff.toml"):
                    runners.append(("lint", "ruff", ["ruff", "check", "."]))
                elif is_tool_available("flake8") or self.has_file(".flake8"):
                    runners.append(("lint", "flake8", ["flake8"]))

                if is_tool_available("mypy") or self.has_file("mypy.ini"):
                    runners.append(("lint", "mypy", ["mypy", "."]))

        # --- JavaScript / TypeScript ---
        has_package_json = self.has_file("package.json")
        if has_package_json:
            pkg_json_path = self.workspace / "package.json"
            pkg_data = {}
            try:
                with open(pkg_json_path, "r", encoding="utf-8") as f:
                    pkg_data = json.load(f)
            except Exception:
                pass

            scripts = pkg_data.get("scripts", {})
            pkg_manager = "npm"
            if self.has_file("pnpm-lock.yaml") and is_tool_available("pnpm"):
                pkg_manager = "pnpm"
            elif self.has_file("yarn.lock") and is_tool_available("yarn"):
                pkg_manager = "yarn"
            elif self.has_file("bun.lockb", "bun.lock") and is_tool_available("bun"):
                pkg_manager = "bun"

            if runner_type in ("all", "test"):
                if "test" in scripts:
                    runners.append(("test", f"{pkg_manager}-test", [pkg_manager, "test", "--", "--silent"] if pkg_manager in ("npm", "pnpm") else [pkg_manager, "test"]))
                elif self.has_file("vitest.config.*", "vite.config.*") or "vitest" in pkg_data.get("devDependencies", {}):
                    runners.append(("test", "vitest", ["npx", "vitest", "run", "--reporter=verbose"]))
                elif self.has_file("jest.config.*") or "jest" in pkg_data.get("devDependencies", {}):
                    runners.append(("test", "jest", ["npx", "jest", "--silent", "--no-coverage"]))

            if runner_type in ("all", "lint"):
                if "lint" in scripts:
                    runners.append(("lint", f"{pkg_manager}-lint", [pkg_manager, "run", "lint"]))
                elif self.has_file(".eslintrc*", "eslint.config.*") or "eslint" in pkg_data.get("devDependencies", {}):
                    runners.append(("lint", "eslint", ["npx", "eslint", "."]))
                elif self.has_file("biome.json") or "biome" in pkg_data.get("devDependencies", {}):
                    runners.append(("lint", "biome", ["npx", "@biomejs/biome", "lint", "."]))

                if self.has_file("tsconfig.json") and is_tool_available("npx"):
                    runners.append(("lint", "tsc", ["npx", "tsc", "--noEmit"]))

        # --- Rust ---
        has_cargo = self.has_file("Cargo.toml")
        if has_cargo and is_tool_available("cargo"):
            if runner_type in ("all", "test"):
                runners.append(("test", "cargo-test", ["cargo", "test", "--quiet", "--", "--nocapture"]))
            if runner_type in ("all", "lint"):
                runners.append(("lint", "cargo-clippy", ["cargo", "clippy", "--quiet", "--", "-D", "warnings"]))

        # --- Go ---
        has_go = self.has_file("go.mod", "*.go")
        if has_go and is_tool_available("go"):
            if runner_type in ("all", "test"):
                runners.append(("test", "go-test", ["go", "test", "./..."]))
            if runner_type in ("all", "lint") and is_tool_available("golangci-lint"):
                runners.append(("lint", "golangci-lint", ["golangci-lint", "run"]))

        # --- C / C++ ---
        if self.has_file("CMakeLists.txt") and is_tool_available("ctest") and runner_type in ("all", "test"):
            if (self.workspace / "build").exists():
                runners.append(("test", "ctest", ["ctest", "--test-dir", "build", "--output-on-failure"]))
        elif self.has_file("Makefile") and runner_type in ("all", "test"):
            runners.append(("test", "make-test", ["make", "test"]))

        # --- Java / Kotlin ---
        if self.has_file("gradlew") and runner_type in ("all", "test"):
            runners.append(("test", "gradle", ["./gradlew", "test", "-q"]))
        elif self.has_file("pom.xml") and is_tool_available("mvn") and runner_type in ("all", "test"):
            runners.append(("test", "maven", ["mvn", "test", "-q"]))

        # --- Ruby ---
        if self.has_file("Gemfile") and runner_type in ("all", "test"):
            if self.has_file(".rspec", "spec") and is_tool_available("bundle"):
                runners.append(("test", "rspec", ["bundle", "exec", "rspec", "--format", "progress"]))

        return runners


class OutputParser:
    """Parses raw test and lint outputs to extract low-token failure summaries."""

    @staticmethod
    def parse(tool: str, raw_output: str, exit_code: int) -> Tuple[str, List[FailureDetail]]:
        if exit_code == 0:
            return OutputParser._parse_success(tool, raw_output)

        parser_map = {
            "pytest": OutputParser._parse_pytest,
            "unittest": OutputParser._parse_unittest,
            "ruff": OutputParser._parse_ruff,
            "flake8": OutputParser._parse_flake8,
            "mypy": OutputParser._parse_mypy,
            "cargo-test": OutputParser._parse_cargo_test,
            "cargo-clippy": OutputParser._parse_cargo_clippy,
            "go-test": OutputParser._parse_go_test,
            "golangci-lint": OutputParser._parse_golangci_lint,
            "jest": OutputParser._parse_jest,
            "vitest": OutputParser._parse_vitest,
            "npm-test": OutputParser._parse_generic_js,
            "pnpm-test": OutputParser._parse_generic_js,
            "yarn-test": OutputParser._parse_generic_js,
            "bun-test": OutputParser._parse_generic_js,
            "eslint": OutputParser._parse_eslint,
            "tsc": OutputParser._parse_tsc,
        }

        handler = parser_map.get(tool, OutputParser._parse_generic)
        return handler(raw_output)

    @staticmethod
    def _parse_success(tool: str, output: str) -> Tuple[str, List[FailureDetail]]:
        lines = [l.strip() for l in output.strip().splitlines() if l.strip()]
        last_line = lines[-1] if lines else "Passed"
        return f"✓ {tool}: {last_line}", []

    @staticmethod
    def _parse_pytest(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        summary = "Pytest execution failed"

        # Look for summary line e.g. "=== 1 failed, 12 passed in 0.23s ==="
        for line in output.splitlines():
            if re.search(r"=+\s+(\d+\s+failed|\d+\s+error).+=+", line):
                summary = line.strip(" =")
                break

        # Extract FAILURES / ERRORS blocks
        lines = output.splitlines()
        current_failure: Optional[FailureDetail] = None
        in_failure_block = False

        for line in lines:
            if line.startswith("_") and line.endswith("_") and len(line) > 5:
                # Test header: __________________ test_name ___________________
                if current_failure:
                    failures.append(current_failure)
                test_name = line.strip(" _")
                current_failure = FailureDetail(name=test_name, message="", stack_trace=[])
                in_failure_block = True
                continue

            if in_failure_block and current_failure:
                if line.startswith("="):
                    # End of failure sections
                    failures.append(current_failure)
                    current_failure = None
                    in_failure_block = False
                    continue

                if line.startswith("E   ") or line.startswith("E "):
                    err_msg = line[2:].strip()
                    if not current_failure.message:
                        current_failure.message = err_msg
                    else:
                        current_failure.message += f"\n{err_msg}"
                elif ":" in line and not line.startswith(" ") and ("test_" in line or ".py:" in line):
                    current_failure.location = line.strip()
                
                # Keep concise stack trace lines (limit to relevant lines)
                if len(current_failure.stack_trace) < 8 and (">" in line or "E " in line or ".py:" in line):
                    current_failure.stack_trace.append(line.strip())

        if current_failure:
            failures.append(current_failure)

        if not failures:
            # Fallback extraction for short summary
            for line in lines:
                if "FAILED " in line or "ERROR " in line:
                    parts = line.split(" - ")
                    failures.append(FailureDetail(
                        name=line.split()[1] if len(line.split()) > 1 else line,
                        message=parts[1] if len(parts) > 1 else line,
                        location=line.split()[1] if len(line.split()) > 1 else None
                    ))

        return summary, failures

    @staticmethod
    def _parse_unittest(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        summary = "Unittest execution failed"
        lines = output.splitlines()

        for line in lines:
            if line.startswith("FAILED ("):
                summary = line.strip()
                break

        current_failure = None
        for line in lines:
            if line.startswith("FAIL: ") or line.startswith("ERROR: "):
                if current_failure:
                    failures.append(current_failure)
                parts = line.split(" ", 1)
                name = parts[1] if len(parts) > 1 else line
                current_failure = FailureDetail(name=name, message="")
            elif current_failure:
                if line.startswith("AssertionError:") or "Error:" in line:
                    current_failure.message = line.strip()
                elif line.startswith("  File "):
                    current_failure.location = line.strip()
                elif len(current_failure.stack_trace) < 6:
                    current_failure.stack_trace.append(line.strip())

        if current_failure:
            failures.append(current_failure)

        return summary, failures

    @staticmethod
    def _parse_ruff(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        for line in lines:
            match = re.match(r"^([^:]+:\d+:\d+):\s+([A-Z0-9]+)\s+(.*)$", line)
            if match:
                loc, code, msg = match.groups()
                failures.append(FailureDetail(name=f"[{code}] {loc}", message=msg, location=loc))
        summary = f"Ruff found {len(failures)} issue(s)" if failures else "Ruff lint errors found"
        return summary, failures

    @staticmethod
    def _parse_flake8(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        for line in lines:
            match = re.match(r"^([^:]+:\d+:\d+):\s+([A-Z0-9]+)\s+(.*)$", line)
            if match:
                loc, code, msg = match.groups()
                failures.append(FailureDetail(name=f"[{code}] {loc}", message=msg, location=loc))
        summary = f"Flake8 found {len(failures)} issue(s)" if failures else "Flake8 lint errors found"
        return summary, failures

    @staticmethod
    def _parse_mypy(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        summary = "Mypy type check failed"
        for line in lines:
            if "Found " in line and " error" in line:
                summary = line
            elif ": error:" in line:
                parts = line.split(": error:", 1)
                loc = parts[0].strip()
                msg = parts[1].strip() if len(parts) > 1 else ""
                failures.append(FailureDetail(name=loc, message=msg, location=loc))
        return summary, failures

    @staticmethod
    def _parse_cargo_test(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        summary = "Cargo test failed"
        lines = output.splitlines()

        for line in lines:
            if "test result: FAILED." in line:
                summary = line.strip()

        in_failures = False
        for line in lines:
            if line.strip() == "failures:":
                in_failures = True
                continue
            if in_failures:
                if not line.strip() or line.startswith("test result:"):
                    in_failures = False
                    continue
                test_name = line.strip()
                if test_name and not test_name.startswith("----"):
                    failures.append(FailureDetail(name=test_name, message="Test failed assertion", location=test_name))

        return summary, failures

    @staticmethod
    def _parse_cargo_clippy(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        lines = output.splitlines()
        summary = "Cargo clippy checks failed"
        for i, line in enumerate(lines):
            if line.startswith("error:"):
                msg = line[6:].strip()
                loc = None
                if i + 1 < len(lines) and "-->" in lines[i + 1]:
                    loc = lines[i + 1].strip().replace("-->", "").strip()
                failures.append(FailureDetail(name=loc or "Clippy error", message=msg, location=loc))
        return summary, failures

    @staticmethod
    def _parse_go_test(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        summary = "Go tests failed"
        lines = output.splitlines()

        for line in lines:
            if line.startswith("--- FAIL:"):
                test_name = line.replace("--- FAIL:", "").strip().split()[0]
                failures.append(FailureDetail(name=test_name, message="Test failed", location=test_name))
            elif line.startswith("FAIL\t") or line.startswith("FAIL"):
                summary = line.strip()

        return summary, failures

    @staticmethod
    def _parse_golangci_lint(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        for line in lines:
            parts = line.split(":", 3)
            if len(parts) >= 4:
                loc = f"{parts[0]}:{parts[1]}:{parts[2]}"
                msg = parts[3].strip()
                failures.append(FailureDetail(name=loc, message=msg, location=loc))
        summary = f"golangci-lint found {len(failures)} issue(s)"
        return summary, failures

    @staticmethod
    def _parse_jest(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        summary = "Jest tests failed"
        lines = output.splitlines()

        for line in lines:
            if "Tests:" in line and "failed" in line:
                summary = line.strip()
            elif "● " in line:
                test_name = line.replace("●", "").strip()
                failures.append(FailureDetail(name=test_name, message="Test assertion failed"))

        return summary, failures

    @staticmethod
    def _parse_vitest(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        summary = "Vitest tests failed"
        lines = output.splitlines()

        for line in lines:
            if "Tests " in line and "failed" in line:
                summary = line.strip()
            elif "FAIL " in line:
                test_name = line.replace("FAIL", "").strip()
                failures.append(FailureDetail(name=test_name, message="Test failed", location=test_name))

        return summary, failures

    @staticmethod
    def _parse_generic_js(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        lines = output.splitlines()
        for line in lines:
            if "✕ " in line or "FAIL " in line or "error " in line.lower():
                failures.append(FailureDetail(name=line.strip(), message="Test/lint error"))
        summary = f"Execution failed with {len(failures)} error(s)" if failures else "Execution failed"
        return summary, failures

    @staticmethod
    def _parse_eslint(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        for line in lines:
            if "error" in line and ":" in line:
                failures.append(FailureDetail(name=line, message="ESLint error"))
        return f"ESLint reported {len(failures)} error(s)", failures

    @staticmethod
    def _parse_tsc(output: str) -> Tuple[str, List[FailureDetail]]:
        failures = []
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        for line in lines:
            match = re.match(r"^([^:]+:\d+:\d+):\s+error\s+TS\d+:\s+(.*)$", line)
            if match:
                loc, msg = match.groups()
                failures.append(FailureDetail(name=loc, message=msg, location=loc))
        return f"TypeScript reported {len(failures)} compilation error(s)", failures

    @staticmethod
    def _parse_generic(output: str) -> Tuple[str, List[FailureDetail]]:
        lines = [l for l in output.splitlines() if l.strip()]
        failures = []
        error_lines = [l for l in lines if any(k in l.lower() for k in ("fail", "error", "exception", "assert"))]
        for l in error_lines[:10]:
            failures.append(FailureDetail(name=l.strip()[:80], message=l.strip()))
        summary = f"Command failed with {len(error_lines)} error indicator(s)"
        return summary, failures


class RunnerExecutor:
    """Executes detected commands and formats concise diagnostic output."""

    def __init__(self, workspace: Path, max_failures: int = 5, verbose: bool = False):
        self.workspace = workspace.resolve()
        self.max_failures = max_failures
        self.verbose = verbose

    def run_command(self, tool: str, category: str, cmd: List[str], target: Optional[str] = None) -> RunnerResult:
        import time

        final_cmd = list(cmd)
        if target:
            final_cmd.append(target)

        start_time = time.time()
        try:
            process = subprocess.run(
                final_cmd,
                cwd=self.workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=120,
            )
            raw_output = process.stdout or ""
            exit_code = process.returncode
        except subprocess.TimeoutExpired as e:
            raw_output = f"Command timed out after 120s: {e}"
            exit_code = 124
        except Exception as e:
            raw_output = f"Failed to execute command {' '.join(final_cmd)}: {e}"
            exit_code = 1

        duration = round(time.time() - start_time, 2)
        passed = (exit_code == 0)

        summary, failures = OutputParser.parse(tool, raw_output, exit_code)

        return RunnerResult(
            tool=tool,
            category=category,
            command=final_cmd,
            exit_code=exit_code,
            passed=passed,
            summary=summary,
            failures=failures,
            raw_output=raw_output,
            duration_sec=duration,
        )


def format_report(results: List[RunnerResult], max_failures: int = 5, json_output: bool = False) -> str:
    """Formats runner results into clean, token-efficient markdown/terminal text or JSON."""
    if json_output:
        data = [asdict(r) for r in results]
        return json.dumps(data, indent=2)

    total = len(results)
    passed_count = sum(1 for r in results if r.passed)
    failed_count = total - passed_count

    output_lines = []
    output_lines.append("## 🧪 Verification & Lint Report")
    output_lines.append("")

    if failed_count == 0:
        output_lines.append(f"**Status:** ✅ ALL CHECKS PASSED ({passed_count}/{total} suites successful)")
    else:
        output_lines.append(f"**Status:** ❌ {failed_count} OF {total} SUITE(S) FAILED")
    output_lines.append("")

    # Summary table
    output_lines.append("| Category | Tool | Command | Status | Duration |")
    output_lines.append("|---|---|---|---|---|")
    for r in results:
        status_icon = "✅ PASS" if r.passed else f"❌ FAIL ({r.exit_code})"
        cmd_str = f"`{' '.join(r.command)}`"
        output_lines.append(f"| {r.category.upper()} | **{r.tool}** | {cmd_str} | {status_icon} | {r.duration_sec}s |")

    output_lines.append("")

    # Detailed Failure Breakdowns
    if failed_count > 0:
        output_lines.append("### 🔍 Failure Diagnostic Summaries")
        output_lines.append("")

        for r in results:
            if r.passed:
                continue

            output_lines.append(f"#### ❌ {r.tool} ({r.category.upper()})")
            output_lines.append(f"**Summary:** {r.summary}")
            output_lines.append("")

            if r.failures:
                output_lines.append(f"Surfacing top {min(len(r.failures), max_failures)} failures:")
                for i, fail in enumerate(r.failures[:max_failures], 1):
                    output_lines.append(f"- **#{i} {fail.name}**")
                    if fail.location:
                        output_lines.append(f"  - Location: `{fail.location}`")
                    if fail.message:
                        output_lines.append(f"  - Message: `{fail.message.strip().splitlines()[0]}`")
                    if fail.stack_trace:
                        output_lines.append("  - Trace:")
                        output_lines.append("    ```")
                        for t in fail.stack_trace[:4]:
                            output_lines.append(f"    {t}")
                        output_lines.append("    ```")
                if len(r.failures) > max_failures:
                    output_lines.append(f"*(...and {len(r.failures) - max_failures} more failures omitted for brevity)*")
            else:
                output_lines.append("```")
                tail_lines = [l for l in r.raw_output.splitlines() if l.strip()][-15:]
                output_lines.extend(tail_lines)
                output_lines.append("```")
            output_lines.append("")

    return "\n".join(output_lines)


def main():
    parser = argparse.ArgumentParser(
        description="verify.py - Automated Polyglot Test & Lint Diagnostic Runner"
    )
    parser.add_argument(
        "--dir",
        default=".",
        help="Workspace directory to inspect and execute in (default: current directory)",
    )
    parser.add_argument(
        "--type",
        choices=["all", "test", "lint"],
        default="all",
        help="Check types to run: 'all', 'test', or 'lint' (default: all)",
    )
    parser.add_argument(
        "--runner",
        help="Override runner detection and run specific runner (e.g. pytest, ruff, cargo-test, jest)",
    )
    parser.add_argument(
        "--target",
        help="Target test file or filter pattern to pass to runner",
    )
    parser.add_argument(
        "--max-failures",
        type=int,
        default=5,
        help="Max number of failure stack traces to surface (default: 5)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Output raw runner output without suppression",
    )

    args = parser.parse_args()
    workspace = Path(args.dir).resolve()

    if not workspace.exists():
        print(f"Error: Directory {workspace} does not exist", file=sys.stderr)
        sys.exit(1)

    detector = PolyglotDetector(workspace)
    discovered = detector.detect_runners(runner_type=args.type)

    if args.runner:
        matched = [r for r in discovered if r[1] == args.runner]
        if not matched:
            discovered = [("test", args.runner, [args.runner])]
        else:
            discovered = matched

    if not discovered:
        print(f"⚠️ No test or lint runners discovered for workspace in: {workspace}")
        print("Tip: Specify runner manually with --runner <name> or ensure config files are present.")
        sys.exit(0)

    executor = RunnerExecutor(workspace, max_failures=args.max_failures, verbose=args.verbose)
    results = []

    for cat, tool_name, cmd in discovered:
        res = executor.run_command(tool_name, cat, cmd, target=args.target)
        results.append(res)

    report = format_report(results, max_failures=args.max_failures, json_output=args.json)
    print(report)

    any_failed = any(not r.passed for r in results)
    sys.exit(1 if any_failed else 0)


if __name__ == "__main__":
    main()
