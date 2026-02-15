# Installing Line Cook for Kiro

## Install

```bash
git clone https://github.com/smileynet/line-cook.git ~/line-cook
python3 ~/line-cook/plugins/kiro/install.py
```

## Update

```bash
cd ~/line-cook && git pull && python3 plugins/kiro/install.py
```

## Verify

After installing, run:

```
@line-help
```

You should see a list of available Line Cook commands.

## Troubleshooting

**Python not found:**
- Kiro install requires Python 3. Use `python3` explicitly.

**Permissions issue:**
- Check that Kiro's agent config directory is writable.

See [Kiro Troubleshooting](../dev/kiro-troubleshooting.md) for more Kiro-specific issues.

## Next Steps

1. Install [beads](https://github.com/steveyegge/beads): `brew install beads`
2. Initialize beads in your project: `bd init`
3. Follow [Getting Started](../getting-started.md)
