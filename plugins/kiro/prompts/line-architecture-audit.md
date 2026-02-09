## Summary

**Analyze codebase structure and detect code smells.** Complements `@line-plan-audit` (bead quality) with code-level analysis.

**STOP after completing.** Show audit report and wait for user.

---

## Arguments

```
@line-architecture-audit [scope] [--report]

scope:
  quick     - Run validation scripts only (default)
  full      - Full analysis with smell detection
  <path>    - Specific directory to analyze

--report    - Generate dated report in docs/features/
```

### Scope Behavior

| Scope | Focus | Includes |
|-------|-------|----------|
| `quick` | Fast validation | Scripts only, no metrics collection |
| `full` | Comprehensive | Metrics, smell detection, refactoring candidates |
| `<path>` | Targeted | Analyze specific directory or module |

---

## Process

### Step 1: Parse Arguments

Extract scope and flags from command:

```bash
# Default: quick scope
SCOPE="quick"
GENERATE_REPORT=false
TARGET_PATH="."

# Parse arguments
# First non-flag arg is scope or path
# --report enables dated report generation
```

### Step 2: Run Validation Scripts

Execute existing validation tools if present:

```bash
# Check for validation scripts
if [ -f "dev/check-plugin-health.py" ]; then
  python3 dev/check-plugin-health.py
fi

if [ -f "dev/check-platform-parity.py" ]; then
  python3 dev/check-platform-parity.py
fi

if [ -f "dev/doctor-docs.py" ]; then
  python3 dev/doctor-docs.py
fi
```

Record pass/fail status for each script.

### Step 3: Collect Metrics (Full Scope Only)

For `full` scope, collect quantitative measurements:

#### 3a: File Size Analysis

```bash
# Find large files (>500 LOC)
find $TARGET_PATH -name "*.py" -o -name "*.ts" -o -name "*.js" | \
  xargs wc -l 2>/dev/null | sort -rn | head -20

# Identify files exceeding thresholds
# Warning: >500 LOC
# Critical: >1000 LOC
```

#### 3b: Complexity Metrics (If Tools Available)

```bash
# Python complexity (if radon installed)
if command -v radon &>/dev/null; then
  radon cc -a -nc $TARGET_PATH 2>/dev/null
fi

# Line counts by language
if command -v cloc &>/dev/null; then
  cloc --quiet $TARGET_PATH
fi
```

### Step 4: Detect Code Smells (Full Scope Only)

Systematically check for smell categories per docs/guidance/architecture-audit.md:

#### 4a: Bloaters

```bash
# Long files (>500 LOC)
find $TARGET_PATH \( -name "*.py" -o -name "*.ts" -o -name "*.js" \) \
  -exec wc -l {} + 2>/dev/null | awk '$1 > 500'

# Long parameter lists (>4 parameters)
grep -rn "def.*(" --include="*.py" $TARGET_PATH | grep -E ",.*,.*,.*,"

# Data clumps (same params in multiple functions)
# Look for repeated parameter patterns
```

#### 4b: Couplers

```bash
# Message chains (long dot chains)
grep -rn "\.\w\+\.\w\+\.\w\+\.\w\+" --include="*.py" --include="*.ts" $TARGET_PATH

# High import coupling
grep -rh "^from\|^import" --include="*.py" $TARGET_PATH | \
  sed 's/from \([^ ]*\).*/\1/; s/import \([^ ]*\).*/\1/' | \
  sort | uniq -c | sort -rn | head -10
```

#### 4c: Change Preventers

```bash
# Files with high churn (frequently modified)
git log --format='' --name-only -- $TARGET_PATH | \
  sort | uniq -c | sort -rn | head -10

# Shotgun surgery candidates (files often changed together)
git log --oneline --name-only -- $TARGET_PATH | \
  grep -v "^[a-f0-9]" | sort | uniq -c | sort -rn | head -10
```

#### 4d: Dispensables

```bash
# Dead imports (Python)
if command -v pylint &>/dev/null; then
  pylint --disable=all --enable=W0611 $TARGET_PATH 2>/dev/null
fi

# Duplicate code detection
if command -v jscpd &>/dev/null; then
  jscpd --threshold 3 $TARGET_PATH --reporters consoleFull 2>/dev/null
fi

# Small files (potential lazy classes)
find $TARGET_PATH \( -name "*.py" -o -name "*.ts" \) \
  -exec wc -l {} + 2>/dev/null | awk '$1 < 20 && $1 > 0'
```

#### 4e: CLI/Plugin-Specific (If Applicable)

```bash
# Command file sizes (if commands/ exists)
if [ -d "commands" ]; then
  find commands/ -name "*.md" -exec wc -l {} + | sort -rn
fi

# Platform coupling (check for platform-specific imports in shared code)
if [ -d "scripts" ]; then
  grep -rn "claude\|opencode\|kiro" --include="*.py" scripts/ 2>/dev/null
fi
```

### Step 5: Check Documentation Health

```bash
# Run doc validation
if [ -f "dev/doctor-docs.py" ]; then
  python3 dev/doctor-docs.py
fi

# Count ADRs
if [ -d "docs/decisions" ]; then
  adr_count=$(ls -1 docs/decisions/*.md 2>/dev/null | wc -l)
  echo "ADRs: $adr_count"

  # Check for superseded without replacement
  grep -l "superseded" docs/decisions/*.md 2>/dev/null
fi
```

