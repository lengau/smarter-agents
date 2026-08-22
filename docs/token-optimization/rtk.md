# RTK (Rust Token Kit)

## Overview & Purpose

RTK is a high-performance Rust binary for filtering and compressing shell output, reducing token usage by 60-90% when feeding command output to LLMs. It includes a Terminal User Interface (TUI) for interactive filtering and real-time preview of token savings.

**Key Features:**
- Rust binary for maximum performance
- Intelligent shell output filtering (removes ANSI, progress bars, duplicates)
- 60-90% token savings on typical command output
- Interactive TUI for real-time filtering
- Streaming support for large outputs
- Configurable filter rules

## Installation

```bash
# Install via cargo
cargo install rtk

# Download pre-built binary
curl -L https://github.com/rtk/rtk/releases/latest/download/rtk-x86_64-unknown-linux-gnu -o rtk
chmod +x rtk

# Homebrew (macOS)
brew install rtk

# Docker
docker pull rtk/rtk:latest
```

## Configuration

Add to your `opencode.json`:

```json
{
  "plugins": {
    "rtk": {
      "enabled": true,
      "defaultFilters": ["ansi", "progress", "duplicate", "timestamp"],
      "maxOutputTokens": 4000,
      "compression": {
        "enabled": true,
        "algorithm": "lz4",
        "dictionary": "shell-output"
      },
      "tui": {
        "enabled": true,
        "keybindings": "vim",
        "theme": "dark"
      },
      "hooks": {
        "preFilter": [],
        "postFilter": ["summarize"]
      }
    }
  }
}
```

### Standalone Config File (`~/.config/rtk/config.toml`)

```toml
[filters]
# Remove ANSI escape codes
ansi = true

# Remove progress bars and spinners
progress = true

# Remove duplicate consecutive lines
duplicate = true

# Remove timestamps from log lines
timestamp = true

# Truncate long lines
max_line_length = 200

# Keep only last N lines of repetitive output
tail_repetitive = 50

[compression]
enabled = true
algorithm = "lz4"
dictionary = "shell-output"

[output]
max_tokens = 4000
format = "text"  # text, json, markdown

[tui]
enabled = true
keybindings = "vim"
theme = "dark"
preview_lines = 20
```

## Usage Examples

### Basic Filtering

```bash
# Filter command output
rtk filter --input build.log

# Filter with custom rules
rtk filter --input build.log --filters ansi,progress,duplicate

# Filter stdin
cat build.log | rtk filter

# Save filtered output
rtk filter --input build.log --output build-filtered.log
```

### Token Counting

```bash
# Count tokens in file
rtk count --input build.log

# Count tokens in stdin
cat build.log | rtk count

# Compare before/after
rtk count --input build.log --filtered
```

### Interactive TUI

```bash
# Launch TUI for interactive filtering
rtk tui --input build.log

# TUI with live command
rtk tui --command "make build"

# TUI with saved session
rtk tui --session build-session
```

### Streaming Large Output

```bash
# Stream filter large build output
make build 2>&1 | rtk filter --stream --max-tokens 4000

# Stream to LLM directly
make test 2>&1 | rtk filter --stream | opencode ask "Analyze test failures"
```

### Summarization

```bash
# Generate summary after filtering
rtk filter --input build.log --summarize

# Custom summary prompt
rtk filter --input build.log --summarize --prompt "Extract errors and warnings only"
```

## Savings Tracking Commands

```bash
# Show savings for last run
rtk stats

# Detailed savings report
rtk stats --detailed --since 24h

# Savings by filter type
rtk stats --by-filter

# Export savings data
rtk export --format json --output rtk-savings.json

# Real-time savings in TUI
# Press 's' in TUI to toggle savings display
```

## Integration with Other Tools

### With Headroom

```bash
# Pipe through RTK then Headroom
make build 2>&1 | rtk filter --stream | headroom compress --stdin

# Or use Headroom proxy with RTK preprocessing
export RTK_PREPROCESS=1
headroom exec -- make build
```

### With context-mode

