# Contributing to Smarter Agents

Thank you for contributing! This document covers workflow and branch protection.

## Pull Request Workflow

### CI Checks on PR Update

When a pull request or merge request is updated, the CI workflow must run and all required status checks must pass before merge.

**Requirements:**

1. Any push, rebase, or force-push to a PR triggers CI jobs (lint, test, etc.).
2. Branch protection requires relevant status checks (`lint`, `test` if applicable) to pass before merging.
3. Contributors must fix CI failures and push new commits; CI re-runs automatically.

**Rationale:** Validates changes against linting, testing, and security policies, preventing regressions.

**Implementation:**

- Add branch-protection rule requiring status checks `lint` (and `test`) to pass.
- Document rule here (migrated from former `rules/pr-ci-update.md` which was repository policy, not agent behavior).

## General Guidelines

1. Fork repository, create feature branch (`git checkout -b feat/my-change`).
2. Make changes, run `make lint` and relevant tests.
3. Push branch and open pull request for review. Never directly commit to `main` or use auto-merge.
