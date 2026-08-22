---
name: context-checkpoint
description: Standardized format and conventions for checkpointing goals, milestones, decisions, and blockers.
---

# Context Checkpoint 💾

The `context-checkpoint` skill defines standardized conventions for serializing and restoring session state
across context compactions, token truncations, and multi-turn workflows.

---

## 🎯 When to Checkpoint

1. **Task Initialization**: Anchor primary goal, scope boundaries, and acceptance criteria.
2. **Milestone Completion**: Record verified milestones immediately after automated tests pass.
3. **Key Architectural Decisions**: Log chosen designs and rationale to avoid backtracking.
4. **Active Context Changes**: Update the current step, modified files, and next actions.
5. **Session Resumption / Compaction Recovery**: Inspect `.checkpoint.json` or `SESSION.md` to re-anchor state.

---

## 📁 File Conventions

Maintain checkpoints at the workspace root (or under `.agents/checkpoints/`):

- **`.checkpoint.json`**: Machine-readable state conforming to the
  [Draft 7 Checkpoint Schema](schemas/checkpoint.schema.json). Seed from
  [`templates/checkpoint.template.json`](templates/checkpoint.template.json).
- **`SESSION.md`**: Human- and agent-readable markdown summary. Seed from
  [`templates/SESSION.template.md`](templates/SESSION.template.md).

---

## 🛠️ State Management Protocol

Agents manage checkpoints directly using file editing tools (`write_to_file`, `replace_file_content`):

1. **Initialize**: Copy and populate `templates/checkpoint.template.json` to `.checkpoint.json`.
2. **Update**: Add completed milestones, decisions, or active context directly to `.checkpoint.json`.
3. **Sync Markdown**: Keep `SESSION.md` synchronized with the structured data for easy prompt re-ingestion.
4. **Validate**: Ensure `.checkpoint.json` conforms to `schemas/checkpoint.schema.json`.

---

## 📋 Session Compaction Recovery Protocol

Upon entering a resumed session or detecting context compaction:

1. **Read `.checkpoint.json` / `SESSION.md`** first to reconstruct exact task state.
2. **Re-anchor on Goal**: Validate current plan against `goal.primary` and `goal.scope_boundaries`.
3. **Preserve Verified Milestones**: Do not re-implement or undo work recorded as completed.
4. **Respect Settled Decisions**: Follow recorded architectural choices without reopening debate.
5. **Resume Execution**: Pick up directly from `active_context.next_actions`.

---

## 📂 Bundled Resources

- Schema: [`schemas/checkpoint.schema.json`](schemas/checkpoint.schema.json)
- JSON Template: [`templates/checkpoint.template.json`](templates/checkpoint.template.json)
- Markdown Template: [`templates/SESSION.template.md`](templates/SESSION.template.md)
