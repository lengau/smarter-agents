---
applyTo: '**'
description: 'Aggressive context window management — quality degrades past ~120k tokens; cost grows quadratically; skills consume context at load time.'
---

# Rule: Context Paranoia

## Core Problem

**Context is a liability, not an asset.** Treat every token entering the conversation as a cost that compounds.

| Threshold | Effect |
|-----------|--------|
| **~120k tokens** | Optimal quality window |
| **120k–500k** | Silent quality degradation |
| **500k+** | Significant errors, hallucinations |
| **Quadratic growth** | Message N repeats messages 1..N-1 |

---

## Root Causes

1. **Quality Degradation**: Best output from first ~120k tokens. Past that, quality drops while nothing visibly fails.
2. **Cost Growth**: Total input over a session grows with the square of turns. A 40-message session "repeats" messages 1–39.
3. **Error Compounding**: LLMs re-reading their own errors get biased to repeat them.
4. **Skill Overload**: Every skill's header loads at session start. Bigger skills = more context. `disable-model-invocation: true` prevents auto-loading.

---

## Mandatory Techniques

### 1. Ask, Then Rewind
> For quick answers: prompt → get answer → **rewind conversation to before the prompt**.
> - Answer stays in your head
> - Question + answer tokens removed from history

### 2. Handoff Documents for Long Work
> For extended tasks: request a **handoff document** → open fresh session → let it go deep → return with finished spec.
> - Resets history each subagent re-sends
> - Use `handoff` skill (see skills-playground)

### 3. Longer Prompts Upfront
> One 500-token prompt spelling constraints, answer shape, and ruled-out options **costs less** than 6 clarification rounds (thousands of tokens + context pollution).

### 4. Subagents for Mechanical Work
> Spawn subagents for exploration, file operations, test runs.
> - Each subagent: isolated history, fresh context
> - Several small sessions cheaper than one large
> - Parent synthesizes; subagent history discarded

### 5. Progressive Disclosure in Agent Docs
> **Show basic options first. Hide advanced details behind references.**
> - Ask: "Is this useful for EVERY session?"
> - If no: extract to smaller doc + add reference link
> - Reference link << full skill contents in context

### 6. Disable Model Invocation for Skills
```yaml
disable-model-invocation: true
```
> Prevents harness from loading skill into initial session context.
> Use when: skill won't be auto-invoked, or shouldn't be.

---

## Skill Design Guidelines

| Pattern | Token Cost | Use When |
|---------|------------|----------|
| Full skill in context | High (1–5k) | Always needed, auto-invoked |
| `disable-model-invocation: true` | Zero (header only) | Manual invocation only |
| Reference link to external doc | Minimal | Rarely needed, progressive disclosure |
| Handoff skill | Zero (separate session) | Long-running, multi-phase |

---

## Token-Saving Stack (Compounding)

1. **RTK** — Filters shell output FIRST (60–90% savings)
2. **context-mode** — Keeps analysis in sandbox (98% reduction)
3. **Headroom** — Compresses what enters prompt (2–3% + cache alignment)
4. **Headroom `--memory`** — Cross-agent memory (avoids re-explanation)

---

## References

- **goal-anchor**: Anchor primary goal; re-anchor on drift
- **agent-architecture**: Subagent delegation resets history
- **tool-selection**: Native tools over shell waste
- **communication-formatting**: Artifacts over chat clutter

---

## Summary

| Technique | Savings | Effort |
|-----------|---------|--------|
| Ask → rewind | High for quick Q&A | Low |
| Handoff docs | High for long tasks | Medium |
| Longer prompts | High vs clarification | Low |
| Subagents | High for mechanical work | Medium |
| Progressive disclosure | High for skill docs | Medium |
| Disable model invocation | High for unused skills | Low |
| Token-saving stack | Compounding 60%+ | Setup once |

**Be paranoid. Every token costs.**

(End of file - total 73 lines)
