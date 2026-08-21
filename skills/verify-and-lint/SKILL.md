---
name: verify-and-lint
description: Automated polyglot test and lint diagnostic runner that discovers project test suites and formats concise, low-token failure summaries.
---

# Verify & Lint Diagnostic Runner (`verify-and-lint`)

A specialized skill and execution harness designed to eliminate agent hallucination of test passes, catch syntax/lint regressions early, and present compact, high-signal failure traces without overflowing context windows.

---

## 🎯 When to Use This Skill

Activate or execute this skill whenever:
1. **Pre-Completion Verification Gate**: Before declaring any coding or refactoring task complete.
2. **Regression Check**: After modifying files to confirm no existing functionality was broken.
3. **Targeted Triage**: When diagnosing specific test or lint failures across unfamiliar polyglot codebases.
4. **Context Conservation**: When full test outputs (e.g. thousands of passing lines) would exhaust the model context window.

---

## 🛠️ Ecosystem Discovery & Supported Runners

The included runner (`scripts/verify.py` / `scripts/verify.sh`) automatically detects repository structure and triggers appropriate commands:

| Ecosystem | Config / Marker Files | Default Test Command | Default Lint Command |
| :--- | :--- | :--- | :--- |
| **Python** | `pyproject.toml`, `pytest.ini`, `setup.py`, `tests/` | `pytest -q` (or `unittest`) | `ruff check .` / `flake8 .` |
| **JavaScript / TypeScript** | `package.json`, `pnpm-lock.yaml`, `yarn.lock` | `npm test` / `pnpm test` / `yarn test` | `npm run lint` / `npm run check` |
| **Rust** | `Cargo.toml` | `cargo test` | `cargo clippy -- -D warnings` |
| **Go** | `go.mod`, `*_test.go` | `go test ./...` | `golangci-lint run` |
| **Java / Kotlin** | `pom.xml`, `build.gradle`, `gradlew` | `mvn test -q` / `./gradlew test -q` | Maven/Gradle check tasks |
| **C / C++ / CMake** | `CMakeLists.txt`, `Makefile` | `ctest --output-on-failure` / `make test` | `clang-tidy` / compiler warnings |

---

## 📋 Standard Verification Protocol

Follow this 4-step protocol when running verification:

### 1. Execute Polyglot Discovery
Run the verify script from the repository root:
```bash
# Automated polyglot verification (runs tests + linter)
python3 skills/verify-and-lint/scripts/verify.py

# Or using the shell wrapper:
./skills/verify-and-lint/scripts/verify.sh
```

### 2. Inspect Low-Token Failure Summaries
When tests fail, `verify.py` isolates only the failing test cases, exception traces, and failure lines, discarding hundreds of lines of passing noise:
```markdown
## 🧪 Verification & Lint Diagnostic Summary

❌ **1 of 2 checks failed.**

### ❌ `pytest` (TEST)
- **Command**: `pytest -q`
- **Status**: FAILED (Exit code 1)
- **Summary**: 1 failed, 14 passed in 0.42s
- **Targeted Re-run**: `pytest -k 'test_parse_failure'`

**Failures / Diagnostics:**

> **tests/test_parser.py::test_parse_failure** (tests/test_parser.py:42)
> ```text
> >       assert result.status == "success"
> E       AssertionError: assert 'failed' == 'success'
> ```
```

### 3. Perform Targeted Re-runs
Use the suggested targeted re-run command while iterating on the fix to minimize execution time and token usage:
```bash
# Example targeted re-run:
pytest -k 'test_parse_failure'
```

### 4. Zero Anti-Tampering Rule
> [!CRITICAL]
> **Never modify, delete, or weaken test assertions to make a test suite pass.**
> If a test fails after your changes:
> - Review the root cause in the application code.
> - Fix the implementation to satisfy the original contract.
> - Only modify tests if the issue explicitly specifies a breaking specification change.

---

## ⚙️ CLI Options & Overrides

| Option | Flag | Description |
| :--- | :--- | :--- |
| **Path** | `--path <dir>`, `-p <dir>` | Specify target project directory (default: `.`) |
| **Test Only** | `--test-only`, `--test` | Run only discovered test suites |
| **Lint Only** | `--lint-only`, `--lint` | Run only discovered linters |
| **Custom Command** | `--cmd "<command>"` | Execute explicit command(s) with filtering |
| **JSON Output** | `--json` | Return structured JSON object for automated parsers |
| **Verbose** | `--verbose`, `-v` | Keep full un-truncated stdout/stderr |

### Example CLI Usages:
```bash
# Run tests only on a sub-package
python3 skills/verify-and-lint/scripts/verify.py --test-only --path ./packages/backend

# Run custom verification commands with structured failure triage
python3 skills/verify-and-lint/scripts/verify.py --cmd "pytest tests/unit" --cmd "mypy src"

# Emit JSON for programmatic inspection
python3 skills/verify-and-lint/scripts/verify.py --json
```
