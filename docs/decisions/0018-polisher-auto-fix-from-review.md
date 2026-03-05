---
status: accepted
date: 2026-03-04
tags: [architecture, agents, workflow]
relates-to: ["0006", "0007", "0017"]
superseded-by: null
---

# 0018: Polisher auto-fix from review

## Context

Sous-chef already classifies findings with `Auto-fixable: true | false`, serve already reserves an `Auto-fixed:` output section, and polisher already has Edit tools. But nothing connects them — auto-fixable findings flow straight to tidy and become beads, creating overhead for trivial fixes like stale comments, unused imports, and naming inconsistencies.

Industry practice (Parasoft, Apiiro, CodeRabbit, Prettier/ESLint ecosystem) consistently separates mechanical fixes from judgment-requiring review: formatters auto-fix style, linters find bugs. The key guideline: "Straightforward violations are candidates for automation — style issues, common patterns, standard remediations. Complex architectural decisions, design changes, and business logic modifications should remain manual."

Options considered:
- **Status quo** — all findings become beads in tidy, even trivial ones. Simple but creates bead overhead and wastes loop iterations on mechanical fixes.
- **Auto-fix in sous-chef** — reviewer applies fixes directly. Violates ADR-0006's read-only reviewer principle and ADR-0007's author/reviewer separation.
- **New auto-fix agent** — dedicated fixer between review and polish. Adds a fourth agent without clear benefit over extending polisher.
- **Polisher applies review-directed fixes** — sous-chef identifies, polisher applies, serve reports. Reuses existing infrastructure with minimal new surface area.

## Decision

Wire the three existing pieces together: sous-chef classifies findings as `Auto-fixable: true | false`, serve extracts auto-fixable findings and passes them to polisher alongside the file list, and polisher applies them before its standard clarity polish. Serve then populates the `Auto-fixed:` output section from polisher's results.

Key constraints:
- **APPROVED-only** — auto-fix only runs on APPROVED verdicts. NEEDS_CHANGES goes back to cook; mixing auto-fix with rework creates confusion.
- **Behavioral classification** — `Auto-fixable` is about whether the fix is mechanical, not how important it is. A P2 naming bug can be auto-fixable; a P4 architecture suggestion cannot.
- **Graceful degradation** — if polisher skips a directed fix (code shifted, ambiguous suggestion), it flows to tidy as a normal `[DEFER]` finding.
- **Separate commit preserved** — polisher's auto-fixes go in the same `polish:` commit as clarity changes, keeping author work and polish work in distinct commits.
- **Reviewer-fixer separation** — sous-chef (read-only) identifies problems; polisher (edit) applies fixes. Different agents, different contexts, no anchoring bias.

## Consequences

- Positive: Trivial findings resolved automatically instead of becoming beads — reduces bead overhead and loop iterations
- Positive: Sous-chef can focus review feedback on substantive issues, knowing mechanical ones will be handled
- Positive: Polisher commit (`polish: refine <id>`) provides clear audit trail — easy to review or rollback
- Positive: No Python code changes — parsing already handles `Auto-fixed:` as a section boundary
- Negative: Polisher now has a dual role (clarity polish + directed fixes) — slightly more complex prompt
- Negative: Auto-fix classification is a judgment call by sous-chef — borderline items may be misclassified
- Neutral: Skipped auto-fixes appear as `[DEFER]` findings — same path as before, no new failure mode
