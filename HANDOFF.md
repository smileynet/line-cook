HANDOFF: LINE COOK — FULL PROJECT STATUS
══════════════════════════════════════════════════════════════

STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary: Line Cook is a mature AI-assisted development workflow tool at v0.20.0
         with 108 of 111 beads closed, 3 open (two P4 epics + one P4 task).
         Two open GitHub bugs remain. Working tree is clean on main.
Branch:  main
State:   paused (between work cycles)
Date:    2026-03-03

PROJECT OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Line Cook is a chezmoi-distributed plugin system for AI coding assistants
(Claude Code, Kiro, OpenCode). It provides two cycles:
  - Mise Cycle: brainstorm → sample → scope → finalize (ideas → tasks)
  - Run Cycle:  prep → cook → serve → tidy (tasks → shipped code)
  - Loop:       autonomous Run Cycles until no work remains

Structure:
  - plugins/claude-code/  — Claude Code plugin (primary)
  - plugins/kiro/         — Kiro plugin
  - plugins/opencode/     — OpenCode plugin
  - core/line_loop/       — Python package for autonomous loop (8 files, ~7k lines)
  - core/templates/       — Shared command/agent templates synced to all plugins
  - dev/                  — Release tooling, sync scripts
  - docs/decisions/       — 17 ADRs documenting design choices
  - tests/                — unittest-based test suite

RELEASE HISTORY (RECENT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
v0.20.0 (2026-03-01) — /sample command, smarter cook timeouts
v0.19.0 (2026-02-28) — stalled task detection, auto-retry interrupted tasks
v0.18.0 (2026-02-27) — /inspect-issues, /feedback-broker, trunk-based loop,
                        circuit breaker improvements, failure classification
v0.17.1 (2026-02-21) — loop crash fixes
v0.17.0 (2026-02-21) — Kiro support

Unreleased: Windows 11 native support, OpenCode backend

DECISIONS MADE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
17 ADRs documented in docs/decisions/. Key recent ones:
1. ADR-0016: Trunk-based loop development — loop runs on main by default
   instead of requiring epic branches
2. ADR-0017: Deferred findings triage — /serve routes to FIX/DEFER/RETRO
3. ADR-0014: Spice plugins for domain knowledge
4. ADR-0015: Shared modules vs bundled scripts — core/line_loop/ package
   is bundled into a single file for distribution
5. ADR-0009: Autonomous loop as external package — loop logic lives in
   core/line_loop/, bundled via dev/release.py --bundle

DEAD ENDS (DO NOT REVISIT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
None identified in this session (clean main, no active work).

Historical (from stashes):
1. epic/lc-3nl branch — has 2 stashes; work was done and stashed but not merged
2. epic/lc-j2x branch — has 1 stash; similarly stashed and abandoned
3. prompt-update branch — has 2 stashes; sous-chef/serve work stashed
4. go-cli branch — has 1 stash from 2026-01-21; appears long-abandoned

These stashes may contain salvageable work or may be obsolete. Review before
dropping.

CURRENT STATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Completed:
- 108 beads closed across the project lifetime
- v0.20.0 released with /sample and cook timeout improvements
- Windows 11 and OpenCode support implemented (unreleased)
- Issue agent improvements (confidence scores, timeout handling)
- Kiro task_injection workaround removed (#14, PR #19)
- Epic-only diagnostic added (#18, PR #20)

In progress:
- Nothing actively in progress (no in_progress beads)

Not started / Open:
- lc-bc5 [epic, P4]: Retrospective (empty — no children yet)
- lc-ltr [epic, P4]: Backlog (3/4 children closed)
  - lc-ltr.4 [task, P4]: DRY release notification template
    (nit from serve review, not trivially fixable due to different
    variable syntax between workflow YAML and template)

OPEN GITHUB ISSUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#10 [bug, triaged]: Loop serve phase returns BLOCKED for tasks that
    bd ready shows as unblocked
    - Root cause: sous-chef misinterprets parent-child deps as blockers
    - PR #21 open: fix/issue-10-sous-chef-dep-type-blocked
    - Adds dep-type guidance to sous-chef template

#16 [bug, triaged]: Windows support — 10 bugs across v0.18.0/v0.20.0
    - 5 bugs patched in-tree, but claude -p --output-format stream-json
      produces zero stdout on Windows subprocess invocation
    - Likely upstream Claude Code bug; needs upstream fix

OPEN PR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#21: fix: clarify parent-child dep semantics in sous-chef
    - Branch: fix/issue-10-sous-chef-dep-type-blocked
    - Fixes #10
    - Adds guidance to sous-chef template about parent-child vs blocks deps

NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Review and merge PR #21 (fixes #10, sous-chef dep type confusion)
   - Branch: fix/issue-10-sous-chef-dep-type-blocked

2. Cut v0.21.0 release — changelog already drafted in CHANGELOG.md [Unreleased]
   with Windows 11 support and OpenCode backend. After merging PR #21,
   consider including the fix.

3. Populate lc-bc5 Retrospective epic — currently empty. Could capture
   lessons from the v0.18-v0.20 development cycle (loop reliability,
   multi-CLI support, issue agent evolution).

4. Evaluate stashes — 6 stashes from old feature branches. Decide
   whether to apply, cherry-pick, or drop each one:
   - stash@{0,1}: epic/lc-3nl (loop branch management)
   - stash@{2}: epic/lc-j2x (broker/test work)
   - stash@{3,4}: prompt-update (serve/sous-chef)
   - stash@{5}: go-cli (Jan 2026, likely obsolete)

5. Address #16 Windows upstream blocker — monitor Claude Code releases
   for stream-json subprocess fix. The in-tree patches are applied but
   the core issue remains.

6. Close lc-ltr.4 or defer — the DRY notification template task is a
   nit (P4) with non-trivial variable syntax differences.

KEY FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- core/line_loop/          — Python package (7k lines) for autonomous loop
- plugins/claude-code/scripts/line-loop.py — Bundled loop script (6.3k lines,
  auto-generated — do NOT edit directly)
- dev/release.py           — Release tooling, includes bundle_line_loop()
- dev/sync-commands.sh     — Syncs templates to all three plugin dirs
- core/templates/          — Shared command/agent templates
- CHANGELOG.md             — Changelog with [Unreleased] section drafted
- docs/decisions/          — 17 ADRs documenting architectural choices
- tests/test_line_loop.py  — Unit tests (run: python3 -m unittest tests.test_line_loop -v)
- .beads/                  — Issue tracker database (111 issues)

GOTCHAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- After modifying core/line_loop/, MUST re-bundle via ./dev/release.py --bundle
  (includes syntax check, size guard, smoke test)
- Tests use unittest, NOT pytest (pytest not installed)
- Walrus operators in comprehensions leak scope — avoid (sous-chef catches this)
- parse_bd_json_item() in iteration.py handles both dict and list bd JSON
  responses — reuse instead of duplicating list-unwrapping logic
- core/templates/ must be synced to all 3 plugin dirs via dev/sync-commands.sh
- lookPath in chezmoi templates is non-hermetic (depends on runtime PATH)

OPEN QUESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- When to cut v0.21.0? Changelog is drafted. PR #21 should merge first.
- What goes in the Retrospective epic (lc-bc5)? No children defined yet.
- Are any of the 6 stashes still valuable, or should they be dropped?
- Is the Windows stream-json upstream bug being tracked by Anthropic?
