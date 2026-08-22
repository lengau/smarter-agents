---
name: configure-repo-for-agents
description: Interactive setup wizard for configuring repositories with reusable skill collections across agent harnesses (Copilot, OpenCode, Cursor, Claude Code, Generic).
argument-hint: [--target <dir>] [--harness <type>] [--collection <name>] [--non-interactive]
---

# Configure Repository for Agents 🛠️

The `configure-repo-for-agents` skill provides an interactive wizard to audit a repository's current agent configuration, recommend appropriate skill collections based on the detected harness, install selected collections using the toolkit installer, and generate harness-specific configuration files.

---

## 🎯 When to Use This Skill

Activate or run `configure-repo-for-agents` when:
1. **Onboarding a new repository** — No existing agent configuration present.
2. **Switching or adding harnesses** — Need to generate config for Copilot, OpenCode, Cursor, etc.
3. **Upgrading collections** — Want to add new skill collections (e.g., `skills-playground`, `copilot-collections`).
4. **Validating setup** — Verify lint passes and test invocation works after configuration.

---

## 🔍 Repository Audit & Harness Detection

The wizard automatically detects existing agent harness configurations:

| Harness | Detection Signal | Config Target |
|---------|------------------|---------------|
| **GitHub Copilot** | `.github/copilot-instructions.md`, `.github/instructions/` | `.copilot-collections.yaml` |
| **OpenCode** | `.opencode/`, `opencode.json` | `opencode.json`, `.opencode/skills/`, `.opencode/instructions/` |
| **Cursor** | `.cursor/rules/`, `.cursor/mcp.json` | `.cursor/rules/`, `.cursor/mcp.json` |
| **Claude Code** | `.claude/`, `CLAUDE.md` | `.claude/skills/`, `.claude/commands/` |
| **Generic / Antigravity** | `.agents/`, `.agents/rules/`, `.agents/skills/` | `.agents/rules/`, `.agents/skills/` |

---

## 📦 Recommended Collections per Harness

### Core Collections (Available in Toolkit)

| Collection | Description | Rules | Skills |
|------------|-------------|-------|--------|
| `smarter-agents-core` | Full suite of foundational rules and verification skills | 10 | 3 |
| `rules-only` | Only directive rules for agent reasoning and safety | 10 | 0 |
| `skills-only` | Operational skills without strict behavioral rules | 0 | 3 |

### Canonical Collections (External, to Research & Add)

| Collection | Source | Target Harnesses | Notes |
|------------|--------|------------------|-------|
| `copilot-collections` | `canonical/copilot-collections` | Copilot, Generic | Community-maintained Copilot instruction packs |
| `skills-playground` | `canonical/skills-playground` | All | Experimental skills for various workflows |
| `awesome-copilot` | `github/awesome-copilot` | Copilot | Curated list of Copilot resources |
| `vscode-copilot-skills` | `microsoft/vscode-copilot-skills` | Copilot, Cursor | Official VS Code Copilot skills |
| `claude-code-skills` | `anthropics/claude-code-skills` | Claude Code | Official Claude Code skills |
| `opencode-skills` | `opencode-ai/skills` | OpenCode | Official OpenCode skills |
| `cursor-rules` | `cursor/cursor-rules` | Cursor | Official Cursor rules |

> **Note**: External collections are installed via the installer using their repository URLs. The wizard will prompt to clone and link them.

---

## ⚙️ Automated Configuration Script

This skill includes an interactive CLI wizard: [`skills/configure-repo-for-agents/scripts/configure_repo.py`](scripts/configure_repo.py).

### Quick Commands

```bash
# 1. Interactive wizard (recommended for first-time setup)
python3 skills/configure-repo-for-agents/scripts/configure_repo.py

# 2. Non-interactive: configure for specific harness with default collection
python3 skills/configure-repo-for-agents/scripts/configure_repo.py --target . --harness copilot --collection smarter-agents-core --non-interactive

# 3. Non-interactive: configure for all harnesses with core collection
python3 skills/configure-repo-for-agents/scripts/configure_repo.py --target . --harness all --collection smarter-agents-core --non-interactive

# 4. Audit only (detect harness, show recommendations, no changes)
python3 skills/configure-repo-for-agents/scripts/configure_repo.py --target . --audit-only

# 5. Validate existing setup (lint skills, test invocation)
python3 skills/configure-repo-for-agents/scripts/configure_repo.py --target . --validate
```

---

