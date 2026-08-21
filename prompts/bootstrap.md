# Smarter Agents: Agent Bootstrap Prompt 🤖⚡

Use this prompt to instruct any AI coding agent (e.g., **Claude Code**, **Pi Agent**, **OpenCode**, **Antigravity**, **Cursor**, **Aider**, **Windsurf**, **SWE-agent**) to automatically bootstrap, install, and adopt the **Smarter Agents** rules and skills into the current workspace.

---

## 📋 Copy-Pastable Bootstrap Prompt

Copy and send the following prompt block directly to your agent:

```markdown
Please bootstrap and install the Smarter Agents toolkit (rules and skills) into this repository:

1. **Detect Workspace & Harness:**
   - Locate the root directory of this repository / workspace.
   - Detect the active agent harness convention(s):
     * Antigravity / Agentic CLI: `.agents/rules/` and `.agents/skills/`
     * GitHub Copilot / VS Code: `.github/instructions/` and `.github/skills/`
     * OpenCode: `.opencode/instructions/` and `.opencode/skills/`
     * Pi Agent: `.pi/rules/` and `.pi/skills/`
     * Cursor / Windsurf: `.cursor/rules/` and `.cursor/skills/` (or standard `.agents/`)
     * Default / Multi-harness: Install into both `.agents/` and `.github/` for maximum agent compatibility.

2. **Download & Install Rules & Skills:**
   - Clone or download the smarter-agents toolkit repository:
     ```bash
     git clone --depth 1 https://github.com/lengau/smarter-agents.git /tmp/smarter-agents
     python3 /tmp/smarter-agents/installer.py . --copy --harness default
     rm -rf /tmp/smarter-agents
     ```
   - Alternatively, if Python is unavailable, fetch directly from `https://raw.githubusercontent.com/lengau/smarter-agents/main/` or use git submodules / symlinks.

3. **Initialize Configuration (Optional):**
   - If this project uses Copilot Collections or automated hooks, create a `.copilot-collections.yaml` in the project root containing:
     ```yaml
     collections:
       - smarter-agents-core
     ```

4. **Activate & Verify:**
   - Inspect the newly installed rules:
     * `scoped-autonomy.md`: Strict blast radius controls and scope boundaries.
     * `test-driven-verification.md`: Mandatory test verification before claiming completion.
     * `robust-file-ops.md`: Safe multi-turn file edits and whole-buffer verification.
     * `goal-anchor.md`: Structured goal tracking to prevent context drift and amnesia.
   - Read these rules into your context and adhere to them for all subsequent tasks in this project.
   - Output a brief summary table of the installed rules and skills.
```

---

## 🚀 One-Line Shell Command Alternative

If you prefer to run a shell command directly in your terminal or agent runner:

```bash
curl -fsSL https://raw.githubusercontent.com/lengau/smarter-agents/main/installer.py | python3 - . --copy
```

Or with git clone:

```bash
git clone --depth 1 https://github.com/lengau/smarter-agents.git /tmp/smarter-agents && python3 /tmp/smarter-agents/installer.py . --copy && rm -rf /tmp/smarter-agents
```

---

## 🛠️ Harness Detection Reference Table

| Agent Harness | Rules Destination | Skills Destination | Notes |
| :--- | :--- | :--- | :--- |
| **Antigravity / Google Agentic CLI** | `.agents/rules/` | `.agents/skills/` | Natively discovered by AGY / Antigravity |
| **GitHub Copilot / VS Code** | `.github/instructions/` | `.github/skills/` | Standard GitHub instructions & skills |
| **OpenCode** | `.opencode/instructions/` | `.opencode/skills/` | OpenCode agent workspace convention |
| **Pi Agent** | `.pi/rules/` | `.pi/skills/` | Pi modular rules and skills |
| **Cursor / Windsurf** | `.cursor/rules/` | `.cursor/skills/` | Also supports standard `.agents/rules/` |
| **Claude Code / Aider / Generic** | `.agents/rules/` | `.agents/skills/` | Referenced via prompt or instruction config |
