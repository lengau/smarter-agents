---
applyTo: '**'
description: 'Mandatory verification gate: agents must execute automated build, lint, and test suites before committing.'
---

# Rule: Mandatory Test & Lint Verification Before Commit

## Core Directives

1. **Mandatory Pre-Commit Verification Gate**:
   - You must **NEVER commit code or declare a task complete** without actively executing the workspace's build,
     linter, and test suite and verifying that all checks pass. Prefer fixing lint issues with an auto-formatter to
     editing the file yourself.
   - If tests or linters exist in the repository, their execution is mandatory, not optional. "Looks correct" or
     theoretical verification is strictly forbidden.

2. **Repository Instructions & Command Discovery**:
   - Check repository-level instructions (`.agents/rules/`, `.github/instructions/`, `CONTRIBUTING.md`, `README.md`,
     `Makefile`, etc.) to discover the project's canonical test and lint commands.
   - If the repository instructions do not specify testing/linting procedures or if you are unsure of the appropriate
     commands, **ask the user** for clarification rather than guessing.

3. **Strict Anti-Tampering Protocol**:
   - **NEVER** modify, weaken, delete, or comment out test assertions to turn a red suite green.
   - When a test fails, the fault lies in the implementation code. Fix the implementation, not the test contract,
     unless the user explicitly requested a specification change.

4. **Root-Cause Diagnostic Protocol on Failure**:
   - On build, lint, or test failure, do NOT perform trial-and-error edits.
   - Inspect the exact failure logs and stack traces, pinpoint the divergence, and formulate a clear rationale
     before applying a targeted fix.

5. **Test Reuse & Parametrization**:
   - Prefer reusing and extending existing tests (e.g., via parametrization, adding test cases or data fixtures)
     where feasible rather than writing duplicate, boilerplate new tests from scratch.
