# Token Optimization Tools

This directory documents three complementary tools for reducing token usage when working with LLMs. Each tool operates at a different layer and can be used independently or combined for maximum savings.

## Quick Comparison

| Feature | Headroom | context-mode | RTK |
|---------|----------|--------------|-----|
| **Type** | Local Proxy | MCP Server | CLI Binary |
| **Language** | Rust | Rust/TypeScript | Rust |
| **Primary Savings** | 30-50% (compression + caching) | 98% (semantic memory) | 60-90% (output filtering) |
| **Integration** | Transparent proxy | MCP protocol | Pipe/Stream |
| **Persistence** | Cache (TTL-based) | SQLite (permanent) | None (streaming) |
| **Interface** | HTTP Proxy + Dashboard | MCP Tools + CLI | CLI + TUI |
| **Best For** | API call optimization | Conversation memory | Command output reduction |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Your LLM Client                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │      Headroom Proxy      │  ← Compression, Caching, Cache Alignment
              │      (Port 8080)         │
              └────────────┬────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐  ┌──────────────┐  ┌─────────────┐
   │ context-mode│  │  Direct API  │  │   RTK       │
   │  MCP Server │  │  Calls       │  │  (Preprocess)│
   │ (Port 8081) │  │              │  │             │
   └──────┬──────┘  └──────────────┘  └──────┬──────┘
          │                                  │
          ▼                                  ▼
   ┌─────────────┐                    ┌─────────────┐
   │ SQLite DB   │                    │ Filtered    │
   │ (Memory)    │                    │ Output      │
   └─────────────┘                    └─────────────┘
```

## Combined Usage

### Maximum Token Savings Pipeline

```bash
# 1. Start Headroom proxy (caches & compresses API calls)
headroom start --config opencode.json &

# 2. Start context-mode MCP server (persistent memory)
context-mode serve --proxy http://localhost:8080 &

# 3. Run commands with RTK filtering (reduces output tokens)
make test 2>&1 | rtk filter --stream --max-tokens 4000 | opencode ask "Analyze results"
```

### OpenCode Configuration (All Three)

```json
{
  "plugins": {
    "headroom": { "enabled": true, "port": 8080 },
    "context-mode": { "enabled": true, "autoAttach": true },
    "rtk": { "enabled": true, "defaultFilters": ["ansi", "progress", "duplicate"] }
  },
  "mcpServers": {
    "context-mode": {
      "command": "context-mode",
      "args": ["serve", "--proxy", "http://localhost:8080"]
    }
  },
  "preprocessors": ["rtk"]
}
```

## Savings Breakdown

### Typical Scenario: Debugging a Build Failure

| Stage | Tokens | Savings |
|-------|--------|---------|
| Raw build output | 50,000 | - |
| After RTK filtering | 5,000 | **90%** |
| After Headroom compression | 3,500 | **30%** additional |
| With context-mode recall (repeat debug) | 100 | **98%** additional |

**Total: 99.8% reduction** (50,000 → 100 tokens on repeat analysis)

### Scenario: Long-Running Conversation

| Stage | Tokens | Savings |
|-------|--------|---------|
| Full conversation history | 100,000 | - |
| With context-mode semantic memory | 2,000 | **98%** |
| API calls via Headroom | 1,400 | **30%** compression |
| **Total** | **1,400** | **98.6%** |

## Tool Selection Guide

### Use Headroom When:
- Making frequent API calls to LLM providers
- Want transparent optimization (no code changes)
- Need caching for repeated prompts
- Want dashboard for monitoring usage

### Use context-mode When:
- Have long-running conversations across sessions
- Need to reference previous context without re-sending
- Want semantic search over conversation history
- Building agents with persistent memory

### Use RTK When:
- Feeding command output to LLMs
- Working with CI/CD logs, build output, test results
- Need interactive filtering (TUI)
- Want to preprocess before sending to LLM

## Installation Summary

```bash
# Install all three
cargo install headroom context-mode rtk

# Or via package managers
npm install -g @context-mode/server
brew install headroom context-mode rtk
```

## Documentation

- [Headroom Proxy](./headroom.md) - Local proxy with compression, caching, and dashboard
- [context-mode MCP Server](./context-mode.md) - Persistent semantic memory with 98% reduction
- [RTK (Rust Token Kit)](./rtk.md) - Shell output filtering with 60-90% savings and TUI

## Contributing

Each tool is developed independently. See their respective repositories for contribution guidelines:

- Headroom: https://github.com/headroom/headroom
- context-mode: https://github.com/context-mode/context-mode
- RTK: https://github.com/rtk/rtk

## License

Documentation: MIT License
Tools: See individual repositories for licenses
