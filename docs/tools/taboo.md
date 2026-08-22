# Taboo: AI Agent Orchestration in Workshop Sandboxes

## Overview

**Taboo** is a Go library for orchestrating AI agents within Workshop sandboxes. Built during the AI Engineering course (AFK Loops module) as part of learning Go and exploring Workshop (Madrid Engineering Sprint), taboo enables running automated workflows with AI agents that can execute code, make changes, and land commits directly onto repository branches.

### Key Features

- **Workshop Sandbox Integration**: Runs AI agents in isolated Workshop sandbox environments
- **Automated Commits**: Agents can create commits and push directly to repository branches
- **AFK Loop Pattern**: Implements the "Away From Keyboard" loop for autonomous agent execution
- **Go Native**: Built in Go for performance and concurrency

---

## Installation

```bash
# If published as a Go module
go get github.com/<org>/taboo

# Or build from source
git clone https://github.com/<org>/taboo
cd taboo
go build
```

> **Note**: Replace `<org>` with the actual GitHub organization once the repository is public.

---

## Usage

### Basic Example

```go
package main

import (
    "context"
    "fmt"
    "github.com/<org>/taboo"
)

func main() {
    ctx := context.Background()

    // Configure the sandbox
    config := taboo.Config{
        Repository: "github.com/user/repo",
        Branch:     "feature/agent-task",
        Sandbox:    taboo.SandboxConfig{Image: "workshop-base:latest"},
    }

    // Create orchestrator
    orchestrator, err := taboo.NewOrchestrator(ctx, config)
    if err != nil {
        panic(err)
    }
    defer orchestrator.Close()

    // Define agent workflow
    workflow := taboo.Workflow{
        Name: "code-review",
        Steps: []taboo.Step{
            {Name: "analyze", Agent: "analyzer", Prompt: "Review PR #123 for security issues"},
            {Name: "fix", Agent: "fixer", Prompt: "Apply fixes for issues found"},
            {Name: "test", Agent: "tester", Prompt: "Run tests and verify fixes"},
        },
    }

    // Execute workflow
    result, err := orchestrator.Run(ctx, workflow)
    if err != nil {
        panic(err)
    }

    fmt.Printf("Workflow completed: %v commits landed\n", result.CommitsLanded)
}
```

### Configuration

```go
type Config struct {
    Repository string          // Git repository URL
    Branch     string          // Target branch for commits
    Sandbox    SandboxConfig   // Sandbox configuration
    Agents     []AgentConfig   // Agent definitions
    Git        GitConfig       // Git credentials and settings
}

type SandboxConfig struct {
    Image       string            // Docker image for sandbox
    Resources   ResourceLimits    // CPU/Memory limits
    EnvVars     map[string]string // Environment variables
    MountPaths  []string          // Host paths to mount
}

type AgentConfig struct {
    Name        string
    Model       string            // LLM model to use
    SystemPrompt string           // Base system prompt
    Tools       []string          // Allowed tools
    MaxTurns    int               // Maximum conversation turns
}
```

---

## Integration with Workshop

Taboo is designed to work natively with **Workshop** sandboxes, providing:

### Sandbox Lifecycle Management

```go
// Workshop automatically provisions sandboxes
sandbox, err := workshop.CreateSandbox(ctx, workshop.SandboxSpec{
    Image: "taboo-agent:latest",
    Repo:  "github.com/user/repo",
    Branch: "feature/branch",
})
```

### Git Operations in Sandbox

```go
// Agents can perform git operations within the sandbox
gitOps := taboo.NewGitOperations(sandbox)

// Create commit
commit, err := gitOps.Commit(ctx, taboo.CommitOptions{
    Message: "fix: resolve security issue in auth module",
    Files:   []string{"auth/auth.go", "auth/auth_test.go"},
})

// Push to remote
err = gitOps.Push(ctx, taboo.PushOptions{
    Remote: "origin",
    Branch: "feature/agent-task",
})
```

### Workshop API Integration

```go
// Monitor sandbox status
status, err := workshop.GetSandboxStatus(ctx, sandbox.ID)

// Stream logs from agent execution
logStream, err := workshop.StreamLogs(ctx, sandbox.ID)
for entry := range logStream {
    fmt.Printf("[%s] %s\n", entry.Timestamp, entry.Message)
}
```

---

## AFK Loop Pattern

The **AFK (Away From Keyboard) Loop** is the core execution pattern that enables agents to run autonomously for extended periods.

