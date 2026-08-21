#!/usr/bin/env python3
"""
Unit tests for the verify-and-lint skill scripts and parsers.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

# Add skills directory to path for direct imports
SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "verify-and-lint" / "scripts"
sys.path.insert(0, str(SKILL_DIR))

import verify


class TestTestResult(unittest.TestCase):
    def test_result_properties(self):
        passed_result = verify.TestResult(
            name="test-pass",
            category="test",
            command="pytest",
            exit_code=0,
            stdout="OK",
            stderr="",
        )
        self.assertTrue(passed_result.passed)
        self.assertEqual(passed_result.to_dict()["exit_code"], 0)

        failed_result = verify.TestResult(
            name="test-fail",
            category="test",
            command="pytest",
            exit_code=1,
            stdout="",
            stderr="AssertionError",
            failures=[{"test": "test_foo", "message": "Failed assertion"}],
            rerun_cmd="pytest -k test_foo",
        )
        self.assertFalse(failed_result.passed)
        d = failed_result.to_dict()
        self.assertEqual(d["exit_code"], 1)
        self.assertEqual(len(d["failures"]), 1)
        self.assertEqual(d["rerun_cmd"], "pytest -k test_foo")


class TestParsers(unittest.TestCase):
    def test_parse_pytest_failure(self):
        sample_output = """
============================= test session starts ==============================
collected 2 items

test_app.py .F                                                           [100%]

=================================== FAILURES ===================================
_________________________________ test_addition ________________________________

    def test_addition():
>       assert 1 + 1 == 3
E       assert 2 == 3

test_app.py:12: AssertionError
=========================== short test summary info ============================
FAILED test_app.py::test_addition - assert 2 == 3
========================= 1 failed, 1 passed in 0.12s ==========================
"""
        summary, failures, rerun = verify.parse_pytest_output(sample_output, "")
        self.assertIn("1 failed", summary)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["test"], "test_addition")
        self.assertIn("test_app.py:12", failures[0]["location"])
        self.assertEqual(rerun, "pytest -k 'test_addition'")

    def test_parse_jest_failure(self):
        sample_output = """
FAIL src/index.test.ts
  ● AuthModule › login › should return jwt token

    expect(received).toBe(expected) // Object.is equality

    Expected: "valid-token"
    Received: "invalid-token"

      14 |     const token = auth.login("user", "pass");
    > 15 |     expect(token).toBe("valid-token");
         |                   ^

Tests: 1 failed, 4 passed, 5 total
"""
        summary, failures, rerun = verify.parse_jest_output(sample_output, "")
        self.assertIn("1 failed, 4 passed", summary)
        self.assertEqual(len(failures), 1)
        self.assertIn("AuthModule", failures[0]["test"])
        self.assertIn("npm test -- -t", rerun)

    def test_parse_cargo_failure(self):
        sample_output = """
running 2 tests
test tests::test_pass ... ok
test tests::test_fail ... FAILED

failures:

---- tests::test_fail stdout ----
thread 'tests::test_fail' panicked at src/lib.rs:10:9:
assertion `left == right` failed
  left: 2
 right: 4

failures:
    tests::test_fail

test result: FAILED. 1 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out
"""
        summary, failures, rerun = verify.parse_cargo_output(sample_output, "")
        self.assertIn("test result: FAILED", summary)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["test"], "tests::test_fail")
        self.assertEqual(rerun, "cargo test tests::test_fail")

    def test_parse_go_failure(self):
        sample_output = """
=== RUN   TestCalculator
=== RUN   TestCalculator/Add
=== RUN   TestCalculator/Subtract
--- FAIL: TestCalculator/Subtract (0.00s)
    calc_test.go:25: expected 5, got 3
