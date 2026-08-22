---
applyTo: '**'
description: 'Prevent test gaming by isolating test harness from builder agent; blind grading with held-out checks.'
---

# Rule: Test Harness Isolation & Blind Grading

## Core Directives

### 1. Blind Grader Isolation

- **Test files must reside in isolated context** the producing agent cannot read or access during implementation.
- **Grader runs in separate process/session** with no access to builder workspace, files, or reasoning trace.
- **Builder receives only high-level criteria** (paraphrased requirements), never the actual test assertions or test files.

### 2. Held-Out Test Generation

- **Actual assertions hidden** from builder until grading phase.
- **Generate held-out tests** not visible to builder for critical paths.
- **Score genuinely earned**: passes both paraphrased criteria AND held-out checks.

### 3. Trajectory Monitoring for Test Gaming

- **Detect "inspect-grader-first" pattern**: Agent opens test file before writing implementation.
- **Flag special-casing**: Output matches inspected assertions exactly but fails held-out cases.
- **Score-vs-held-out gap detection**: Widening gap between visible-test score and held-out performance across runs.
- **Alert/block** on grader-reconnaissance trajectories.

### 4. Test Harness Protection

- **Unit test files marked read-only** for builder agent.
- **Integration/e2e tests in separate isolated environment** with no builder access.
- **Test configuration, fixtures, mocks** similarly protected.

### 5. Verification Gates

- **Builder implementation evaluated against full test suite** (visible + held-out) by blind grader.
- **No test modifications by builder** to make tests pass (enforced by `test-driven-verification.md` anti-tampering).
- **Test changes require explicit user approval** and separate review.

## Anti-Patterns Prevented

| Anti-Pattern | Detection | Mitigation |
|--------------|-----------|------------|
| Read test file → special-case assertions → false pass | Trajectory monitor: file access before implementation | Blind grader isolation |
| Weaken test assertions to pass | Anti-tampering protocol + read-only test files | Immutable test harness |
| Mock unit under test instead of fixing | Blind grader runs real tests, not mocked | Held-out real tests |
| Reconnaissance-then-exploit trajectory | Pattern detection in tool call sequence | Alert + block |

## Implementation Requirements

### For Agent Harnesses

1. **Separate grading context**: Spawn grader in isolated process/container with only artifact + rubric.
2. **Test file permissions**: Builder gets read-only or no access to test directories.
3. **Held-out test generator**: Automated generation of paraphrased criteria + hidden assertions.
4. **Trajectory logger**: Record all file accesses, tool calls for anomaly detection.

### For Repository Configuration

1. **Test directory structure**:
   ```
   tests/
   ├── visible/          # Builder may see (high-level criteria only)
   ├── hidden/           # Actual assertions (builder no access)
   └── heldout/          # Generated held-out tests (builder no access)
   ```

2. **CI/CD integration**: Blind grading runs in separate job with restricted permissions.

## Integration with Other Rules

- **`test-driven-verification.md`**: Anti-tampering protocol complements isolation; both required.
- **`adversarial-verification.md`**: Blind grader acts as verifier agent in maker-checker pattern.
- **`scoped-autonomy.md`**: Builder scope explicitly excludes test directories.
- **`robust-file-ops.md`**: Read-only enforcement for test files.

## References

- Agent Patterns Catalog: Verifier-Aware Reward Hacking
- ClayBuddy: Harness errors from underspecification (arXiv:2606.19380)
- WOWHOW Failure Taxonomy: Mode 11 - Test Oracle Confusion
- Adversarial Review: Maker-checker separation (arXiv:2608.18167)