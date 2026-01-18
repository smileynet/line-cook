# Testing Guide

**For Developers Only.** End-users should install via plugin commands in README.md.

Methods to test line-cook commands and plugins during development.

## Claude Code

### Load Plugin Locally

```bash
# Test plugin from local directory
claude --plugin-dir ~/line-cook

# Verify plugin loaded
# In Claude Code REPL, commands should be available as:
# /line:prep, /line:cook, /line:serve, /line:tidy
```

### Test Individual Commands

```bash
# Run command in non-interactive mode
echo "/line:prep" | claude --plugin-dir ~/line-cook

# Or use print mode for quick testing
claude -p "Run /line:prep and summarize the output" --plugin-dir ~/line-cook
```

### Verify Plugin Structure

```bash
# Check plugin.json is valid JSON
cat .claude-plugin/plugin.json | jq .

# List all commands
ls -1 commands/*.md

# Verify frontmatter in commands
for f in commands/*.md; do
  echo "=== $f ==="
  head -10 "$f"
done
```

## OpenCode

### Install Commands

```bash
# Use the install script
./line-cook-opencode/install.sh

# Or manually copy
cp line-cook-opencode/commands/*.md ~/.config/opencode/commands/
```

### Verify Installation

```bash
# Check commands exist
ls ~/.config/opencode/commands/line-*.md

# Verify frontmatter
head -5 ~/.config/opencode/commands/line-prep.md
```

### Test Commands

```bash
# Start OpenCode and run command
opencode
# Then type: /line-prep

# Or use non-interactive mode (if supported)
echo "/line-prep" | opencode
```

## Common Validation

### Frontmatter Validation

```bash
# Check YAML frontmatter is valid
for f in commands/*.md; do
  echo "Checking $f..."
  # Extract frontmatter (between --- markers)
  sed -n '/^---$/,/^---$/p' "$f" | grep -v "^---$" | python3 -c "import sys, yaml; yaml.safe_load(sys.stdin)" && echo "  ✓ Valid" || echo "  ✗ Invalid"
done
```

### Template Variable Check

```bash
# Find template variables in commands
grep -h '\$ARGUMENTS\|\$[0-9]' commands/*.md line-cook-opencode/commands/*.md
```

### Beads Integration Test

```bash
# Ensure beads commands work
bd ready
bd list --status=open
bd sync --status
```

## CI/CD Testing

### GitHub Actions Example

```yaml
name: Test Plugins
on: [push, pull_request]

jobs:
  test-claude-code:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate plugin.json
        run: cat .claude-plugin/plugin.json | jq .
      - name: Validate command frontmatter
        run: |
          for f in commands/*.md; do
            sed -n '/^---$/,/^---$/p' "$f" | grep -v "^---$" | python3 -c "import sys, yaml; yaml.safe_load(sys.stdin)"
          done

  test-opencode:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run install script
        run: ./line-cook-opencode/install.sh
      - name: Verify installation
        run: ls ~/.config/opencode/commands/line-*.md
```

## Troubleshooting

### Command Not Found

1. Verify plugin directory is correct
2. Check plugin.json has the command listed
3. Ensure command file exists and has valid frontmatter

### Frontmatter Issues

- Description must be on single line (no wrapping)
- YAML must be valid (check colons, quotes)
- Use `---` markers exactly

### Permission Errors

- Claude Code: Check `allowed-tools` syntax
- OpenCode: Commands don't restrict tools
