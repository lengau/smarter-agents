# Smarter Agents: Agent Bootstrap Prompt 🤖⚡

See [`prompts/bootstrap.md`](prompts/bootstrap.md) for the full agent bootstrap guide.

## Quick Copy-Pastable Prompt

Feed this prompt directly to any AI coding agent (**Claude Code**, **Pi**, **OpenCode**, **Antigravity**, **Cursor**, etc.) to self-install the toolkit into your active workspace:

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