### Pattern Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      AFK LOOP                               │
├─────────────────────────────────────────────────────────────┤
│  1. INITIALIZE: Provision sandbox, clone repo, setup env   │
│                         │                                   │
│                         ▼                                   │
│  2. PLAN: Agent analyzes task, creates execution plan      │
│                         │                                   │
│                         ▼                                   │
│  3. EXECUTE: Run steps (code, test, lint, commit)          │
│                         │                                   │
│                         ▼                                   │
│  4. VERIFY: Run tests, checks, validation                  │
│                         │                                   │
│         ┌─────────────┴─────────────┐                       │
│         ▼                           ▼                       │
│    SUCCESS                      FAILURE                     │
│         │                           │                       │
│         ▼                           ▼                       │
│  5. COMMIT & PUSH           RETRY / ESCALATE                │
│         │                           │                       │
│         └─────────────┬─────────────┘                       │
│                       ▼                                     │
│  6. CHECKPOINT: Save state, update context                 │
│                       │                                     │
│                       ▼                                     │
│  7. CONTINUE OR COMPLETE (max iterations reached?)         │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

```go
type AFKLoop struct {
    orchestrator *Orchestrator
    maxIterations int
    checkpointInterval time.Duration
}

func (a *AFKLoop) Run(ctx context.Context, task Task) (*Result, error) {
    for i := 0; i < a.maxIterations; i++ {
        // Checkpoint state
        if i > 0 && i%a.checkpointInterval == 0 {
            a.saveCheckpoint(ctx)
        }

        // Execute iteration
        result, err := a.orchestrator.ExecuteIteration(ctx, task)
        if err != nil {
            // Handle failure with retry logic
            if a.shouldRetry(err) {
                continue
            }
            return nil, err
        }

        // Verify results
        if a.verify(result) {
            // Commit and push changes
            if err := a.commitAndPush(ctx, result); err != nil {
                return nil, err
            }
            return result, nil
        }

        // Update task context for next iteration
        task = a.updateContext(task, result)
    }

    return nil, ErrMaxIterationsReached
}
```

### Checkpointing

```go
type Checkpoint struct {
    Iteration    int
    GitState     GitSnapshot
    AgentContext map[string]string
    Timestamp    time.Time
}

func (a *AFKLoop) saveCheckpoint(ctx context.Context) error {
    cp := Checkpoint{
        Iteration:    a.currentIteration,
        GitState:     a.orchestrator.GetGitSnapshot(),
        AgentContext: a.orchestrator.GetAgentContext(),
        Timestamp:    time.Now(),
    }
    return a.checkpointStore.Save(ctx, cp)
}
```

---

## Comparison with Similar Tools

| Feature | Taboo | Sandcastle | Claude Code (Docker) |
|---------|-------|------------|---------------------|
| **Language** | Go | Python/TypeScript | TypeScript |
| **Sandbox** | Workshop | Custom/Docker | Docker |
| **Git Integration** | Native commits to branches | Manual | Via CLI |
| **AFK Loop** | Built-in pattern | Manual implementation | Limited |
| **Agent Orchestration** | Multi-agent workflows | Single agent focus | Single agent |
| **Checkpointing** | Automatic | Manual | Session-based |
| **Workshop Native** | ✅ Yes | ❌ No | ❌ No |
| **Open Source** | Planned | ✅ Yes | ❌ No (proprietary) |

### When to Use Taboo

- **Choose Taboo when**: Building autonomous AI agent workflows that need to run in Workshop sandboxes with native git integration
- **Choose Sandcastle when**: Need a more general-purpose sandboxing solution with broader language support
- **Choose Claude Code (Docker) when**: Want a ready-to-use CLI tool for interactive coding sessions

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        TABOO ARCHITECTURE                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   CLI /     │───▶│ Orchestrator│───▶│  Workshop   │     │
│  │   API       │    │   (Go)      │    │   Client    │     │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘     │
│                            │                    │            │
│                   ┌────────┴────────┐          │            │
│                   ▼                 ▼          ▼            │
│            ┌─────────────┐   ┌─────────────┐ ┌─────────┐   │
│            │  Agent Pool │   │ Git Manager │ │Sandbox  │   │
│            │ (Analyzers, │   │ (Commit,    │ │ Manager │   │
│            │  Fixers,    │   │  Push, PR)  │ │         │   │
│            │  Testers)   │   └─────────────┘ └─────────┘   │
│            └─────────────┘                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Orchestrator** - Coordinates workflow execution, manages sandbox lifecycle
2. **Agent Pool** - Manages different agent types (analyzer, fixer, tester, etc.)
3. **Git Manager** - Handles all git operations within sandboxes
4. **Sandbox Manager** - Interfaces with Workshop API for sandbox provisioning
5. **Checkpoint Store** - Persists execution state for recovery

---

## Links & Resources

- **Repository**: Private/internal (built during AI Engineering course - AFK Loops module)
- **Workshop Documentation**: Internal Workshop platform docs
- **AFK Loops Module**: Course materials from AI Engineering program
- **Madrid Engineering Sprint**: Internal engineering event where taboo was developed (learning Go + exploring Workshop)

> **Note**: Taboo is not currently open source. This documentation describes the library as it exists internally. If/when published, links will be updated.

---

## Contributing

Taboo is currently in development. Once open-sourced, contributions will be welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `go test ./...`
5. Submit a pull request

---

## License

MIT License - see LICENSE file for details.