### Step 6: Prioritize Findings

Categorize findings by severity:

| Priority | Criteria | Examples |
|----------|----------|----------|
| **P0 (Critical)** | Blocks work, security issues | Circular deps, complexity >15, broken scripts |
| **P1 (High)** | Should fix soon | Files >500 LOC, shotgun surgery, complexity 10-15 |
| **P2 (Medium)** | Fix when nearby | Message chains, high coupling, complexity 8-10 |
| **P3 (Low)** | Track, fix opportunistically | Minor duplication, lazy classes |

### Step 7: Output Report

Output the audit report:

```
╔══════════════════════════════════════════════════════════════╗
║  ARCHITECTURE AUDIT                                          ║
╚══════════════════════════════════════════════════════════════╝

Scope: <quick|full|path>
Date: <YYYY-MM-DD>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXECUTIVE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Category | Status | Issues |
|----------|--------|--------|
| Validation Scripts | [OK/WARN/FAIL] | count |
| Structural | [OK/WARN/FAIL] | count |
| Complexity | [OK/WARN/FAIL] | count |
| Code Smells | [OK/WARN/FAIL] | count |
| Documentation | [OK/WARN/FAIL] | count |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VALIDATION SCRIPTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ check-plugin-health.py: PASSED
✓ check-platform-parity.py: PASSED
✗ doctor-docs.py: 2 broken links found

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL (must fix)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[COMPLEXITY] <file>:<function> complexity=16
  Exceeds maximum threshold (>15)
  Technique: Extract Method, Decompose Conditional

[BLOATER] <file> is 1,247 LOC
  Exceeds critical threshold (>1000)
  Technique: Extract Class, Split Module

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HIGH (should fix soon)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[BLOATER] <file> is 623 LOC
  Exceeds warning threshold (>500)
  Technique: Extract Class

[COUPLER] <file>:<line> message chain (4 levels)
  Pattern: a.b().c().d().e()
  Technique: Hide Delegate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEDIUM (fix when nearby)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[COUPLER] High import coupling: <module>
  Imported by 15 files
  Consider: Interface extraction

[CHURN] High modification frequency: <file>
  Modified 23 times in last 30 days
  Indicates: Possible divergent change smell

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOW (track, fix opportunistically)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[DISPENSABLE] <file> is only 12 LOC
  May be lazy class
  Technique: Inline Class (if warranted)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUALITY METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Lines of Code: <total>
Files: <count>
Average Complexity: <score> (target: <5)
Duplicate Code: <pct>% (target: <3%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REFACTORING RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Issue | Smell | Technique | Priority | Effort |
|-------|-------|-----------|----------|--------|
| <file> | Large Class | Extract Class | P1 | Medium |
| <func> | Long Method | Extract Method | P2 | Low |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issues: <critical> critical, <high> high, <medium> medium, <low> low
Overall Health: [GOOD/MODERATE/NEEDS ATTENTION]

NEXT STEP: <action based on findings>
```

**NEXT STEP logic:**
- If critical issues: "Fix critical issues before refactoring"
- If validation scripts failed: "Resolve script failures first"
- If high issues only: "Schedule refactoring for top high-priority items"
- If moderate issues: "Consider addressing during nearby work"
- If clean: "Codebase is healthy - continue normal development"

### Step 8: Generate Report File (If --report)

If `--report` flag was passed:

```bash
REPORT_DATE=$(date +%Y-%m-%d)
REPORT_PATH="docs/features/architecture-audit-${REPORT_DATE}.md"

# Write structured markdown report
cat > $REPORT_PATH << EOF
# Architecture Audit Report
Date: $REPORT_DATE

## Executive Summary
...

## Findings
...

## Recommendations
...
EOF

echo "Report saved to: $REPORT_PATH"
```

---

## Validation Rules Reference

### File Size Thresholds

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Lines per file | <200 | 200-500 | >500 |
| Lines per method | <20 | 20-50 | >50 |
| Parameters per method | 1-3 | 4-6 | >6 |

### Complexity Thresholds

| Metric | Good | Moderate | Refactor | Warning | Critical |
|--------|------|----------|----------|---------|----------|
| Cyclomatic | 1-4 | 5-7 | 8-10 | 10-15 | >15 |

### Code Smell Categories

| Category | Examples | Detection |
|----------|----------|-----------|
| **Bloaters** | Long method, large class | LOC counts |
| **Couplers** | Feature envy, message chains | Import/call analysis |
| **Change Preventers** | Shotgun surgery | Git history |
| **Dispensables** | Dead code, duplicates | Coverage, pattern matching |

---

## Integration

| Command | Relationship |
|---------|--------------|
| `@line-plan-audit` | Bead content checks (this = code checks) |
| `bd doctor` | System checks (install, hooks, sync) |
| `@line-serve` | Code review (this = structural analysis) |

---

## Example Usage

```bash
# Quick validation only (default)
@line-architecture-audit

# Full analysis with smell detection
@line-architecture-audit full

# Analyze specific directory
@line-architecture-audit scripts/

# Generate dated report
@line-architecture-audit full --report
```

---

## Reference

See [Architecture Audit Guide](../../docs/guidance/architecture-audit.md) for:
- Complete code smell catalog
- Refactoring technique reference
- Quality checklist
- Detailed methodology
