# Rule: Scoped Autonomy (Prevent Scope Creep & Collateral Damage)

## Core Directive
Operate with surgical precision. Modify **only** the files, functions, and lines of code strictly required to fulfill the user's explicit request or resolve the specified issue. Do not touch unrelated code.

---

## 1. Scope Boundaries & Prohibitions

### 🚫 Forbidden Behaviors
1. **No "Boy Scout" or Opportunistic Refactoring**: Never rewrite, modernize, or restructure functions, classes, or files outside the direct blast radius of the assigned task, even if the surrounding code appears suboptimal.
2. **No Docstring or Comment Stripping**: Never delete existing comments, docstrings, licensing headers, or TODOs unless they are directly invalidated by your changes or explicitly requested by the user.
3. **No Unsolicited Reformatting or Lint Fixes**: Do not run whole-file formatters or linter fixes that modify untouched lines or files. Only format the specific lines you create or modify.
4. **No Speculative Feature Creep or Premature Optimization**: Implement only what was requested. Do not add speculative "future-proofing", unprompted helper utilities, or extra abstraction layers.
5. **No Gratuitous Dependency or Config Changes**: Do not add new third-party packages, update package versions, or modify configuration files unless explicitly required to solve the task.

---

## 2. The "Diff Budget" Mindset

Treat every added, modified, or deleted line of code as an expenditure of a strict "diff budget":
- **Minimal Footprint**: What is the smallest, cleanest change that completely and robustly satisfies the user request?
- **Locality of Change**: Keep changes as local as possible to the affected component.
- **Traceability**: Every line in your diff must directly trace back to a specific requirement in the prompt.

---

## 3. Surgical Editing Protocol

Follow this workflow when modifying code:

1. **Identify Target Symbols**: Determine the exact functions, classes, or config keys that need modification before making any edits.
2. **Preserve Surrounding Context**: Match the existing style, conventions, naming patterns, and error-handling paradigms of the surrounding file.
3. **Audit the Diff**: Before marking any task complete, review the exact diff (`git diff` or review tool output) line by line.
4. **Self-Accounting Question**:
   > *"If the user asks why this specific line was changed, can I justify it as strictly necessary for their request?"*
   - If **yes**: Keep the change.
   - If **no**: Revert the change immediately.

---

## 4. When Out-of-Scope Changes Appear Necessary

If solving the issue genuinely exposes a critical bug, security flaw, or blocking architecture limitation in untouched code:
1. **Do not unilaterally fix it** if it expands the scope of the task.
2. **Highlight the discovery** clearly in your final response or proactively ask the user before expanding scope.
3. Keep the current PR or patch focused solely on the primary objective.

---

## 5. Examples

### ❌ Non-Compliant (Scope Creep & Collateral Damage)
- User asks: *"Fix the off-by-one error in `calculate_tax()`."*
- Agent modifies:
  - Fixes `calculate_tax()`
  - Replaces all `var` with `let`/`const` throughout `tax.js`
  - Deletes all JSDoc comments
  - Renames `TaxHelper` class to `TaxService`

### ✅ Compliant (Scoped Autonomy)
- User asks: *"Fix the off-by-one error in `calculate_tax()`."*
- Agent modifies:
  - Changes `i <= max` to `i < max` in `calculate_tax()`
  - Adds a unit test verifying the boundary condition
  - Leaves all other functions, formatting, and docstrings intact
