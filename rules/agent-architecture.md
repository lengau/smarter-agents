---
applyTo: '**'
description: 'Asynchronous event-driven execution, subagent delegation, and task management.'
---

# Rule: Asynchronous Architecture & Task Management

## 1. Reactive Wakeup (No Polling)

Agents running in modern asynchronous environments receive messages and event triggers automatically.

- **Never Poll**: Never run background `sleep` commands, infinite loops, or busy-wait polling scripts to wait for tasks,
  server readiness, or CI jobs.
- **Halt and Await**: After launching a background command or spawning a subagent, simply proceed with other work or
  halt execution (stop calling tools). The system will automatically wake you up when a task completes or an event
  occurs.

## 2. Subagent Delegation

- **Parallelize Independent Tasks**: Delegate broad research tasks, isolated bug fixes, or long-running CI verification
  to specialized subagents.
- **Isolated Workspaces**: When spawning subagents to modify code, explicitly place them in isolated branched workspaces
  to prevent state collisions with the parent agent.
- **Clear Intent**: Pass down invariant goals and non-negotiable constraints to subagents explicitly.

## 3. Ephemeral Scratch Space

- **Temporary Files**: Write scratch scripts, debug probes, or one-off data files to the designated artifact scratch
  directory (or `/tmp`) rather than cluttering the user's project workspace.
- **Workspace Boundaries**: Do not write source code or configuration files outside the designated project boundaries
  unless explicitly requested.
