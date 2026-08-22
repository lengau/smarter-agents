---
applyTo: '**'
description: 'Code quality enables agent efficiency — clean codebase = less context = faster/cheaper agents.'
---

# Rule: Code Quality Enables Agent Efficiency

## Core Principle

**Code quality is not a speed tradeoff — it is an agent efficiency multiplier.** A clean codebase reduces the context agents need to understand, navigate, and modify code. Less context means faster execution, lower token costs, and fewer errors.

---

## Enforced Practices

### 1. Small Files

- **Target**: Files under 300 lines; functions under 50 lines.
- **Why**: Agents load entire files. Large files force agents to parse irrelevant code, increasing tokens and cognitive load.
- **Action**: Split files at natural boundaries. Extract modules for distinct responsibilities.

### 2. Clear Boundaries

- **Target**: Explicit interfaces, minimal coupling, single-responsibility modules.
- **Why**: Agents can reason about one component without loading its dependencies.
- **Action**: Use dependency inversion. Define contracts at module boundaries. Avoid circular imports.

### 3. Descriptive Names

- **Target**: Self-documenting symbols — variables, functions, classes, modules.
- **Why**: Agents (and humans) infer intent from names. Cryptic names require reading implementation.
- **Action**: `calculateTax` not `calc`. `UserRepository` not `Repo`. Avoid abbreviations.

### 4. Behavioral Tests

- **Target**: Tests verify *behavior*, not implementation. Test public APIs, not private methods.
- **Why**: Behavioral tests serve as executable specifications. Agents understand *what* code does without reading *how*.
- **Action**: Write tests first (TDD). Cover edge cases. Name tests descriptively: `shouldRejectNegativeAmounts`.

---

## TDD as Agent Self-Assessment Loop

**Test-Driven Development is the primary self-assessment mechanism for agents.**

1. **Red**: Write a failing test that defines expected behavior.
2. **Green**: Implement minimal code to pass.
3. **Refactor**: Clean up with confidence — tests catch regressions.
4. **Repeat**: Each cycle validates understanding before adding complexity.

Agents that skip TDD accumulate silent bugs. Agents that TDD continuously verify their own work.

---

## References

- **scoped-autonomy**: Modify only what's necessary — clean boundaries make this possible.
- **test-driven-verification**: TDD as the verification backbone.
- **robust-file-ops**: Safe file operations preserve code quality during edits.

---

## Summary

| Practice | Agent Impact |
|----------|--------------|
| Small files | Less context to load |
| Clear boundaries | Independent reasoning per module |
| Descriptive names | Less implementation reading |
| Behavioral tests | Executable specs, safe refactoring |
| TDD loop | Continuous self-verification |

**Invest in code quality. It pays compound interest in agent efficiency.**
