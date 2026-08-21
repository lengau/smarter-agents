---
name: verify-and-lint
description: Automated polyglot test and lint diagnostic runner that discovers workspace test suites, executes targeted checks, captures exit codes, suppresses verbose passing noise, and outputs concise failure stack traces.
---

# verify-and-lint

A polyglot diagnostic test and lint runner designed to give AI coding agents fast, accurate, and token-efficient feedback across multiple software ecosystems.

## Overview

Agents often struggle with standard test runners because:
1. **Token Bloat**: Passing tests output hundreds or thousands of lines of logs, pushing critical context out of the agent's context window.
2. **Obscured Failures**: Real assertion errors and stack traces are buried inside wall-of-text compiler outputs or long dependency traces.
3. **Multi-Language Heterogeneity**: Different projects use pytest, jest, vitest, cargo test, go test, ctest, ruff, eslint, etc.
4. **Ignored Exit Codes**: Agents may mistakenly assume a test run passed when a subtle error code was emitted.

The `verify-and-lint` skill solves this by providing a unified runner script (`scripts/verify.py` and `scripts/verify.sh`) that automatically detects the project stack, executes tests and linters, filters out passing noise, isolates root-cause failure traces, and formats a clean markdown report.

---

## Supported Ecosystems & Auto-Detection

| Ecosystem | Detected Configs / Files | Test Runner | Linter / Type Checker |
|---|---|---|---|
| **Python** | `pyproject.toml`, `setup.py`, `conftest.py`, `pytest.ini`, `*.py` | `pytest` (via `uv`/`poetry` if present) or `unittest` | `ruff`, `flake8`, `mypy` |
| **JavaScript / TypeScript** | `package.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb` | `vitest`, `jest`, `npm/pnpm/yarn/bun test` | `eslint`, `biome`, `tsc --noEmit` |
| **Rust** | `Cargo.toml` | `cargo test` | `cargo clippy`, `cargo check` |
| **Go** | `go.mod`, `*.go` | `go test ./...` | `golangci-lint` |
| **C / C++** | `CMakeLists.txt`, `Makefile` | `ctest`, `make test` | Compiler diagnostics |
| **Java / Kotlin** | `gradlew`, `build.gradle`, `pom.xml` | `./gradlew test`, `mvn test` | Checkstyle / SpotBugs |
| **Ruby** | `Gemfile`, `.rspec` | `bundle exec rspec`, `rake test` | RuboCop |

---

## Quick Usage

Run the verification wrapper directly from the workspace or skill directory:

```bash
# Run full verification suite (auto-detect all tests and linters)
python3 skills/verify-and-lint/scripts/verify.py

# Or via the shell script wrapper:
./skills/verify-and-lint/scripts/verify.sh
```

### Targeted Execution Options

```bash
# Run only test suites (skip linters)
python3 skills/verify-and-lint/scripts/verify.py --type test

# Run only linters and type checkers
python3 skills/verify-and-lint/scripts/verify.py --type lint

# Target a specific test file or pattern
python3 skills/verify-and-lint/scripts/verify.py --target tests/test_parser.py

# Explicitly select a runner
python3 skills/verify-and-lint/scripts/verify.py --runner pytest

# Limit surfaced failure stack traces (default: 5)
python3 skills/verify-and-lint/scripts/verify.py --max-failures 3

# Machine-readable JSON output
python3 skills/verify-and-lint/scripts/verify.py --json
```

---

## Agent Workflow Guide

When working on a feature, bugfix, or refactoring task, follow this 4-step diagnostic cycle:

```mermaid
flowchart LR
    A[1. Baseline Check] --> B[2. Targeted Fix]
    B --> C[3. Focused Re-run]
    C -->|Fails| B
    C -->|Passes| D[4. Full Polyglot Suite]
```

### Step 1: Baseline Verification
Before making any edits, establish ground truth by running the test suite to verify whether the test baseline is clean:
```bash
python3 skills/verify-and-lint/scripts/verify.py --type test
```
- If baseline tests fail *before* your edits, note the pre-existing failures to avoid regressing or confusing them with new code.

### Step 2: Focused Target Execution During Iteration
When writing unit tests or fixing specific bugs, avoid running the entire test suite on every keystroke. Use `--target` to narrow execution:
```bash
python3 skills/verify-and-lint/scripts/verify.py --runner pytest --target tests/test_feature.py
```

### Step 3: Diagnostic Parsing of Failures
When a check fails, the report surfaces:
- Failed assertion statement
- Exact filename and line number
- Key stack frames (inner application code, stripping third-party library boilerplate)
Use this concise failure trace directly to guide your next code edit.

### Step 4: Full Suite & Lint Confirmation
Once the targeted test passes, run the complete suite including linters to ensure zero collateral regressions:
```bash
python3 skills/verify-and-lint/scripts/verify.py --type all
```
Ensure the process exit code is `0` and status is `ALL CHECKS PASSED`.

---

## Output Example

When all suites pass:
```markdown
## 🧪 Verification & Lint Report

**Status:** ✅ ALL CHECKS PASSED (2/2 suites successful)

| Category | Tool | Command | Status | Duration |
|---|---|---|---|---|
| TEST | **pytest** | `pytest -q --tb=short` | ✅ PASS | 0.84s |
| LINT | **ruff** | `ruff check .` | ✅ PASS | 0.05s |
```

When tests fail:
```markdown
## 🧪 Verification & Lint Report

**Status:** ❌ 1 OF 2 SUITE(S) FAILED

| Category | Tool | Command | Status | Duration |
|---|---|---|---|---|
| TEST | **pytest** | `pytest -q --tb=short` | ❌ FAIL (1) | 0.42s |
| LINT | **ruff** | `ruff check .` | ✅ PASS | 0.05s |

### 🔍 Failure Diagnostic Summaries

#### ❌ pytest (TEST)
**Summary:** 1 failed, 14 passed in 0.42s

Surfacing top 1 failures:
- **#1 test_detector_finds_pytest**
  - Location: `tests/test_verify.py:45`
  - Message: `AssertionError: assert 'pytest' in ['unittest']`
  - Trace:
    ```
    > assert 'pytest' in detected_tools
    E AssertionError: assert 'pytest' in ['unittest']
    ```
```

---

## Key Principles & Best Practices

1. **Always Check Exit Codes**: Never declare a task complete if the verification script exits with non-zero.
2. **Preserve Context Space**: Do not run raw test commands with verbose flag (`-vvv` or `--nocapture`) unless explicitly debugging an unparsed silent crash.
3. **Polyglot Monorepo Awareness**: If working in a subdirectory or monorepo sub-package, pass `--dir <subpath>` to target the correct workspace scope.
