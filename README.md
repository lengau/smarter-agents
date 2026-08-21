# Smarter Agents 🧠⚡

A standardized, modular library of **Rules** (`.agents/rules`, `.github/instructions`) and **Skills** (`.agents/skills`, `.github/skills`) built to eliminate common failure modes in modern coding agents (such as **Pi**, **OpenCode**, **SWE-agents**, **Antigravity**, and **Copilot**).

Licensed under [Apache 2.0](LICENSE).

---

## 🤖 Quick Install for Any Agent

Paste this prompt into your agent to install Smarter Agents globally:

```markdown
Install Smarter Agents rules and skills globally for yourself:
1. Clone `https://github.com/lengau/smarter-agents.git` (e.g. to `~/.smarter-agents` or `~/.gemini/`).
2. Symlink or copy the `rules/` and `skills/` into your global agent configuration directory (e.g., `~/.gemini/config/skills/`, `~/.agents/`, `~/.config/opencode/`, `~/.pi/`, or your harness's global instructions/skills path).
3. Confirm installation and list the active rules and skills.
```

---

## 🎯 Problems Solved

| Problem | Root Cause | Solution |
| :--- | :--- | :--- |
| **Context Amnesia & Drift** | Multi-turn compaction strips goals | `rules/goal-anchor.md` & `skills/context-checkpoint` |
| **Sloppy Engineering** | Declares tasks done without testing | `rules/test-driven-verification.md` |
| **Scope Overreach** | Eager refactors & stripping comments | `rules/scoped-autonomy.md` & `skills/diff-auditor` |
| **Brittle File Edits** | Stale buffers & chunk truncation | `rules/robust-file-ops.md` & `skills/patch-repair` |

---

## 📁 Repository Structure

```
.
├── LICENSE                     # Apache 2.0 License
├── README.md                   # Overview & installation
├── collections.yaml            # Copilot collections manifest
├── installer.py                # Universal CLI installer for projects & harnesses
│
├── rules/                      # Behavioral guardrails and reasoning instructions
│   ├── basic-directives.md
│   ├── scoped-autonomy.md
│   ├── test-driven-verification.md
│   ├── robust-file-ops.md
│   └── goal-anchor.md
│
└── skills/                     # Executable workflows and verification tools
    ├── diff-auditor/           # Git diff boundary & AST sanity auditor
    ├── patch-repair/           # Robust fuzzy matching for failed file edits
    └── context-checkpoint/     # Structured memory snapshot across long sessions
```
