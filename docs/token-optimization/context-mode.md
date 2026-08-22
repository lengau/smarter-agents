# context-mode

## Overview & Purpose

context-mode is an MCP (Model Context Protocol) server that provides sandboxed execution environments for LLMs. It achieves up to 98% token reduction by maintaining persistent SQLite memory across sessions, allowing models to reference previous context without re-sending full conversation history.

**Key Features:**
- MCP server interface for seamless integration
- Sandboxed execution environments
- Persistent SQLite memory with semantic indexing
- 98% token reduction for repeated context
- Session isolation and security

## Installation

```bash
# Install via npm
npm install -g @context-mode/server

# Or via cargo
cargo install context-mode

# Docker
docker pull contextmode/server:latest
```

## Configuration

Add to your `opencode.json`:

```json
{
  "mcpServers": {
    "context-mode": {
      "command": "context-mode",
      "args": ["serve"],
      "env": {
        "CONTEXT_MODE_DB": "./data/context-mode.db",
        "CONTEXT_MODE_SANDBOX": "true",
        "CONTEXT_MODE_MAX_TOKENS": "100000",
        "CONTEXT_MODE_COMPRESSION": "semantic",
        "CONTEXT_MODE_TTL": "30d"
      }
    }
  },
  "plugins": {
    "context-mode": {
      "enabled": true,
      "autoAttach": true,
      "memory": {
        "persist": true,
        "indexing": "semantic",
        "maxEntries": 10000
      },
      "sandbox": {
        "enabled": true,
        "timeout": "30s",
        "memoryLimit": "256MB"
      }
    }
  }
}
```

## Usage Examples

### Basic MCP Server

```bash
# Start the MCP server
context-mode serve --db ./data/context.db

# Connect via MCP client
# The server exposes tools: remember, recall, search, execute
```

### With OpenCode

```bash
# OpenCode automatically detects and connects to context-mode MCP server
opencode run --mcp context-mode
```

### Manual Memory Operations

```bash
# Store context
context-mode remember "project:auth" "User authentication uses JWT with RS256"

# Recall context
context-mode recall "project:auth"

# Semantic search
context-mode search "JWT authentication"

# Execute in sandbox
context-mode execute --code "python3 -c 'print(2+2)'"
```

### Session Management

```bash
# List sessions
context-mode sessions list

# Create named session
context-mode session create "feature-auth"

# Switch session
context-mode session use "feature-auth"

# Export session memory
context-mode session export "feature-auth" --output auth-memory.json
```

## Savings Tracking Commands

```bash
# View token savings
context-mode stats --since 24h

# Memory efficiency report
context-mode stats --memory-efficiency

# Session-specific savings
context-mode stats --session "feature-auth"

# Export savings data
context-mode export --format json --output savings.json
```

## Integration with Other Tools

### With Headroom

```json
{
  "mcpServers": {
    "context-mode": {
      "command": "context-mode",
      "args": ["serve", "--proxy", "http://localhost:8080"]
    }
  }
}
```

### With RTK

```bash
# Use RTK to filter output before storing in context-mode
rtk filter --input build.log | context-mode remember "build:latest" --stdin
```

### Custom MCP Client

```python
from mcp import Client

client = Client("context-mode")

# Store large context once
await client.call("remember", {
    "key": "api-docs",
    "value": large_api_documentation
})

# Recall in future sessions - minimal tokens
result = await client.call("recall", {"key": "api-docs"})
```

### With CI/CD

```yaml
# .github/workflows/context-mode.yml
- name: Store build context
  run: |
    context-mode remember "build:${{ github.sha }}" "$(cat build-output.txt)"

- name: Recall for PR analysis
  run: |
    context-mode recall "build:${{ github.sha }}" > previous-build.txt
```

## Configuration Reference

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `CONTEXT_MODE_DB` | string | "./context.db" | SQLite database path |
| `CONTEXT_MODE_SANDBOX` | boolean | true | Enable sandboxed execution |
| `CONTEXT_MODE_MAX_TOKENS` | integer | 100000 | Max tokens per context entry |
| `CONTEXT_MODE_COMPRESSION` | string | "semantic" | Compression type (semantic, none) |
| `CONTEXT_MODE_TTL` | string | "30d" | Entry time-to-live |
| `memory.persist` | boolean | true | Persist memory across sessions |
| `memory.indexing` | string | "semantic" | Indexing strategy |
| `memory.maxEntries` | integer | 10000 | Maximum memory entries |
| `sandbox.enabled` | boolean | true | Enable sandbox |
| `sandbox.timeout` | string | "30s" | Execution timeout |
| `sandbox.memoryLimit` | string | "256MB" | Sandbox memory limit |

## Troubleshooting

### Database Locked
```bash
# Check for stale processes
context-mode doctor

# Force unlock
context-mode db unlock
```

### High Memory Usage
```bash
# Reduce max entries
context-mode config set memory.maxEntries 5000

# Enable aggressive compression
context-mode config set CONTEXT_MODE_COMPRESSION semantic
```

### Slow Recall
```bash
# Rebuild search index
context-mode index rebuild

# Check index stats
context-mode index stats
```

## Semantic Compression Details

context-mode uses semantic compression to achieve 98% reduction:

1. **Entity Extraction** - Identifies key entities, functions, variables
2. **Relationship Mapping** - Maps relationships between entities
3. **Summary Generation** - Creates compressed semantic summaries
4. **Index Storage** - Stores in SQLite with FTS5 for fast retrieval

Example:
```
Original (5000 tokens): Full API documentation with examples
Compressed (100 tokens): "AuthAPI: POST /login (JWT), GET /user, POST /refresh. Errors: 401, 403, 429. Rate: 100/min"
```