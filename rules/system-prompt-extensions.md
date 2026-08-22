---
applyTo: '**'
description: 'Additional system‑prompt directives not yet captured in the repository rules.'
---

# Rule: System Prompt Extensions (Missing Directives)

## 2. Workspace‑Rule Precedence

- **Check Workspace Rules First**: If the repository contains `.github/instructions`, `.github/rules`, or `.agents/rules/` files, they **override** all built‑in defaults. These workspace‑specific directives must be obeyed before any other rule.

## 3. No Polling or Busy‑Wait Loops

- **Never Use `sleep` or Infinite Loops**: Do not write scripts that poll or busy‑wait. Use the `schedule` tool (one‑shot timers or cron) to wait for events. The system will automatically wake the agent when the timer fires.

## 4. No Global PATH Modifications

- **Do Not Alter the System PATH** or install packages globally unless the user explicitly asks for it. All dependencies must be installed in a temporary virtual environment or via the project's lockfile.

## 5. No Raw `cd` in Commands

- **All Terminal Commands Must Specify a Working Directory** via the tool's `Cwd` argument or use absolute paths. Never rely on `cd` to change state between commands.

## 6. MCP Schema First

- **Read MCP Tool Schemas Before Invoking**: For any lazy‑loaded MCP tool, read its `<tool>.json` schema file to understand required arguments, types, and constraints. Do not guess parameter names.

## 7. Skill‑Documentation‑First

- **Read a Skill’s `SKILL.md` Before Using It**. Never assume a skill’s interface; always open and review its instruction file prior to execution.

## 8. Artifact‑Only Large Outputs

- **Never Embed Large Code Diffs, Tables, or Logs Directly in Chat**. For extensive information, generate a persistent Markdown artifact and reference it.

## 9. Search‑Tool‑Only

- **Never Use Raw `grep`, `find`, or `ls` in Bash**. Use the native `grep_search`, `list_dir`, or `find_by_name` tools instead.

## 10. File‑Operation‑Only via Native Tools

- **Never Use Raw File‑Manipulation Commands (`cat`, `sed`, `awk`, `echo >`)**. Use the built‑in `write_to_file`, `replace_file_content`, or `view_file` tools for all file edits.

## 11. No Background Sleep Waiting

- **If Waiting Is Required, Use `schedule`**. The system will not poll; a scheduled timer will wake the agent when the time elapses.

## 12. Mandatory Symbol Linking

- **Always Use Clickable `file://` Links** for any referenced file, class, function, or line range. Plain text paths are not allowed.

## 13. Secret‑Output‑Protection

- **Redact Secrets in Tool Output**: If any tool returns data that appears to be a credential (tokens, keys, passwords), replace it with `[REDACTED]` before sending it to the user.

## 14. No Auto‑Merge

- **Never Auto‑Merge or Directly Commit to Main**. All changes must be pushed to a feature branch and opened as a pull request for review.

## 15. Workspace‑Boundary for Writes

- **Write Only Inside the Designated Workspace** (`/home/lengau/Projects/AI/smarter-agents`). Do not create source files or configuration files outside this directory unless the user explicitly requests it. Use the artifact `scratch/` folder for temporary scripts.
