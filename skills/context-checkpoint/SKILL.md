---
name: context-checkpoint
description: Standardized format and CLI for recording active goals, verified milestones, architectural decisions, and known blockers to survive aggressive context window compaction and multi-turn amnesia.
---

# Context Checkpoint 💾

The `context-checkpoint` skill provides agents with a compact, deterministic mechanism to serialize and restore session state across context truncations, memory compactions, and multi-turn workflows.

When context windows fill up or compaction summarization occurs, long chains of thought, nuanced constraints, architectural decisions, and verified milestones are frequently lost or distorted. This skill provides a standardized file format (`.checkpoint.json` and human-readable `SESSION.md`), JSON schema, validation rules, and a lightweight Python CLI utility to snapshot, update, and restore session state.

---

## 🎯 When to Use This Skill

1. **Long-Running & Multi-Step Tasks**: Any task spanning more than 3-5 turns, multiple files, or requiring extensive research before implementation.
2. **Prior to Context Window Compaction**: Whenever approaching context limits or before handing off to subagents.
3. **Milestone Verification**: Immediately after running tests or verifying a component, record the verified status so progress is not lost.
4. **Architectural & Design Decisions**: Whenever choosing an implementation strategy over alternatives, record the rationale to prevent backtracking.
5. **Session Resumption**: When starting or resuming an agent session, read `.checkpoint.json` / `SESSION.md` first to reconstruct the exact state of work.

---

## 📁 Checkpoint File Formats

A checkpoint consists of two synchronized representations:
1. **`.checkpoint.json`** (Machine-readable): A strictly structured JSON file conforming to the [checkpoint schema](schemas/checkpoint.schema.json).
2. **`SESSION.md`** (Human/Agent-readable markdown): A clean, token-efficient markdown summary rendered directly from `.checkpoint.json` for rapid ingestion in agent system prompts or user inspection.

Both files are maintained at the repository/workspace root or in `.agents/checkpoints/`.

---

## 🧱 Checkpoint Schema Overview

A valid `.checkpoint.json` contains the following sections:

```json
{
  "$schema": "https://raw.githubusercontent.com/lengau/smarter-agents/main/skills/context-checkpoint/schemas/checkpoint.schema.json",
  "version": "1.0.0",
  "session_id": "session-2026-08-21-001",
  "updated_at": "2026-08-21T18:40:00Z",
  "goal": {
    "primary": "Implement oauth2 refresh token rotation in auth service",
    "scope_boundaries": [
      "Modify src/auth/oauth.py and src/auth/tokens.py only",
      "Do not alter user profile schemas or database migrations"
    ],
    "acceptance_criteria": [
      "Tokens rotate upon every refresh call",
      "Expired or reused refresh tokens immediately revoke family",
      "All unit tests in tests/auth/ pass with 100% success"
    ]
  },
  "milestones": [
    {
      "id": "M1",
      "title": "Unit tests for refresh token store",
      "status": "completed",
      "verified_by": "pytest tests/auth/test_tokens.py -k test_refresh",
      "timestamp": "2026-08-21T18:25:00Z"
    },
    {
      "id": "M2",
      "title": "Implement token rotation logic",
      "status": "in_progress",
      "verified_by": null,
      "timestamp": null
    }
  ],
  "decisions": [
    {
      "id": "D1",
      "topic": "Token family tracking",
      "choice": "Store family UUID in Redis hash with TTL matching refresh window",
      "rationale": "Avoids relational DB lock contention on high-frequency auth refreshes"
    }
  ],
  "blockers": [
    {
      "id": "B1",
      "description": "Mock Redis server in CI sometimes flakes on async disconnect",
      "status": "active",
      "workaround": "Use redis-mock fixture with explicit flushdb in teardown"
    }
  ],
  "active_context": {
    "current_step": "Implementing handle_reuse_detection in src/auth/tokens.py",
    "open_files": [
      "src/auth/tokens.py",
      "tests/auth/test_tokens.py"
    ],
    "next_actions": [
      "Add revocation cascade on token reuse",
      "Run full test suite: pytest tests/auth/"
    ]
  }
}
```

---

## 🛠️ CLI Helper Tool: `checkpoint.py`

The skill includes a lightweight Python utility at [`scripts/checkpoint.py`](scripts/checkpoint.py).

### Quick Commands

```bash
# Initialize a new session checkpoint
python3 skills/context-checkpoint/scripts/checkpoint.py init --goal "Implement feature X"

# Add a milestone
python3 skills/context-checkpoint/scripts/checkpoint.py milestone add --title "Create data models" --status in_progress

# Complete and verify a milestone
python3 skills/context-checkpoint/scripts/checkpoint.py milestone complete M1 --verify-cmd "pytest tests/test_models.py"

# Record an architectural decision
python3 skills/context-checkpoint/scripts/checkpoint.py decision add --topic "Database" --choice "PostgreSQL" --rationale "ACID compliance needed for financial ledgers"

# Log a blocker or issue
python3 skills/context-checkpoint/scripts/checkpoint.py blocker add --desc "Missing API key for staging" --workaround "Using mock provider"

# Update active working context
python3 skills/context-checkpoint/scripts/checkpoint.py update-context --step "Refactoring auth controller" --next-action "Run pytest"

# Render or synchronize SESSION.md from .checkpoint.json
python3 skills/context-checkpoint/scripts/checkpoint.py render

# Validate .checkpoint.json against schema
python3 skills/context-checkpoint/scripts/checkpoint.py validate
```

---

## 📋 Session Compaction Recovery Protocol

When an agent detects that context has been compacted, or upon entering a resumed session:

1. **Look for `.checkpoint.json` or `SESSION.md`** at the root of the workspace.
2. **Re-anchor on Primary Goal**: Ensure current execution matches `goal.primary` and respects `goal.scope_boundaries`.
3. **Review Completed Milestones**: Never re-implement or undo work verified in completed milestones unless an explicit regression is identified.
4. **Respect Architectural Decisions**: Do not re-open settled debates recorded in `decisions`.
5. **Resume Next Actions**: Pick up immediately from `active_context.next_actions`.
6. **Update Checkpoint**: After completing the next unit of work, update `.checkpoint.json` and sync `SESSION.md`.

---

## 📂 Bundled Resources

- Schema: [`schemas/checkpoint.schema.json`](schemas/checkpoint.schema.json)
- Template JSON: [`templates/checkpoint.template.json`](templates/checkpoint.template.json)
- Template Markdown: [`templates/SESSION.template.md`](templates/SESSION.template.md)
- CLI Utility: [`scripts/checkpoint.py`](scripts/checkpoint.py)
