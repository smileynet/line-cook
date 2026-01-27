# Kiro Plugin Troubleshooting

Developer reference for Kiro CLI integration issues.

## Installation Options

```bash
# Global install (default) - installs to ~/.kiro/
python3 line-cook-kiro/install.py

# Local install - installs to .kiro/ in current directory
python3 line-cook-kiro/install.py --local
```

## Common Issues

### Agent config malformed error

**Symptom:**
```
WARNING Agent config line-cook is malformed at /resources/3: "skill://~/.kiro/skills/**/SKILL.md" is not valid
```

**Cause:** Old global install uses tilde (`~`) paths. Kiro's `skill://` URI scheme doesn't expand tilde.

**Fix:** Reinstall globally:
```bash
python3 line-cook-kiro/install.py --global
```

The installer now uses absolute paths (e.g., `/home/user/.kiro/...`) instead of tilde paths.

### Local vs Global Priority

Kiro loads agents from `~/.kiro/agents/` (global) by default. If you have both global and local installs, the global one takes precedence when using `--agent line-cook`.

To use a local install:
1. Remove the global agent: `rm ~/.kiro/agents/line-cook.json`
2. Or don't specify `--agent` and let Kiro auto-detect from `.kiro/`

### Prompts Not Found

**Symptom:** `@line-prep` doesn't work or shows "prompt not found".

**Cause:** Prompts weren't installed or installed to wrong location.

**Fix:** Verify prompts exist:
```bash
ls ~/.kiro/prompts/line-*.md   # Global
ls .kiro/prompts/line-*.md     # Local
```

Reinstall if missing:
```bash
python3 line-cook-kiro/install.py
```

## CLI Flags Reference

```bash
kiro-cli chat -a -r --agent line-cook
```

| Flag | Long | Description |
|------|------|-------------|
| `-a` | `--auto-accept` | Auto-accept tool calls (less confirmation prompts) |
| `-r` | `--resume` | Resume previous session if available |
| | `--agent <name>` | Use specified agent configuration |

## Path Handling in Agent Config

The `install.py` script transforms paths based on install type:

| Install Type | Path Format | Example |
|--------------|-------------|---------|
| Local | Relative | `file://.kiro/steering/...` |
| Global | Absolute | `file:///home/user/.kiro/steering/...` |

**Why absolute paths for global?** The `skill://` URI scheme doesn't expand `~` (tilde). Using full absolute paths avoids validation errors.

## Relevant Files

- `line-cook-kiro/install.py` - Installation script with path transformation logic
- `line-cook-kiro/agents/line-cook.json` - Source agent configuration
- `~/.kiro/agents/line-cook.json` - Installed global agent config
- `.kiro/agents/line-cook.json` - Installed local agent config
