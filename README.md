# Smarter Agents 🧠⚡

A standardized, modular library of **Rules** (`.agents/rules`, `.github/instructions`) and **Skills** (`.agents/skills`, `.github/skills`) built to eliminate the most common failure modes in modern coding agents (such as **Pi**, **OpenCode**, **SWE-agents**, **Antigravity**, and **Copilot**).

Licensed under [Apache 2.0](LICENSE).

---

## 🎯 Problems Solved

| Problem | Root Cause | Provided Solution |
| :--- | :--- | :--- |
| **Context Amnesia & Drift** | Multi-turn compaction strips goals | `rules/goal-anchor.md` & `skills/context-checkpoint` |
| **Sloppy Engineering** | Declares tasks done without testing | `rules/test-driven-verification.md` & `skills/verify-and-lint` |
| **Scope Overreach** | Eager refactors & stripping comments | `rules/scoped-autonomy.md` & `skills/diff-auditor` |
| **Brittle File Edits** | Stale buffers & chunk truncation | `rules/robust-file-ops.md` & `skills/patch-repair` |

---

## 🚀 Quick Start: Add to Any Project

You can install all rules and skills into any repository or agent workspace using an AI prompt, the included `installer.py`, or Copilot Collections.

### Option 1: Copy-Pastable Agent Bootstrap Prompt 🤖

Paste this prompt directly into your agent's chat window (e.g. **Claude Code**, **Pi**, **OpenCode**, **Antigravity**, **Cursor**, **Aider**):

```markdown
Please bootstrap and install the Smarter Agents toolkit (rules and skills) into this repository:
1. Detect active agent harness conventions (.agents/, .github/, .opencode/, .pi/, or .cursor/).
2. Run: git clone --depth 1 https://github.com/lengau/smarter-agents.git /tmp/smarter-agents && python3 /tmp/smarter-agents/installer.py . --copy --harness default && rm -rf /tmp/smarter-agents
3. Read the installed rules in .agents/rules/ or .github/instructions/ into context and apply them.
```
*(For detailed bootstrap options and harness customization, see [prompts/bootstrap.md](prompts/bootstrap.md) or [BOOTSTRAP.md](BOOTSTRAP.md)).*

### Option 2: Automatic CLI Installer

Clone this repository and run the installer targeting your project:

```bash
git clone https://github.com/lengau/smarter-agents.git
cd smarter-agents

# Install into your project (creates symlinks into .agents and .github)
python3 installer.py /path/to/your/project

# Or copy files directly instead of symlinks
python3 installer.py /path/to/your/project --copy

# Target specific agent harness formats (e.g. opencode, pi, antigravity, cursor)
python3 installer.py /path/to/your/project --harness opencode
```

### Option 3: Copilot Collections Sync

If your agent harness or workspace uses automatic Copilot Collections sync (e.g. Antigravity PreInvocation hooks or GitHub Copilot Actions), simply add a `.copilot-collections.yaml` in your project root:

```yaml
collections:
  - smarter-agents-core
```

---

## 📁 Repository Structure

```
.
├── LICENSE                     # Apache 2.0 License
├── PLAN.md                     # Roadmap and architectural design
├── BOOTSTRAP.md                # Quick agent bootstrap instructions
├── collections.yaml            # Collections manifest for automated sync tools
├── installer.py                # Universal CLI installer for projects & harnesses
│
├── prompts/                    # Ready-to-use agent prompts & instructions
│   └── bootstrap.md            # Complete agent bootstrap prompt & harness matrix
│
├── rules/                      # Behavioral guardrails and reasoning instructions
│   ├── scoped-autonomy.md
│   ├── test-driven-verification.md
│   ├── robust-file-ops.md
│   └── goal-anchor.md
│
└── skills/                     # Executable workflows and verification tools
    ├── verify-and-lint/        # Polyglot test runner with low-token failure traces
    ├── diff-auditor/           # Git diff boundary & AST sanity auditor
    ├── patch-repair/           # Robust fuzzy matching for failed file edits
    └── context-checkpoint/     # Structured memory snapshot across long sessions
```

---

## 🛠️ Supported Agent Harnesses

- **Antigravity / Google Agentic CLI**: `.agents/rules/` & `.agents/skills/`
- **GitHub Copilot / Workspace Agents**: `.github/instructions/` & `.github/skills/`
- **OpenCode**: `.opencode/instructions/` & `.opencode/skills/`
- **Pi Agent**: `.pi/rules/` & `.pi/skills/`
- **Cursor / Custom Harnesses**: `.cursor/rules/` or standard markdown references

---

## 🤝 Contributing

Issues, suggestions, and additions are welcome! Please check out the [Issue Tracker](https://github.com/lengau/smarter-agents/issues).
