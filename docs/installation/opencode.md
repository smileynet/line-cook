# Installing Line Cook for OpenCode

## Install

```bash
git clone https://github.com/smileynet/line-cook.git ~/line-cook
cd ~/line-cook/plugins/opencode && ./install.sh
```

## Update

```bash
cd ~/line-cook && git pull && ./plugins/opencode/install.sh
```

## Verify

After installing, run:

```
/line-help
```

You should see a list of available Line Cook commands.

## Troubleshooting

**install.sh fails:**
- Ensure the script is executable: `chmod +x plugins/opencode/install.sh`
- Check that OpenCode's agent config directory exists

## Next Steps

1. Install [beads](https://github.com/steveyegge/beads): `brew install beads`
2. Initialize beads in your project: `bd init`
3. Follow [Getting Started](../getting-started.md)
