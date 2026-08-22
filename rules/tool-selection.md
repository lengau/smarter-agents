---
applyTo: '**'
description: 'Tool selection strictness: prioritizing specialized native tools over brittle shell commands.'
---

# Rule: Tool Selection Strictness & Safety

## 1. Prioritize Native Tools over Terminal Commands

Autonomous coding agents often default to constructing complex, brittle bash pipelines when specialized native tools are
available. Always prioritize the most specific tool for the task at hand.

- **No Raw File Operations in Bash**: Never use `cat`, `echo >`, `sed`, or `awk` via terminal commands to create,
  append, or modify files. Always use the provided native file system tools (e.g., `write_to_file`,
  `replace_file_content`, `read_file`).
- **No Raw Search Commands**: Never use `grep`, `find`, or `ls` in the terminal for standard searches or directory
  listings. Always use native equivalents like `grep_search`, `list_dir`, or `find_by_name`.
- **No Path Mutations**: Never use `cd` in terminal commands. All terminal commands must specify the execution directory
  via the tool's built-in `Cwd` or `cwd` argument, and all file operations must use absolute paths.

## 2. Tool Abort & Fallback

- If a specialized tool fails, diagnose the failure using native read tools before falling back to a shell workaround.
- Maintain environment purity: Do not install global dependencies or modify the system PATH unless explicitly requested.

## 3. Skill & Schema Discovery

- **Read Before You Act**: Before using any skill, read its `SKILL.md` instructions first. Never assume you know a
  skill's interface from its name alone.
- **MCP Tool Schema Discovery**: Before calling any unfamiliar or lazy-loaded MCP tool, read its JSON schema file to
  understand the tool's arguments, types, and constraints. Never guess parameter names or formats.
- **Workspace Rule Discovery**: At the start of a task, check for `.agents/rules/` and `.agents/skills/` directories
  in the workspace. Adhere to any style guides, coding standards, or directives found there.
