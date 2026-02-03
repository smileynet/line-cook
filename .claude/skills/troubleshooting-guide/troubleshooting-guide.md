---
name: troubleshooting-guide
description: Patterns for writing effective troubleshooting documentation. Use when adding troubleshooting sections to commands, features, or tools.
---

# Troubleshooting Documentation Guide

Best practices for writing troubleshooting documentation that helps users diagnose and resolve issues quickly.

## When to Use

- Adding troubleshooting sections to command documentation
- Documenting known issues and their fixes
- Creating runbooks for operations
- Writing FAQ sections that focus on problems

## Quick Reference

### Level 1: Quick Scan Table

For 90% of users who need a fast answer:

```markdown
### Quick Scan

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| "Error X" message | Stale config | `rm -f config.cache` |
| Command hangs | Lock held | `kill -9 $(cat pid)` |
| Output is empty | No input data | Check `data/` directory |
```

### Level 2: Symptom/Cause/Fix Blocks

For users who need more context:

```markdown
**Symptom:** Command reports "cannot connect" but network is fine.

**Cause:** DNS cache contains stale entries from previous environment.

**Fix:**
\`\`\`bash
sudo systemd-resolve --flush-caches
\`\`\`
```

### Level 3: Diagnostic Procedure

For complex issues requiring investigation:

```markdown
### Diagnosing Connection Failures

1. **Check the symptom** - What error message or behavior do you see?
   \`\`\`bash
   cat /var/log/app.log | tail -20
   \`\`\`

2. **Form a hypothesis** - Based on the error, what's the likely cause?
   - If "timeout" → network or server issue
   - If "auth failed" → credentials issue
   - If "not found" → configuration issue

3. **Test the hypothesis**
   \`\`\`bash
   # For network issues:
   ping server.example.com
   curl -v https://server.example.com/health
   \`\`\`

4. **Confirm and fix** - Apply the appropriate remedy based on findings.
```

### Level 4: Developer Debug Reference

For contributors or deep debugging:

```markdown
### Developer Debug

Source: `src/connection.py:142` - `_establish_connection()`

The connection timeout is controlled by `CONNECTION_TIMEOUT_MS` in `config.py`.
Default is 30000ms. For debugging, enable verbose logging:

\`\`\`python
import logging
logging.getLogger('connection').setLevel(logging.DEBUG)
\`\`\`
```

## Topics

### Progressive Disclosure

Layer information by user need. Most users stop at Level 1.

| Level | Format | Who Stops Here | Content |
|-------|--------|----------------|---------|
| 1 | Quick Scan table | 90% of users | Symptom → Fix mapping |
| 2 | Expanded blocks | When quick fix fails | Full Symptom/Cause/Fix |
| 3 | Diagnostic procedure | Complex issues | Step-by-step investigation |
| 4 | Developer debug | Contributors only | Source code links, internals |

**Key insight:** Most users search for their symptom, find the quick fix, and leave. Don't make them read through explanations to find the fix.

### Symptom-Based Organization

Users search by what they see, not by technical cause.

**BAD - organized by cause:**
```markdown
## DNS Issues
- Stale cache causes "cannot connect"
- Missing records cause "host not found"

## Authentication Issues
- Expired token causes "401 Unauthorized"
```

**GOOD - organized by symptom:**
```markdown
## "Cannot connect" error
Cause: Stale DNS cache
Fix: `systemd-resolve --flush-caches`

## "401 Unauthorized" error
Cause: Expired auth token
Fix: `./refresh-token.sh`
```

### Decision Trees

For issues with multiple possible causes, use a decision tree:

```markdown
Command fails unexpectedly
├── Check exit code: `echo $?`
│   ├── Exit 1 → See "General errors" section
│   ├── Exit 2 → See "Missing arguments" section
│   └── Exit 137 → Process killed (OOM or signal)
│       ├── Check dmesg: `dmesg | tail -20`
│       │   ├── "Out of memory" → Increase memory limit
│       │   └── No OOM message → Killed by user/system
└── No exit (hangs)
    ├── Check if process exists: `ps aux | grep cmd`
    │   ├── Process running → Waiting on I/O or deadlock
    │   └── Process gone → Crashed without exit code
```

### Lazy Loading (Discovery Methodology)

Don't try to enumerate every possible issue upfront. Instead:

1. **Provide methodology** for users to discover issues themselves
2. **Template for additions** so issues get documented as discovered
3. **Cross-reference logs/code** for deriving symptoms

