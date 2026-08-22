# Headroom

## Overview & Purpose

Headroom is a local proxy that sits between your LLM client and the API provider. It compresses requests and responses, aligns cache keys for better hit rates, manages memory efficiently, and provides a dashboard for monitoring token usage and savings.

**Key Features:**
- Request/response compression
- Cache key alignment for improved hit rates
- Memory management with configurable limits
- Real-time dashboard for token tracking
- Transparent proxy - no code changes required

## Installation

```bash
# Install via cargo
cargo install headroom

# Or download binary from releases
curl -L https://github.com/headroom/headroom/releases/latest/download/headroom-linux-x64 -o headroom
chmod +x headroom
```

## Configuration

Add to your `opencode.json`:

```json
{
  "plugins": {
    "headroom": {
      "enabled": true,
      "port": 8080,
      "compression": {
        "enabled": true,
        "algorithm": "zstd",
        "level": 3
      },
      "cache": {
        "enabled": true,
        "keyAlignment": true,
        "maxSize": "1GB",
        "ttl": "24h"
      },
      "memory": {
        "maxHeap": "512MB",
        "gcInterval": "5m"
      },
      "dashboard": {
        "enabled": true,
        "port": 9090
      }
    }
  }
}
```

## Usage Examples

### Basic Proxy Setup

```bash
# Start headroom proxy
headroom start --config opencode.json

# Configure your client to use the proxy
export OPENAI_BASE_URL=http://localhost:8080/v1
export ANTHROPIC_BASE_URL=http://localhost:8080
```

### With OpenCode

```bash
# Run opencode with headroom proxy
headroom exec -- opencode run
```

### Dashboard Access

```bash
# Open dashboard in browser
open http://localhost:9090

# Or view metrics via CLI
headroom metrics --format json
```

## Savings Tracking Commands

```bash
# View token savings summary
headroom stats --since 24h

# Detailed breakdown by model
headroom stats --by-model --since 7d

# Export metrics for analysis
headroom export --format csv --output savings.csv

# Real-time monitoring
headroom monitor --interval 10s
```

## Integration with Other Tools

### With context-mode

```json
{
  "plugins": {
    "headroom": { "enabled": true, "port": 8080 },
    "context-mode": { "enabled: true, "proxy": "http://localhost:8080" }
  }
}
```

### With RTK

```bash
# Pipe RTK output through headroom
rtk filter --input large-output.txt | headroom compress --stdin
```

### With Custom Clients

```python
import openai

client = openai.OpenAI(base_url="http://localhost:8080/v1", api_key="your-key")

# All requests automatically compressed and cached
response = client.chat.completions.create(...)
```

## Configuration Reference

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `port` | integer | 8080 | Proxy listening port |
| `compression.enabled` | boolean | true | Enable request/response compression |
| `compression.algorithm` | string | "zstd" | Compression algorithm (zstd, gzip, brotli) |
| `compression.level` | integer | 3 | Compression level (1-9) |
| `cache.enabled` | boolean | true | Enable response caching |
| `cache.keyAlignment` | boolean | true | Align cache keys for better hits |
| `cache.maxSize` | string | "1GB" | Maximum cache size |
| `cache.ttl` | string | "24h" | Cache entry TTL |
| `memory.maxHeap` | string | "512MB" | Maximum heap memory |
| `memory.gcInterval` | string | "5m" | Garbage collection interval |
| `dashboard.enabled` | boolean | true | Enable metrics dashboard |
| `dashboard.port` | integer | 9090 | Dashboard port |

## Troubleshooting

### High Memory Usage
```bash
# Reduce cache size
headroom config set cache.maxSize 500MB

# Increase GC frequency
headroom config set memory.gcInterval 1m
```

### Low Cache Hit Rate
```bash
# Enable key alignment
headroom config set cache.keyAlignment true

# Check alignment effectiveness
headroom stats --cache-alignment
```

### Connection Issues
```bash
# Verify proxy is running
headroom health

# Check logs
headroom logs --level debug
```