## 📋 Wizard Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. REPOSITORY AUDIT                                         │
│    ├── Scan for existing harness configs                    │
│    ├── Detect: Copilot, OpenCode, Cursor, Claude, Generic  │
│    └── Report: Found configs, missing configs               │
├─────────────────────────────────────────────────────────────┤
│ 2. HARNESS SELECTION                                        │
│    ├── List detected + available harnesses                  │
│    ├── User selects target harness(es)                      │
│    └── Default: all detected + generic                      │
├─────────────────────────────────────────────────────────────┤
│ 3. COLLECTION RECOMMENDATION                                │
│    ├── Per harness: recommend core + canonical collections  │
│    ├── Show: smarter-agents-core, copilot-collections, etc. │
│    └── User selects collections to install                  │
├─────────────────────────────────────────────────────────────┤
│ 4. INSTALLATION (via installer.py)                          │
│    ├── Symlink or copy rules/skills to harness paths        │
│    ├── Install external canonical collections               │
│    └── Generate harness-specific config files               │
├─────────────────────────────────────────────────────────────┤
│ 5. CONFIG GENERATION                                        │
│    ├── Copilot: .copilot-collections.yaml                   │
│    ├── OpenCode: opencode.json + .opencode/skills/          │
│    ├── Cursor: .cursor/mcp.json + .cursor/rules/            │
│    ├── Claude Code: .claude/settings.json + .claude/skills/ │
│    └── Generic: .agents/rules/ + .agents/skills/            │
├─────────────────────────────────────────────────────────────┤
│ 6. VALIDATION                                               │
│    ├── Lint skill files (yamllint, markdownlint)            │
│    ├── Test skill invocation (dry-run)                      │
│    └── Verify installer symlinks resolve correctly          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Generated Config Files

### Copilot (`.copilot-collections.yaml`)
```yaml
# Copilot Collections / Smarter Agents Configuration
collections:
  - smarter-agents-core
  - copilot-collections
```

### OpenCode (`opencode.json`)
```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": [".opencode/skills/*"],
  "instructions": [".opencode/instructions/*"]
}
```

### Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "smarter-agents": {
      "command": "python3",
      "args": ["-m", "skills.mcp_server"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Generic / Antigravity (`.agents/`)
```
.agents/
├── rules/     → symlinks to toolkit rules/
└── skills/    → symlinks to toolkit skills/
```

---

## ✅ Validation Steps

After configuration, the wizard runs:

1. **YAML Lint**: `yamllint .copilot-collections.yaml` (if exists)
2. **Markdown Lint**: `markdownlint .github/instructions/*.md .opencode/instructions/*.md`
3. **JSON Schema**: Validate `opencode.json` against OpenCode schema
4. **Skill Invocation Test**: Dry-run each skill's main script with `--help`
5. **Symlink Check**: Verify all symlinks resolve to valid toolkit paths

---

## 📂 Bundled Resources

- **Wizard Script**: [`scripts/configure_repo.py`](scripts/configure_repo.py)
- **Config Templates**: [`templates/`](templates/)
  - `copilot-collections.template.yaml`
  - `opencode.template.json`
  - `cursor-mcp.template.json`
  - `claude-settings.template.json`
  - `agents-structure.template.yaml`

---

## 🔗 Related Skills

- **diff-auditor**: Run after configuration to verify clean diffs before committing generated configs.
- **patch-repair**: Use if config file edits fail during wizard execution.
- **context-checkpoint**: Checkpoint wizard state for resumption across sessions.

---

## 📝 Example Session

```bash
$ python3 skills/configure-repo-for-agents/scripts/configure_repo.py

=== Repository Agent Configuration Wizard ===
Target: /home/user/my-project

[1/6] AUDIT: Scanning repository...
  ✓ Found: .github/instructions/ (Copilot)
  ✓ Found: .opencode/ (OpenCode)
  ✗ Not found: .cursor/
  ✗ Not found: .claude/
  ✗ Not found: .agents/

[2/6] HARNESS SELECTION:
  Detected: Copilot, OpenCode
  Available: Copilot, OpenCode, Cursor, Claude Code, Generic
  Select harnesses to configure [Copilot,OpenCode,Generic]: Copilot,OpenCode,Cursor

[3/6] COLLECTION SELECTION:
  For Copilot:  smarter-agents-core, copilot-collections
  For OpenCode: smarter-agents-core, opencode-skills
  For Cursor:   smarter-agents-core, cursor-rules
  Select collections [all]: all

[4/6] INSTALLATION:
  Installing smarter-agents-core into .github/instructions/, .github/skills/...
  Installing smarter-agents-core into .opencode/instructions/, .opencode/skills/...
  Installing smarter-agents-core into .cursor/rules/...
  Cloning canonical/copilot-collections...
  Cloning canonical/skills-playground...

[5/6] CONFIG GENERATION:
  Created .copilot-collections.yaml
  Created opencode.json
  Created .cursor/mcp.json

[6/6] VALIDATION:
  ✓ yamllint .copilot-collections.yaml
  ✓ markdownlint .github/instructions/*.md
  ✓ json schema validation: opencode.json
  ✓ Skill dry-run: diff-auditor, patch-repair, context-checkpoint
  ✓ Symlinks valid

✓ Configuration complete!
```