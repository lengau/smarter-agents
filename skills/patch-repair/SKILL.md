---
name: patch-repair
description: Resilient strategies to diagnose and recover from failed string-replacement edits without file corruption.
---

# Patch Repair: Resilient & AST-Aware File Editing Strategy

A robust operational skill for coding agents to gracefully diagnose, triangulate, and recover from failed file edit
and string-replacement operations (`replace_file_content`, unified diff patches, or regex substitutions).

---

## 🛑 Why File Patches Fail

Coding agents frequently encounter patch and replacement failures due to subtle environmental differences between model
generation context and actual disk state:

1. **Whitespace & Indentation Shifts**: Target code in model memory uses 2 spaces, while disk uses 4 spaces or tabs;
   trailing whitespace differences; CRLF vs. LF line endings.
2. **Line Offset Drift**: Earlier file modifications shifted line numbering, causing bounded range lookups (`StartLine` /
   `EndLine`) to search the wrong window.
3. **Stale Buffer Syndrome**: The agent attempts to replace text based on outdated context rather than current on-disk
   state.
4. **Non-Unique Target Snippets**: The target snippet matches multiple locations across the file, causing tool aborts.
5. **Partial Patch Corruption**: A failed or partial edit leaves syntax in a broken state, preventing subsequent targeted
   edits.

---

## 🛠️ The 5-Step Patch Recovery Playbook

When an edit tool returns `TargetContent not found`, `multiple occurrences found`, or fails to apply a patch:

```
[Edit Fails]
     │
     ▼
[Step 1: Re-Read Fresh Buffer] ──► Inspect exact on-disk lines & offsets
     │
     ▼
[Step 2: Triangulate Anchor Lines] ──► Find unique syntax anchors (def, class, imports)
     │
     ▼
[Step 3: Normalize Indentation] ──► Match target file's tab/space indentation
     │
     ▼
[Step 4: Elevate AST Granularity] ──► If fine-grained edit fails, replace entire AST block
     │
     ▼
[Step 5: Apply & Validate Syntax] ──► Run language syntax check / linter
     │
    ├──► [Syntax OK] ──► Proceed with verification tests
    └──► [Syntax Error] ──► Restore pre-edit backup & retry with AST replacement
```

---

### Step 1: Re-Read Fresh Buffer (Zero Assumptions)

**Never retry a failed patch blindly with the same target string.**

- Inspect the actual current contents around the expected line range using `view_file` (or `sed -n 'X,Yp'`).
- Check whether earlier edits succeeded or modified surrounding lines.
- Verify line numbers and exact line breaks.

### Step 2: Triangulate Unique Anchor Lines

Locate unambiguous semantic boundaries that are guaranteed to be unique in the file:

```python
# ❌ WEAK TARGET (Ambiguous, matches multiple places in file):
    return result

# ✅ STRONG ANCHOR (Triangulated by signature and context):
def process_user_permissions(user_id: str, roles: list[str]) -> bool:
    if not roles:
        return False
    return result
```

- Include the enclosing function/method signature, class definition, or unique variable assignment as anchor lines.
- Look 3–5 lines above and below the modification site to create a distinctive pattern.

### Step 3: Normalize Indentation & Whitespace

Mismatch between 2-space, 4-space, or tab indentation is the primary cause of string-matching failure.

1. Measure the exact leading indentation on disk for the surrounding block.
2. Re-indent the replacement payload to match disk indentation exactly.
3. Ensure line endings (LF vs CRLF) match the source file.

### Step 4: Elevate Granularity to Enclosing AST Construct

If surgical, fine-grained replacement inside a function or statement block repeatedly fails:

- **Do not attempt complex multi-line regex surgery.**
- **Elevate granularity**: Replace the entire enclosing function, method, or class block from opening signature to
  closing line.
- Full AST block replacement eliminates internal line offset and indentation mismatches within the block.

### Step 5: Post-Patch Syntax & AST Validation

Always validate the syntactic integrity of the modified file immediately after editing:

| Language | Syntax Check Command |
| :--- | :--- |
| **Python** | `python3 -m py_compile <file>` |
| **JavaScript / Node** | `node --check <file>` |
| **TypeScript** | `npx --no-install tsc --noEmit` |
| **JSON** | `python3 -m json.tool <file> > /dev/null` |
| **YAML** | `python3 -c "import yaml; yaml.safe_load(open('<file>'))"` |
| **Go** | `go vet <file>` |
| **Rust** | `cargo check` |

> [!CAUTION]
> If a syntax check fails, **immediately restore** the pre-edit content or target file backup before attempting another
> edit. Preserving unrelated uncommitted changes ensures clean, non-destructive rollbacks. Never leave a file in a
> corrupt, unparseable state.

---

## 📋 Common Failure Scenarios & Solutions

### Scenario A: TargetContent Has Whitespace Differences

- **Symptoms**: `TargetContent not found in file`, but code looks identical visually.
- **Remedy**: Re-read disk lines with `view_file` to capture exact indentation and line breaks, then reapply.

### Scenario B: TargetContent Occurs Multiple Times

- **Symptoms**: `Tool error: Multiple occurrences found`.
- **Remedy**: Expand `StartLine` / `EndLine` search window, or include surrounding unique context (parent function
  definition and docstring).

### Scenario C: File Partially Corrupted by Truncated Write

- **Symptoms**: Unexpected EOF or syntax error after tool invocation.
- **Remedy**: Restore pre-edit backup or run targeted restore for the damaged file, then re-apply using full-block
  replacement.

---

## ⚡ Quick Reference Checklist

- [ ] Re-read fresh file content before retrying a failed edit.
- [ ] Triangulate using unique enclosing anchors (function/class headers).
- [ ] Re-indent payload to match disk indentation precisely.
- [ ] If surgical replacement fails, replace the full enclosing AST block.
- [ ] Run language-specific syntax validation (`py_compile`, `node --check`, etc.).
- [ ] Verify clean `git diff` before proceeding to test execution.
