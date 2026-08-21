# Rule: Scoped Autonomy (Prevent Scope Creep & Collateral Damage)

## Core Directive
Agents must maintain strict scope containment. Edits, refactorings, and file operations must be restricted exclusively to what is directly required to fulfill the user's explicit objective. Do not make opportunistic "cleanups", speculative refactorings, unsolicited formatting overhauls, or stripped docstrings.

---

## 1. Scope Containment Boundaries

### Permitted Modifications
- **Targeted Code Elements**: Only modify functions, classes, configuration entries, or documentation specifically identified in the task or strictly necessary to satisfy the requirements.
- **Direct Dependencies**: Edits to related files or call sites are permitted only if strictly necessary for contract compatibility, import resolution, or test fulfillment.
- **New Code**: Add new functions, files, or tests only when directly supporting the requested functionality or required verification.

### Prohibited Actions (Collateral Damage)
- **NO Speculative Refactoring**: Never refactor unrelated methods, clean up technical debt, or modernize idioms outside the active task scope.
- **NO Unprompted Reformatting**: Do not reformat entire files, alter whitespace conventions, adjust indentation, or reorganize imports across untouched sections.
- **NO Stripping Comments or Docstrings**: Preserve all existing comments, docstrings, type annotations, licenses, and documentation unless specifically instructed to update or delete them.
- **NO Dependency Creep**: Do not introduce new external dependencies or library requirements unless explicitly requested or approved.

---

## 2. The Diff Budget Mindset

Always approach code modifications with a **diff budget**:
1. **Minimal Surface Area**: Seek the solution that yields the cleanest, smallest diff while fully satisfying quality and correctness requirements.
2. **Atomic Changes**: Keep edits focused and logically isolated. Prefer targeted line replacements over full-file rewrites.
3. **No Unrelated Touches**: Every added, modified, or deleted line in `git diff` must have a clear justification directly tied to the primary goal.

---

## 3. Preservation Rules

1. **Comments and Context**:
   - Preserve inline explanations, architectural notes, and TODOs in surrounding code.
   - If an edit touches an area with an existing docstring or comment, update it for accuracy—never remove it without cause.
2. **Project Conventions**:
   - Match existing coding style, naming conventions, line length, and syntax patterns found in the immediate file and project.
3. **Configuration & Tooling**:
   - Do not modify project configs (linter settings, build tools, CI/CD workflows, formatters) unless explicitly instructed.

---

## 4. Self-Audit & Accounting Protocol

Before declaring any task or phase complete, perform a mandatory diff audit:

1. **Review Diff**: Run `git diff` (or inspect staged changes) across all modified files.
2. **Account for Every Chunk**:
   - *Why is this line modified?*
   - *Is this change required for the user's objective?*
   - *Did I accidentally delete comments or reformat untouched blocks?*
3. **Revert Spurious Changes**: Immediately revert any unintentional edits, whitespace shifts, or unrelated refactorings before testing and committing.
4. **Log Changes Clearly**: Provide concise commit messages and summaries that accurately reflect the scoped work without obscuring the intent.
