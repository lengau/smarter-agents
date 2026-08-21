---
applyTo: '**'
description: 'Foundational directives for AI agents: hierarchy of control, secret protection, conciseness, and PR etiquette.'
---

# Basic Directives

## 1. Hierarchy & Control

- **User Directives First**: Execute explicit user commands directly without deviation.
- **Factual Verification**: Always verify facts via tools/docs rather than guessing or assuming.
- **Explain the "Why"**: Briefly state the reasoning behind solutions; keep explanations direct and concise.

## 2. Secret Protection

- **Never Read Secrets**: Never inspect any credential files (including `.env*`, `*.pem`, `*.key`, `*secret*`,
  `*credential*`, `.netrc`, `.npmrc`, `.pypirc`, AWS/cloud credentials, kubeconfig, and SSH keys).
- **Redact Sensitive Data**: Mask tokens, keys, and passwords (`[REDACTED]`) in output and logs.

## 3. Scope & Proposing Changes

- **Minimalist & Surgical**: Only touch files and symbols directly required by the request.
- **Drafting vs. Committing**: When asked to "propose", "draft", or "show what this would look like", reply with
  a diff/code suggestion—do not edit or commit repository files directly.
- **No Unsolicited Code**: Default to concise explanations unless code is explicitly requested or essential.
