# Kiro CLI Headless Mode Research

Research findings for implementing `/serve` (headless peer review) in Kiro CLI.

## Executive Summary

**Kiro CLI supports headless/non-interactive mode** via the `--no-interactive` flag, making it suitable for spawning peer review sessions in the `/serve` workflow step.

However, there are caveats:
1. **Authentication in CI/CD**: No official headless login method - session tokens must be copied manually
2. **Shell environment issues**: Commands run in interactive login shell by default (problematic with zsh + oh-my-zsh)
3. **Tool permissions**: Must use `--trust-tools` or `--trust-all-tools` to avoid prompts

## Supported Flags

| Flag | Purpose |
|------|---------|
| `--no-interactive` | Print first response to STDOUT without interactive mode |
| `--trust-all-tools` | Permit all tools without confirmation |
| `--trust-tools <list>` | Pre-approve specific tools (comma-separated) |
| `--format json` | Machine-readable output (for `whoami`, `settings`, `diagnostic`) |

## /serve Implementation Options

### Option 1: Headless Kiro Session (Recommended)

Spawn a separate Kiro CLI session for peer review:

```bash
git diff HEAD~1 | kiro-cli chat --no-interactive --trust-tools read,shell \
  "Review these changes for correctness, security issues, and potential bugs. Format as: VERDICT (approve/block), ISSUES (bulleted list), AUTO-FIXABLE (items that can be fixed automatically)."
```

**Pros**:
- Uses same AI capabilities as interactive session
- Consistent with Claude Code's `/serve` pattern
- Structured output for parsing

**Cons**:
- Requires authenticated session
- May have shell environment issues on some systems

### Option 2: Manual Review Fallback

If headless mode isn't available or doesn't work:

```
⚠️ HEADLESS REVIEW NOT AVAILABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Kiro CLI headless mode requires:
- Authenticated session (kiro-cli login)
- --no-interactive flag support

Fallback: Manual self-review

Changes to review:
<git diff output>

Please review for:
- Correctness
- Security issues
- Potential bugs

NEXT STEP: /line:tidy (skip review and commit)
```

### Option 3: External AI Review

Use a different tool for review if Kiro headless is unavailable:

```bash
# Example using Claude API directly
git diff HEAD~1 | curl -X POST https://api.anthropic.com/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -d @- <<EOF
{
  "model": "claude-sonnet-4",  // Use latest model
  "messages": [{"role": "user", "content": "Review: $(cat)"}]
}
EOF
```

## Known Issues

### Shell Environment Problems

Kiro executes bash commands using `/bin/zsh -il` (interactive login shell), which loads:
- oh-my-zsh configuration
- powerlevel10k themes
- Other shell customizations

This can cause issues with command execution. There's currently no way to configure Kiro to use a plain shell.

**Workaround**: None officially supported. Feature request exists on GitHub.

### Headless Authentication

No official method for headless login without browser. Community workarounds:
- Log in interactively once, copy session tokens
- Use IAM roles with Amazon Q policy (AWS environments only)

## Recommendation for Line Cook

Implement `/serve` with graceful degradation:

1. **Try headless Kiro** first with `--no-interactive`
2. **Fall back to manual review** if headless fails
3. **Document limitation** in README and steering files

The steering file should indicate that `/serve` may require manual review if headless mode isn't available:

```markdown
### serve - "Review changes"

Invoke headless review of completed work.

```bash
# Attempt headless review
git diff | kiro-cli chat --no-interactive --trust-all-tools "Review these changes..."
```

If headless mode fails, perform manual self-review before proceeding to tidy.
```

## Sources

- [Kiro CLI Commands Reference](https://kiro.dev/docs/cli/reference/cli-commands/)
- [Kiro CLI Settings](https://kiro.dev/docs/cli/reference/settings/)
- [GitHub Issue #3676: Shell execution issues](https://github.com/kirodotdev/Kiro/issues/3676)
- [DEV Community: Headless login discussion](https://dev.to/bharani_dharan_4504d6d3c1/comment/33551)
- [AWS Weekly Roundup: Kiro CLI January 2026](https://aws.amazon.com/blogs/aws/aws-weekly-roundup-kiro-cli-latest-features-aws-european-sovereign-cloud-ec2-x8i-instances-and-more-january-19-2026/)
