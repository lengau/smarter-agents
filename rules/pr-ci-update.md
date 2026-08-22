---
applyTo: '**'
description: 'Mandatory CI execution on PR updates - all status checks must pass before merge'
---

# CI Check on PR Update

## Rule

When a pull request or merge request is updated, the CI workflow must be executed, and all required status checks must pass before the PR can be merged.

## Requirements

1. Any push, rebase, or force-push to a PR triggers the CI jobs (lint, test, etc.).
2. Repository branch protection must require the relevant status checks to pass before merging.
3. Contributors must address any CI failures and push new commits; CI will automatically re-run.

## Rationale

Ensures that all changes are validated against linting, testing, and security policies, preventing regressions from being merged.

## Implementation Guidance

- Add a branch-protection rule in the repository settings requiring the status checks `lint` (and `test` if applicable) to pass.
- Document this rule in the project's `RULES.md` or similar documentation.
