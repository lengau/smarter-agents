import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add skill script to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "verify-and-lint" / "scripts"))

from verify import PolyglotDetector, OutputParser, RunnerResult, FailureDetail, format_report


class TestPolyglotDetector(unittest.TestCase):
    def test_detect_python_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "test_sample.py").write_text("def test_ok(): pass")
            (tmppath / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
            
            detector = PolyglotDetector(tmppath)
            runners = detector.detect_runners(runner_type="all")
            tools = [r[1] for r in runners]
            self.assertTrue("pytest" in tools or "unittest" in tools)

    def test_detect_javascript_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            pkg = {
                "name": "test-pkg",
                "scripts": {"test": "jest", "lint": "eslint ."},
                "devDependencies": {"jest": "^29.0.0"}
            }
            (tmppath / "package.json").write_text(json.dumps(pkg))
            (tmppath / "jest.config.js").write_text("module.exports = {};")

            detector = PolyglotDetector(tmppath)
            runners = detector.detect_runners(runner_type="all")
            tools = [r[1] for r in runners]
            self.assertTrue("npm-test" in tools or "jest" in tools)
            self.assertTrue("npm-lint" in tools or "eslint" in tools)

    def test_detect_rust_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "Cargo.toml").write_text("[package]\nname = \"foo\"\nversion = \"0.1.0\"\n")

            detector = PolyglotDetector(tmppath)
            runners = detector.detect_runners(runner_type="all")
            tools = [r[1] for r in runners]
            # If cargo is in PATH, it detects cargo-test
            import shutil
            if shutil.which("cargo"):
                self.assertIn("cargo-test", tools)

    def test_detect_go_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "go.mod").write_text("module example.com/foo\n")
            (tmppath / "main.go").write_text("package main\n")

            detector = PolyglotDetector(tmppath)
            runners = detector.detect_runners(runner_type="all")
            tools = [r[1] for r in runners]
            import shutil
            if shutil.which("go"):
                self.assertIn("go-test", tools)


class TestOutputParser(unittest.TestCase):
    def test_parse_pytest_failure(self):
        sample_output = """
============================= test session starts ==============================
rootdir: /path/to/project
collected 2 items

tests/test_math.py .F                                                    [100%]

=================================== FAILURES ===================================
_________________________________ test_divide __________________________________

    def test_divide():
>       assert divide(4, 2) == 3
E       AssertionError: assert 2 == 3

tests/test_math.py:12: AssertionError
=========================== short test summary info ============================
FAILED tests/test_math.py::test_divide - AssertionError: assert 2 == 3
========================= 1 failed, 1 passed in 0.05s ==========================
"""
        summary, failures = OutputParser.parse("pytest", sample_output, exit_code=1)
        self.assertIn("1 failed, 1 passed in 0.05s", summary)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].name, "test_divide")
        self.assertIn("assert 2 == 3", failures[0].message)

    def test_parse_pytest_success(self):
        sample_output = "========================= 12 passed in 0.15s =========================="
        summary, failures = OutputParser.parse("pytest", sample_output, exit_code=0)
        self.assertTrue(summary.startswith("✓ pytest:"))
        self.assertEqual(len(failures), 0)

    def test_parse_ruff_failure(self):
        sample_output = """
src/app.py:10:5: F401 `os` imported but unused
src/app.py:25:1: E302 Expected 2 blank lines, found 1
Found 2 errors.
"""
        summary, failures = OutputParser.parse("ruff", sample_output, exit_code=1)
        self.assertIn("2", summary)
        self.assertEqual(len(failures), 2)
        self.assertIn("[F401]", failures[0].name)
        self.assertIn("`os` imported but unused", failures[0].message)

    def test_parse_cargo_test_failure(self):
        sample_output = """
running 2 tests
test tests::test_pass ... ok
test tests::test_fail ... FAILED

failures:

---- tests::test_fail stdout ----
thread 'tests::test_fail' panicked at 'assertion failed: `(left == right)`

failures:
    tests::test_fail

test result: FAILED. 1 passed; 1 failed; 0 ignored
"""
        summary, failures = OutputParser.parse("cargo-test", sample_output, exit_code=101)
        self.assertIn("FAILED", summary)
        self.assertTrue(any(f.name == "tests::test_fail" for f in failures))

    def test_parse_go_test_failure(self):
        sample_output = """
=== RUN   TestAdd
--- PASS: TestAdd (0.00s)
=== RUN   TestSubtract
--- FAIL: TestSubtract (0.00s)
    calc_test.go:15: Subtract(5, 3) = 1; want 2
FAIL
FAIL	example.com/calc	0.003s
FAIL
"""
        summary, failures = OutputParser.parse("go-test", sample_output, exit_code=1)
        self.assertIn("FAIL", summary)
        self.assertTrue(any(f.name == "TestSubtract" for f in failures))


class TestReportFormatting(unittest.TestCase):
    def test_format_all_passed(self):
        results = [
            RunnerResult(
                tool="pytest",
                category="test",
                command=["pytest", "-q"],
                exit_code=0,
                passed=True,
                summary="✓ pytest: 10 passed in 0.2s",
                duration_sec=0.2,
            )
        ]
        report = format_report(results)
        self.assertIn("ALL CHECKS PASSED", report)
        self.assertIn("✅ PASS", report)

    def test_format_with_failures(self):
        results = [
            RunnerResult(
                tool="pytest",
                category="test",
                command=["pytest", "-q"],
                exit_code=1,
                passed=False,
                summary="1 failed in 0.1s",
                failures=[
                    FailureDetail(
                        name="test_foo",
                        message="AssertionError: 1 != 2",
                        location="tests/test_foo.py:10",
                        stack_trace=["> assert 1 == 2", "E AssertionError: 1 != 2"]
                    )
                ],
                duration_sec=0.1,
            )
        ]
        report = format_report(results)
        self.assertIn("FAILED", report)
        self.assertIn("test_foo", report)
        self.assertIn("AssertionError: 1 != 2", report)

    def test_format_json(self):
        results = [
            RunnerResult(
                tool="pytest",
                category="test",
                command=["pytest"],
                exit_code=0,
                passed=True,
                summary="ok",
            )
        ]
        report = format_report(results, json_output=True)
        data = json.loads(report)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["tool"], "pytest")


if __name__ == "__main__":
    unittest.main()