```bash
# Store filtered output in context-mode
make test 2>&1 | rtk filter | context-mode remember "test:latest" --stdin

# Recall and re-filter
context-mode recall "test:latest" | rk filter --filters ansi
```

### With OpenCode

```bash
# Use as OpenCode preprocessor
opencode run --preprocessor "rtk filter --stream"

# In opencode.json
{
  "preprocessors": ["rtk"]
}
```

### Shell Integration

```bash
# Add to .bashrc/.zshrc
alias rtk-filter='rtk filter --stream --max-tokens 4000'

# Auto-filter all command output
function rtk-wrap() {
    "$@" 2>&1 | rtk filter --stream
}

# Use with any command
rtk-wrap make build
rtk-wrap npm test
rtk-wrap docker build .
```

### CI/CD Integration

```yaml
# .github/workflows/analyze.yml
- name: Run tests with RTK filtering
  run: |
    npm test 2>&1 | rtk filter --stream --max-tokens 8000 > filtered-output.txt

- name: Analyze with LLM
  run: |
    opencode ask "Analyze test failures" < filtered-output.txt
```

### Custom Filter Rules

```rust
// Custom filter plugin (compile as dynamic library)
use rtk::filter::{Filter, FilterContext};

pub struct CustomFilter;

impl Filter for CustomFilter {
    fn name(&self) -> &str { "custom" }
    
    fn apply(&self, ctx: &FilterContext, input: &str) -> String {
        // Remove internal debug lines
        input.lines()
            .filter(|l| !l.contains("[DEBUG]"))
            .collect::<Vec<_>>()
            .join("\n")
    }
}
```

```toml
# Load custom filter
[filters.custom]
enabled = true
library = "./target/release/libcustom_filter.so"
```

## Configuration Reference

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `defaultFilters` | array | ["ansi","progress","duplicate","timestamp"] | Enabled filters by default |
| `maxOutputTokens` | integer | 4000 | Maximum output tokens |
| `compression.enabled` | boolean | true | Enable output compression |
| `compression.algorithm` | string | "lz4" | Compression algorithm |
| `compression.dictionary` | string | "shell-output" | Compression dictionary |
| `tui.enabled` | boolean | true | Enable TUI |
| `tui.keybindings` | string | "vim" | Keybinding scheme (vim, emacs) |
| `tui.theme` | string | "dark" | UI theme |
| `filters.ansi` | boolean | true | Strip ANSI codes |
| `filters.progress` | boolean | true | Remove progress bars |
| `filters.duplicate` | boolean | true | Remove duplicate lines |
| `filters.timestamp` | boolean | true | Strip timestamps |
| `filters.max_line_length` | integer | 200 | Truncate long lines |
| `filters.tail_repetitive` | integer | 50 | Keep last N repetitive lines |

## Filter Details

### ANSI Filter
Removes all ANSI escape sequences (colors, cursor movement, styling).

### Progress Filter
Detects and removes:
- Spinners (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`)
- Progress bars (`[====>    ] 45%`)
- Percentage indicators
- Download/upload progress

### Duplicate Filter
Removes consecutive identical lines, keeping first occurrence with count:
```
Original:
error: failed
error: failed
error: failed

Filtered:
error: failed (x3)
```

### Timestamp Filter
Strips common timestamp formats:
- `[2024-01-15 10:30:45]`
- `10:30:45.123`
- `2024-01-15T10:30:45Z`

## Troubleshooting

### TUI Not Starting
```bash
# Check terminal capabilities
rtk doctor

# Force text mode
rtk tui --no-tui --input build.log
```

### High Memory on Large Files
```bash
# Use streaming mode
rtk filter --stream --input huge.log

# Increase buffer size
rtk filter --input huge.log --buffer-size 100MB
```

### Insufficient Token Reduction
```bash
# Enable all filters
rtk filter --input build.log --filters all

# Add summarization
rtk filter --input build.log --summarize

# Check which filters helped
rtk stats --by-filter
```

### Custom Dictionary for Compression

```bash
# Train custom dictionary
rtk dict train --inputs *.log --output shell-dictionary.bin

# Use custom dictionary
rtk filter --input build.log --dict shell-dictionary.bin
```