---
applyTo: '**'
description: 'Safe file editing, state freshness verification, surgical replacements, and truncation prevention.'
---

# Robust File Operations & State Synchronization

## 1. Overview & Core Objective

File manipulation is a critical failure point for autonomous coding agents. Agents frequently encounter:

- **Stale buffer desynchronization**: Editing against outdated in-memory context or shifted line numbers.
- **Whole-file rewrite truncation**: Rewriting whole files, hitting token limits, and leaving corrupted files.
- **Ambiguous replacement target failures**: Passing short search patterns that match multiple locations.
- **Blind retry loops**: Resending failed edits repeatedly without re-inspecting current disk contents.

This rule enforces strict operational procedures for reading, editing, and verifying files.

---

## 2. Mandatory File Operation Rules

### Rule 1: Freshness & Stale Buffer Verification

1. **Inspect immediately before editing**: Inspect the target slice or symbol immediately prior to submitting a change.
   Perform a write-time comparison between expected target content and current disk content; abort if they differ.
2. **Never assume line numbers remain static**: Any prior edit shifts line numbers. Re-anchor line ranges against current
   disk state.
3. **Respect file conventions**: Match existing line endings (`\n` vs. `\r\n`), indentation (tabs vs. spaces, width),
   and trailing newline conventions.

### Rule 2: Surgical Modifications Over Full-File Rewrites

1. **Avoid full-file overwrites**: For existing files with more than 50 lines, never rewrite the entire file to modify a
   localized section. Use targeted contiguous chunk replacement (`replace_file_content` or diff patch).
2. **Chunk size limitation**: Keep individual edit chunks bounded (under 100 contiguous lines per replacement call).
   Split large changes into smaller, cohesive edits.
3. **Prevent output truncation loops**: If a write outputs truncated content or creates syntax errors, immediately
   inspect the file rather than attempting another full-file write blindly.

### Rule 3: Strict Target Uniqueness & Context Anchoring

1. **Context anchors**: Surrounding context aids identification but does not guarantee uniqueness. Include sufficient
   surrounding lines (function headers, decorators, adjacent comments) to ensure an exact match.
2. **Single match validation**: Perform a pre-edit match-count check using the same search scope and matching semantics
   as the edit operation. Require exactly one match as the validity condition before replacing.
3. **Exact character matching**: Match leading whitespace, indentation, docstrings, and comments byte-for-byte.

### Rule 4: Idempotent Failure Recovery

When an edit or patch operation fails:

1. **Do NOT blindly retry the identical tool call**: A failed replacement indicates a mismatch with disk state.
2. **Execute Diagnostic Sequence**:
   - **Step A (Inspect)**: Read the surrounding 20–30 lines around the intended target area.
   - **Step B (Idempotency Check)**: Determine whether a previous step or tool already applied the change.
   - **Step C (Recalibrate)**: Extract the exact lines directly from the fresh disk view and formulate a newly anchored
     replacement chunk.
3. **Partial Write Recovery**: If a partial write leaves a file truncated, incomplete, or invalid, immediately restore
   the pre-edit backup or git state before proceeding.

### Rule 5: Post-Edit Integrity & Syntax Validation

1. **Syntax validation**: After applying edits, run a file-type-aware parser, syntax check, or linter (e.g. `ruff check`,
   `python3 -m py_compile`, `tsc --noEmit`) as the primary verification.
2. **Supplemental diff check**: Check `git diff` as supplemental evidence to confirm that old and new target counts
   match expected values and no unintended deletions or orphaned tokens occurred.

---

## 3. Anti-Patterns vs. Safe Practices

| Anti-Pattern | Risk | Safe Practice |
| :--- | :--- | :--- |
| **Blind full-file overwrite** (`write_to_file` of 50+ lines) | Truncation, token limit cutoff, lost helper functions | Surgical replacement (`replace_file_content`) with localized target lines. |
| **Editing without re-viewing** | Desync error, wrong line numbers, missed concurrent changes | View target lines immediately prior to submitting the replacement. |
| **Minimal 1-line target without context** (`target = "def foo():"`) | Matches multiple declarations or incorrect class methods | Anchor with 2–3 surrounding lines (preceding decorator, class header, docstring). |
| **Infinite retry of failed edit** | Endless loop, context exhaustion | Read current lines on disk, identify mismatch, and update target content. |
| **Assuming edits are idempotent** | Duplicate code blocks, invalid syntax | Verify disk state and run syntax/test checks after editing. |

---

## 4. Agent Execution Checklist

Before submitting any file edit:

- [ ] Have I viewed the target file or specific line slice immediately before editing?
- [ ] Is `TargetContent` verified to match exactly one unique location?
- [ ] Is the replacement chunk bounded to avoid truncation risks?
- [ ] Did I preserve the original indentation, whitespace, and comment structure?

After submitting any file edit:

- [ ] Did the edit tool report success?
- [ ] If failed or partially written, did I restore pre-edit state and inspect disk lines?
- [ ] Did I verify syntax using a language linter or compiler?