FAIL
FAIL	github.com/example/calc	0.015s
FAIL
"""
        summary, failures, rerun = verify.parse_go_output(sample_output, "")
        self.assertIn("FAIL", summary)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["test"], "TestCalculator/Subtract")
        self.assertIn("calc_test.go:25", failures[0]["message"])
        self.assertEqual(rerun, "go test -run ^TestCalculator/Subtract$ ./...")

    def test_parse_generic_failure(self):
        sample_output = """
Compiling project...
Fatal error: syntax error, unexpected token ';' on line 45
Build failed with status 1
"""
        summary, failures, rerun = verify.parse_generic_output(sample_output, "")
        self.assertIn("Build failed", summary)
        self.assertEqual(len(failures), 1)
        self.assertIn("syntax error", failures[0]["message"])


class TestSuiteDiscovery(unittest.TestCase):
    def test_python_discovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "pyproject.toml").touch()
            (tmppath / "tests").mkdir()
            discovery = verify.SuiteDiscovery(tmppath)
            suites = discovery.discover()
            suite_names = [s[0] for s in suites]
            self.assertTrue(any("pytest" in s or "unittest" in s for s in suite_names))

    def test_node_discovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            pkg = {
                "name": "test-pkg",
                "scripts": {
                    "test": "vitest run",
                    "lint": "eslint ."
                }
            }
            (tmppath / "package.json").write_text(json.dumps(pkg))
            discovery = verify.SuiteDiscovery(tmppath)
            suites = discovery.discover()
            suite_names = [s[0] for s in suites]
            self.assertIn("npm-test", suite_names)
            self.assertIn("npm-lint", suite_names)

    def test_rust_discovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "Cargo.toml").touch()
            discovery = verify.SuiteDiscovery(tmppath)
            suites = discovery.discover()
            if shutil.which("cargo"):
                suite_names = [s[0] for s in suites]
                self.assertIn("cargo-test", suite_names)

    def test_empty_dir_discovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            discovery = verify.SuiteDiscovery(tmppath)
            suites = discovery.discover()
            self.assertEqual(len(suites), 0)


class TestMarkdownReport(unittest.TestCase):
    def test_all_passed_report(self):
        results = [
            verify.TestResult(
                name="pytest",
                category="test",
                command="pytest -q",
                exit_code=0,
                stdout="10 passed",
                stderr="",
            )
        ]
        report = verify.format_markdown_report(results)
        self.assertIn("All 1 checks passed successfully", report)
        self.assertIn("pytest", report)

    def test_failed_report(self):
        results = [
            verify.TestResult(
                name="pytest",
                category="test",
                command="pytest -q",
                exit_code=1,
                stdout="1 failed",
                stderr="",
                summary="1 failed in 0.1s",
                failures=[{
                    "test": "test_foo",
                    "location": "test_foo.py:10",
                    "snippet": "AssertionError: 1 != 2",
                }],
                rerun_cmd="pytest -k test_foo",
            )
        ]
        report = verify.format_markdown_report(results)
        self.assertIn("1 of 1 checks failed", report)
        self.assertIn("test_foo.py:10", report)
        self.assertIn("pytest -k test_foo", report)


class TestCLIExecution(unittest.TestCase):
    def test_custom_command_pass(self):
        verify_script = SKILL_DIR / "verify.py"
        res = subprocess.run(
            [sys.executable, str(verify_script), "--cmd", "python3 -c 'exit(0)'", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["passed"])
        self.assertEqual(data["passed_count"], 1)

    def test_custom_command_fail(self):
        verify_script = SKILL_DIR / "verify.py"
        res = subprocess.run(
            [sys.executable, str(verify_script), "--cmd", "python3 -c 'exit(1)'", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertFalse(data["passed"])
        self.assertEqual(data["failed_count"], 1)

    def test_shell_wrapper_execution(self):
        verify_sh = SKILL_DIR / "verify.sh"
        res = subprocess.run(
            [str(verify_sh), "--cmd", "python3 -c 'exit(0)'", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["passed"])


if __name__ == "__main__":
    unittest.main()
