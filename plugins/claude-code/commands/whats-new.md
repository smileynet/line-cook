---
description: Recent changes
allowed-tools: Bash, Read, Glob
---


## Summary

**Contextualized release digest.** Reads the CHANGELOG and synthesizes it into a narrative the user can act on — not a rote listing, but an explanation of what changed, why it matters, and what to try.

**Arguments:** `$ARGUMENTS` (optional)
- `(empty)` — Latest 3 releases, contextualized
- `<version>` — Deep dive on a specific version
- `all` — Timeline overview with themes per release

---

## Process

### Step 1: Locate and Read CHANGELOG

Use Glob to search for `**/CHANGELOG.md` near the plugin installation or in the current working directory.

If not found locally, fetch via GitHub API:

```bash
gh api repos/smileynet/line-cook/contents/CHANGELOG.md \
  --jq '.content' | base64 -d
```

Parse the content using [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format — version sections delimited by `## [X.Y.Z]` headers, with `### Added`, `### Changed`, `### Fixed` subsections.

### Step 2: Determine Scope from Arguments

- **No argument:** Latest 3 releases
- **Version number** (e.g., `0.14.0`): Deep dive on that version
- **`all`:** Timeline overview

### Step 3: Synthesize and Present

**Your job is to contextualize, not transcribe.** The CHANGELOG already exists — the user can read it directly. You add value by:

1. **Grouping related changes into themes** — If 4 entries are all about loop reliability, say "Loop execution got a major reliability overhaul" and explain what that means practically.

2. **Explaining impact on the user's workflow** — Don't just say "Added /close-service command." Say what it changes about how they work: "Epics now get the same quality gate treatment that features get — you'll be prompted for E2E validation before an epic closes."

3. **Highlighting what to try** — For each theme, suggest a concrete action: "Try `/line:loop --epic` to focus autonomous execution on a single epic."

4. **Noting breaking changes prominently** — If something moved, renamed, or behaves differently, call it out clearly so users aren't surprised.

5. **Connecting releases to each other** — If v0.14.0 added a feature and v0.15.0 fixed bugs in it, say so.

**Format for latest 3 releases (default):**

```
WHAT'S NEW IN LINE COOK
━━━━━━━━━━━━━━━━━━━━━━━

v0.15.0 — <release theme in a few words>

<2-4 sentence narrative: what's the story of this release? What problem
did it solve? What should users notice?>

  Try: <concrete command or workflow to experience the change>

v0.14.0 — <release theme>

<narrative>

  Try: <action>

v0.13.2 — <release theme>

<narrative>

Older releases: /line:whats-new all
Deep dive: /line:whats-new <version>
```

**Format for specific version deep dive:**

```
LINE COOK v0.14.0
━━━━━━━━━━━━━━━━━

<Theme — one sentence summarizing the release>

<Theme 1 heading>
<Paragraph explaining the group of related changes, why they were made,
and what the user should know. Reference specific commands.>

<Theme 2 heading>
<Same pattern>

Bug fixes
<Brief list of fixes with context on what users would have experienced>

  Try: <actions to experience the changes>

Back: /line:whats-new
```

**Format for all versions timeline:**

```
LINE COOK TIMELINE
━━━━━━━━━━━━━━━━━━

v0.15.0  2026-02-15  <theme phrase — NOT a list of changes>
v0.14.0  2026-02-12  <theme phrase>
v0.13.2  2026-02-11  <theme phrase>
...

Deep dive: /line:whats-new <version>
```

Each theme phrase should capture the *story* of the release (e.g., "Loop reliability overhaul" not "Added circuit breaker, caching, findings tracking").

### Step 4: Invite Conversation

End with:

```
Questions about any of these changes? Just ask.
```

The user can ask follow-up questions and you should answer using the CHANGELOG content and your knowledge of Line Cook's architecture.

---

## Example Output (default)

```
WHAT'S NEW IN LINE COOK
━━━━━━━━━━━━━━━━━━━━━━━

v0.15.0 — Loop reliability overhaul

The autonomous loop got significantly more robust. A circuit breaker
now stops runaway failures, hierarchy maps are cached to cut iteration
overhead, and periodic bd sync keeps long-running loops from drifting
out of date. Four bugs in loop execution were also fixed — notably,
the skip list and epic filter are now actually respected during cook.

  Try: /line:loop to experience the improved autonomous execution.

v0.14.0 — Epic quality gates and the spice rack

Epics now get proper closure validation via /close-service, matching
what /plate already does for features. The serve phase was reordered
to review your code first, then polish — so reviews are on your
actual work. The spice rack pattern launched with game-spice as the
first domain addon.

  Try: /line:close-service after completing an epic's features.

v0.13.2 — Marketplace compatibility fix

A path discovery bug meant prep, cook, and serve didn't work when
Line Cook was installed from the marketplace (vs cloned locally).
Fixed by switching to dynamic script discovery.

Older releases: /line:whats-new all
Deep dive: /line:whats-new <version>

Questions about any of these changes? Just ask.
```

---

## Example Usage

```
/line:whats-new              # Latest 3 releases, contextualized
/line:whats-new 0.14.0       # Deep dive on specific version
/line:whats-new all          # Timeline overview
```