```markdown
### Discovering Issues from Logs

1. Check the log file: `tail -100 /var/log/app.log`
2. Search for ERROR/WARN: `grep -E 'ERROR|WARN' /var/log/app.log`
3. Find the first error in a failure sequence

### Issue Template

When documenting a new issue, use this format:

**Symptom:** [What the user sees - error message, behavior]

**Cause:** [Technical explanation of why this happens]

**Fix:**
\`\`\`bash
[Commands to resolve]
\`\`\`

**Prevention:** [How to avoid in future, if applicable]
```

### Recovery Checklists

For multi-step recovery procedures:

```markdown
### Recovery Checklist

When things go wrong, follow these steps in order:

1. [ ] **Stop the process** (if running):
   \`\`\`bash
   ./stop.sh
   \`\`\`

2. [ ] **Check what happened**:
   \`\`\`bash
   cat /var/log/app.log | tail -50
   \`\`\`

3. [ ] **Clean up state** (if needed):
   \`\`\`bash
   rm -f /tmp/app.lock
   \`\`\`

4. [ ] **Fix underlying issues** based on logs

5. [ ] **Restart**:
   \`\`\`bash
   ./start.sh
   \`\`\`
```

## Anti-Patterns

### Assuming Baseline Knowledge

**BAD:**
```markdown
## Fixing the Widget

Run the reticulation script with the --force flag.
```

**GOOD:**
```markdown
## Widget fails to initialize

**Symptom:** "Widget initialization failed" error on startup.

**Cause:** Cached state from previous version is incompatible.

**Fix:**
\`\`\`bash
./scripts/reticulate.sh --force
\`\`\`

This clears the widget cache and rebuilds from scratch.
```

### Missing the Symptom

**BAD - leads with cause:**
```markdown
## DNS Cache Issues

When the DNS cache contains stale entries...
```

**GOOD - leads with symptom:**
```markdown
## "Cannot connect to server" error

**Symptom:** Commands fail with "cannot connect" even though the server is reachable.

**Cause:** DNS cache contains stale entries.
```

### Wall of Text

**BAD:**
```markdown
## Troubleshooting

If you encounter issues, first check that the service is running by using
the systemctl status command. If the service is not running, you can start
it with systemctl start. However, if it fails to start, check the journal
logs using journalctl -u service-name. Common issues include missing
configuration files, which you can fix by running the setup script again...
```

**GOOD:**
```markdown
## Troubleshooting

### Quick Scan

| Symptom | Fix |
|---------|-----|
| Service not running | `systemctl start service-name` |
| Service won't start | Check logs: `journalctl -u service-name` |
| "Config not found" | Run `./setup.sh` |
```

### No Recovery Path

**BAD - states problem without solution:**
```markdown
## Known Issues

- The cache may become corrupted after power loss.
- Large files may cause memory exhaustion.
```

**GOOD - provides recovery:**
```markdown
## Known Issues

### Cache corruption after power loss

**Symptom:** "Cache checksum mismatch" error after unexpected shutdown.

**Fix:**
\`\`\`bash
rm -rf /var/cache/app/*
./rebuild-cache.sh
\`\`\`

### Memory exhaustion with large files

**Symptom:** Process killed or "out of memory" errors with files >1GB.

**Fix:** Process files in chunks:
\`\`\`bash
./process.sh --chunk-size 100MB large-file.dat
\`\`\`
```

### Hiding Fixes in Prose

**BAD:**
```markdown
If you see the "connection refused" error, this typically means the server
isn't running. You should check if the server process is active, and if not,
you can start it by navigating to the server directory and running the start
command with appropriate flags.
```

**GOOD:**
```markdown
### "Connection refused" error

**Fix:**
\`\`\`bash
cd /opt/server && ./start.sh --daemon
\`\`\`
```

## Common Issue Categories

Reference these categories when organizing troubleshooting sections:

| Category | Typical Symptoms | Common Causes |
|----------|-----------------|---------------|
| Startup | Won't start, crashes immediately | Config errors, missing deps |
| Connection | Timeout, refused, unreachable | Network, firewall, DNS |
| Authentication | 401, 403, permission denied | Credentials, tokens, permissions |
| State | Inconsistent data, stale cache | Corruption, version mismatch |
| Resource | OOM, disk full, too many files | Limits, leaks, accumulation |
| Timeout | Hangs, slow, deadline exceeded | Load, blocking ops, bad config |

## See Also

- `commands/loop.md` - Example applying these troubleshooting patterns
- `.claude/skills/python-scripting/python-scripting.md` - Error handling patterns in code
