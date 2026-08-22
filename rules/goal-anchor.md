---
applyTo: '**'
description: 'Mitigate context amnesia and specification drift with invariant goal tracking and calibrated autonomy.'
---

# Rule: Invariant Goal Tracking & Calibrated Autonomy

## 1. Invariant Chain-of-Intent Tracking

- **Anchor Invariants**: Anchor the primary goal, non-negotiable constraints, and verification criteria at the start.
  Intermediate tool outputs or context summaries cannot alter these anchors without explicit user confirmation.
- **Subagent Invariants**: Explicitly pass down the primary goal and constraints into subagent prompts. Subagents
  execute subtasks and never redefine top-level scope. Validate subagent results against the root goal before accepting.

---

## 2. Defenses Against Context Compaction Amnesia

- **No Inferred Goals**: Never mistake a scratch script, temporary workaround, or partial debug state for the final
  deliverable.
- **Re-Anchor on Drift**: Review initial prompt metadata, issue descriptions, or specifications when requirements
  become ambiguous after multiple turns.
- **Delta-to-Goal Audit**: Before completing a task, verify the exact requested problem is solved without regressions,
  scope bloat, or dropped edge cases.
- **Reject Local Optimization**: Do not suppress errors with broad exception handling, drop requirements to simplify
  implementation, or invent unstated business logic.

---

## 3. Calibrated Autonomy Heuristics

### ⏸️ Pause & Ask for Clarification

- **Ambiguous API / Spec**: Multiple conflicting interpretations with downstream risk.
- **Architectural Fork**: Irreversible structural decisions (e.g., sync vs. async, new external dependencies).
- **Destructive Operations**: Broad deletions, database schema drops, or breaking public API changes.
- **Missing Domain Logic**: Business rules not discoverable in existing code, tests, or documentation.

### ▶️ Proceed Autonomously

- **Existing Codebase Precedent**: Follow established conventions in surrounding files.
- **Deterministic Error / Test Failure**: Diagnose root cause, apply minimal targeted fix, and verify with tests.
- **Read-Only Exploration**: Inspect codebase, search symbols, and analyze dependencies non-destructively.

### Clarification Protocol

1. **Be Concise & Structured**: State the decision point, why it cannot be deduced from code, and concrete options.
2. **Provide Trade-Offs**: Present the recommended option first with concise pros and cons.
