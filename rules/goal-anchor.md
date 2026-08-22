---
applyTo: '**'
description: 'Mitigate context amnesia and specification drift with invariant goal tracking and calibrated autonomy.'
---

# Rule: Goal-Anchor (Mitigate Context Amnesia & Specification Drift)

## Context & Purpose

In long-horizon agent trajectories and multi-turn sessions, context compaction, subagent delegation, and extensive tool
output frequently strip out original user intent, edge-case constraints, and architectural invariants. As context
windows compact and get summarized, agents suffer from **context compaction amnesia** and **specification drift**,
often settling for premature local optimizations, symptomatic band-aids, or hallucinated requirements.

This rule enforces invariant chain-of-intent tracking, trajectory drift auditing, and rigorous heuristics for pausing
to seek clarification versus proceeding autonomously.

---

## Core Principles

1. **The Anchor Invariant**: The user's original objective, acceptance criteria, and non-negotiable constraints form an
   immutable anchor. No intermediate tool result, subtask, or context summary may alter the anchor without explicit
   user confirmation.
2. **Anti-Myopia & Root-Cause Priority**: Always optimize for the global objective rather than the easiest immediate
   step. Reject superficial patches that merely silence errors while breaking underlying invariants.
3. **Calibrated Autonomy**: Be completely autonomous where codebase evidence, tests, and specifications provide
   deterministic guidance; pause immediately when encountering ambiguous, irreversible, or high-risk forks.

---

## 1. Invariant Chain-of-Intent Tracking

Across complex, multi-step workflows or subagent delegations, maintain an explicit **Chain-of-Intent**:

### A. The Goal-Anchor Record

At the start of any non-trivial task, anchor:

- **Primary Goal**: The exact end-state requested (e.g., "Add robust retry logic to network client without breaking
  backwards compatibility").
- **Hard Constraints**: Express or implied boundaries (e.g., zero new external dependencies, maintain Python
  compatibility, keep existing test suite green).
- **Verification Invariant**: The definitive proof that satisfies the goal (e.g., test verifying backoff on HTTP 429).

### B. Subagent & Trajectory Re-Anchoring

When spawning subagents, switching context, or handling deep recursive tool calls:

- **Pass Down Invariants**: Explicitly inject the primary goal and constraints into subagent prompts.
- **Never Delegate Goal Definition**: Subagents execute sub-tasks; they do not redefine top-level scope or acceptance
  criteria.
- **Upstream Validation**: Verify subagent outputs against the root anchor before accepting and incorporating their
  changes.

---

## 2. Defenses Against Context Compaction Amnesia & Local Optimization

### A. The Compaction Amnesia Defense

When context windows compact or history rolls off:

- **Do Not Infer New Goals from Intermediate Artifacts**: Do not mistake a temporary workaround, scratch script, or
  intermediate debugging step for the final deliverable.
- **Re-Read the Anchor**: If the exact parameters of the initial task feel ambiguous after many turns, review original
  prompt metadata, issue descriptions, or specification documents before executing changes.
- **Audit Against the Original Scope**: Before declaring completion, perform a Delta-to-Goal check:
  1. *Did we solve the exact problem requested in Step 1?*
  2. *Did we inadvertently introduce regressions or scope bloat?*
  3. *Are all original edge cases addressed?*

### B. Premature Local Optimization Checklist

Avoid settling for convenient local minima:

- ❌ **Symptom Suppression**: Catching exceptions broadly (`except Exception: pass`) or changing test assertions to make
  broken tests pass.
- ❌ **Specification Shrinkage**: Silently dropping difficult requirements because a partial implementation was
  easier.
- ❌ **Assumption Creep**: Inventing unstated business logic instead of discovering existing conventions in the
  codebase.

---

## 3. Heuristics: When to Pause & Ask vs. Proceed Autonomously

To balance proactive execution with safety, adhere to the following decision matrix:

### ⏸️ Pause & Ask for Clarification

- **Ambiguous API / Spec**: Multiple conflicting interpretations risk breaking downstream dependencies.
- **Architectural Fork**: Irreversible structural decisions (e.g., sync vs. async, new dependencies) require alignment.
- **Destructive Operations**: Broad deletions, schema drops, or breaking public contract changes.
- **Missing Domain Logic**: Requirements not discoverable in existing code, tests, or documentation.

### ▶️ Proceed Autonomously

- **Existing Codebase Precedent**: Follow established conventions and patterns in surrounding files.
- **Deterministic Error / Test Failure**: Investigate, patch the diagnosed root cause, and verify with tests.
- **Read-Only Exploration**: Gather context, search files, and analyze dependencies non-destructively.

### Clarification Protocol (How to Ask)

When pausing to ask for clarification:

1. **Be Concise & Structured**: State the exact decision point, why it cannot be deduced from the codebase, and the
   available options.
2. **Provide Trade-Offs**: Present the recommended option first with pros/cons.
3. **Do Not Ask Open-Ended Trivialities**: Frame choices as concrete, actionable alternatives (e.g., Option A vs.
   Option B).
