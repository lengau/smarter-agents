# Robust File Operations & State Synchronization

## 1. Overview & Core Objective
File manipulation is one of the most brittle operations for autonomous coding agents. In harnesses such as **Pi**, **OpenCode**, **SWE-agents**, and **Antigravity**, agents frequently encounter:
- **Stale buffer desynchronization**: Making edits based on outdated in-memory context or obsolete line numbers after prior modifications or background tool executions.
- **Whole-file rewrite truncation loops**: Rewriting entire large files via overwrite tools, hitting token output limits or stream cutoffs, resulting in corrupted or half-written files.
- **Non-unique replacement target failures**: Passing short or ambiguous search patterns to replacement tools that match multiple locations or zero locations due to whitespace/line-ending mismatch.
- **Blind retry loops**: Repeatedly sending the exact same failed edit without re-inspecting current disk contents.

This rule enforces strict operational procedures for reading, editing, and verifying files across any agent harness.

---

## 2. Mandatory File Operation Rules

### Rule 1: Freshness & Stale Buffer Verification
1. **Always inspect before editing**: Before replacing lines or applying surgical patches to an existing file, inspect the target range using a viewing tool (e.g. `view_file`, `grep_search`, or harness-specific file read tools).
2. **Never assume line numbers remain static**: Any prior edit, format pass, or tool invocation shifts line numbers down or up. Always re-anchor line ranges against the current disk state.
3. **Normalize and respect line endings**: Be mindful of platform line endings (`\n` vs `\r\n`) and trailing newlines. Ensure replacement blocks preserve the existing formatting, indentation style (spaces vs tabs), and trailing newline conventions of the file.

### Rule 2: Surgical Modifications Over Full-File Rewrites
1. **Avoid full-file overwrites on existing files**: For any existing file with more than 50 lines, NEVER replace the entire file to change a localized section. Use targeted contiguous chunk replacement (`replace_file_content`, diff patch, or AST-aware edit).
2. **Chunk size limitation**: Keep individual edit chunks bounded (ideally under 100 contiguous lines per replacement call). Split large refactorings into a series of smaller, logically cohesive edits.
3. **Prevent output truncation loops**: Full-file rewrites risk token limit exhaustion, network timeouts, or tool streaming truncation. If a tool output shows truncated content or a syntax error after a write, immediately inspect the file rather than attempting another full-file write blindly.

### Rule 3: Strict Target Uniqueness & Context Anchoring
1. **Provide sufficient context**: When specifying `TargetContent` for search-and-replace tools, include 2–3 surrounding lines of unchanged context above and below the modification to guarantee uniqueness.
2. **Exact character matching**: Ensure whitespace, leading spaces/tabs, docstrings, and comment blocks in `TargetContent` match the disk representation byte-for-byte.
3. **Single match validation**: Before executing an edit that replaces a single instance, verify that the `TargetContent` occurs only once in the designated search range or entire file. If multiple occurrences exist, refine the context anchors or specify precise line bounds.

### Rule 4: Idempotent Failure Recovery
When an edit or patch operation fails:
1. **Do NOT blindly retry the identical tool call**: A failed replacement indicates the target string or line numbers do not match the current disk state.
2. **Execute Diagnostic Sequence**:
   - **Step A (Inspect)**: Read the surrounding 20–30 lines around the intended target area.
   - **Step B (Check if already applied)**: Determine whether a previous step or tool already applied the change (idempotency check).
   - **Step C (Recalibrate)**: Extract the exact lines directly from the fresh disk view and formulate a newly anchored replacement chunk.
3. **Fallback Strategy**: If contiguous string replacement fails twice on a file due to formatting or encoding quirks, utilize an isolated patch script, write a clean minimal helper, or rewrite only the specific function/class boundary.

### Rule 5: Post-Edit Integrity & Syntax Validation
1. **Verify disk state immediately**: After applying edits, run a lightweight validation (such as syntax compilation, linting, or checking git diff) to ensure no syntax errors, unmatched braces, duplicated functions, or unintended deletions occurred.
2. **Check boundary integrity**: Confirm that import blocks, class endings, and module-level exports remain structurally sound.

---

## 3. Anti-Patterns vs. Safe Practices

| Anti-Pattern | Risk | Safe Practice |
| :--- | :--- | :--- |
| **Blind full-file overwrite** (`write_to_file` of 500+ lines) | Truncation, token limit cutoff, lost helper functions | Surgical replacement (`replace_file_content`) with localized target lines. |
| **Editing without re-viewing** | Desync error, wrong line numbers, missed concurrent changes | View target lines immediately prior to submitting the replacement. |
| **Minimal 1-line target without context** (`target = "def foo():"`) | Matches multiple declarations or incorrect class methods | Anchor with 2–3 surrounding lines (e.g. preceding decorator, class header, or succeeding docstring). |
| **Infinite retry of failed edit** | Endless loop, context exhaustion | Read current lines on disk, identify mismatch, and update target content. |
| **Assuming edits are idempotent** | Duplicate code blocks, invalid syntax | Verify disk state and run syntax/test checks after editing. |

---

## 4. Agent Execution Checklist

Before submitting any file edit:
- [ ] Have I viewed the target file or specific line slice within the last turn?
- [ ] Is `TargetContent` uniquely identified by line bounds or surrounding context?
- [ ] Is the replacement chunk bounded to avoid truncation risks?
- [ ] Did I preserve the original indentation, whitespace, and comment structure?

After submitting any file edit:
- [ ] Did the edit tool report success?
- [ ] If failed, did I view disk lines before attempting a revised edit?
- [ ] Did I verify the syntax / git diff of the modified file?
