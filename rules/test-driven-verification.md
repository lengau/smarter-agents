---
applyTo: '**'
description: 'Mandatory verification gate: execute automated build, lint, and test suites with zero tampering.'
---

# Rule: Mandatory Test & Lint Verification Before Commit

## Core Directives

1. **Mandatory Pre-Commit Verification Gate**:
   - You must **NEVER commit code or declare a task complete** without actively executing the workspace's build,
     linter, and test suite and proving that all checks pass. Prefer fixing lint issues with an auto-formatter to
     editing files manually.
   - If tests or linters exist in the repository, their execution is mandatory, not optional. "Looks correct" or
     theoretical verification is strictly forbidden.
   - If a verification check or gate is unavailable or not applicable, obtain explicit user approval before treating
     it as skipped.

2. **Mandatory Test Coverage for All Code**:
   - All code changes, new features, and bug fixes require automated test coverage.
   - Every implementation requires at least comprehensive **unit tests**, and where applicable, **integration tests**
     and **end-to-end (E2E) tests** to validate subsystem interactions and full workflows.
   - Never consider an implementation complete without corresponding tests that exercise expected behaviors and
     edge cases.

3. **Repository Discovery & Baseline Requirements**:
   - Check repository instructions (`Makefile`, `skills/verify-and-lint`, `.agents/rules/`, `.github/instructions/`,
     `CONTRIBUTING.md`, `README.md`) to discover the project's canonical test, lint, and build commands.
   - Run relevant test suites before making changes whenever feasible to establish a clean baseline and catch
     pre-existing failures early.
   - If commands are not documented or ambiguous, ask the user for clarification rather than guessing.

4. **Strict Anti-Tampering Protocol**:
   - **NEVER** modify, weaken, delete, or bypass test assertions, thresholds, test cases, fixtures, mocks,
     snapshots, test setup, or test configuration simply to make a red suite pass.
   - Existing tests represent specified requirements. Do not weaken tests or test fixtures to mask implementation bugs.
   - Allowed test modifications:
     - Adding new tests or expanding existing test coverage for new functionality or edge cases.
     - Updating existing tests and fixtures ONLY when requirements have explicitly changed and the user approved the
       contract update.

5. **Root-Cause Diagnostic Protocol**:
   - When a build, lint, or test failure occurs, do NOT guess or apply random trial-and-error edits.
   - Follow the 5-step diagnostic and validation procedure:
     1. **Inspect**: Read the exact failure log, stack trace, and assertion diff carefully.
     2. **Locate**: Identify the precise file, line, and execution path causing the failure.
     3. **Understand & Classify**: Diagnose whether the failure stems from implementation, test code, test fixtures,
        environment, dependencies, or stale requirements.
     4. **Fix**: Apply the smallest, targeted fix addressing the diagnosed root cause.
     5. **Re-verify**: Rerun the exact failing command, then rerun all applicable build, lint, and test checks.

6. **Test Reuse & Parametrization**:
   - Prefer reusing and extending existing tests (e.g., via parametrization, adding test cases or data fixtures)
     where feasible rather than writing duplicate, boilerplate new tests from scratch.
