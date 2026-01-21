#!/usr/bin/env bash
# run-tests.sh - Main test runner for Line Cook cross-provider tests
#
# Runs all test scripts across available providers (Claude Code, OpenCode, Kiro).
#
# Usage:
#   ./tests/run-tests.sh [options]
#
# Options:
#   --provider <name>   Run tests for specific provider only (claude, opencode, kiro)
#   --test <name>       Run specific test only (getting-started, prep, cook, serve, tidy, work)
#   --tier <level>      Run tests by tier:
#                         unit - Fast tests (getting-started)
#                         integration - Medium tests (prep, serve, tidy)
#                         full - All tests including LLM-heavy (cook, work)
#   --dry-run           Check dependencies only, don't run tests
#   --help              Show this help
#
# Examples:
#   ./tests/run-tests.sh                    # Run all tests for all providers
#   ./tests/run-tests.sh --provider claude  # Run all tests for Claude Code only
#   ./tests/run-tests.sh --test prep        # Run prep test for all providers
#   ./tests/run-tests.sh --tier unit        # Run only fast unit tests

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    BOLD=''
    NC=''
fi

# Defaults
PROVIDER=""
TEST=""
TIER="full"
DRY_RUN=false

# Test tiers
UNIT_TESTS=("getting-started")
INTEGRATION_TESTS=("prep" "serve" "tidy")
FULL_TESTS=("cook" "work")

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        --test)
            TEST="$2"
            shift 2
            ;;
        --tier)
            TIER="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            head -40 "$0" | tail -35
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Print banner
echo ""
echo -e "${BOLD}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║      Line Cook Cross-Provider Test Suite       ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Check dependencies
echo "Checking dependencies..."
DEPS=("git" "jq" "bd")
PROVIDERS=("claude" "opencode" "kiro-cli")
MISSING_DEPS=()
AVAILABLE_PROVIDERS=()

for dep in "${DEPS[@]}"; do
    if command -v "$dep" >/dev/null 2>&1; then
        echo -e "  ${GREEN}Found${NC}: $dep"
    else
        echo -e "  ${RED}Missing${NC}: $dep"
        MISSING_DEPS+=("$dep")
    fi
done

for prov in "${PROVIDERS[@]}"; do
    if command -v "$prov" >/dev/null 2>&1; then
        echo -e "  ${GREEN}Found${NC}: $prov"
        AVAILABLE_PROVIDERS+=("$prov")
    else
        echo -e "  ${YELLOW}Not found${NC}: $prov (tests will skip)"
    fi
done

echo ""

if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
    echo -e "${RED}Error: Missing required dependencies: ${MISSING_DEPS[*]}${NC}"
    echo "Please install them and try again."
    exit 1
fi

if [[ ${#AVAILABLE_PROVIDERS[@]} -eq 0 ]]; then
    echo -e "${RED}Error: No providers available for testing${NC}"
    echo "Install at least one of: claude, opencode, kiro-cli"
    exit 1
fi

if $DRY_RUN; then
    echo "Dry run complete. Dependencies are satisfied."
    exit 0
fi

# Build test list based on tier
TESTS_TO_RUN=()
case $TIER in
    unit)
        TESTS_TO_RUN=("${UNIT_TESTS[@]}")
        ;;
    integration)
        TESTS_TO_RUN=("${UNIT_TESTS[@]}" "${INTEGRATION_TESTS[@]}")
        ;;
    full)
        TESTS_TO_RUN=("${UNIT_TESTS[@]}" "${INTEGRATION_TESTS[@]}" "${FULL_TESTS[@]}")
        ;;
    *)
        echo -e "${RED}Unknown tier: $TIER${NC}"
        exit 1
        ;;
esac

# Override with specific test if requested
if [[ -n "$TEST" ]]; then
    TESTS_TO_RUN=("$TEST")
fi

# Cost warning for full tests
if [[ "$TIER" == "full" || "$TEST" == "cook" || "$TEST" == "work" ]]; then
    echo -e "${YELLOW}Warning: Running LLM-heavy tests.${NC}"
    echo -e "${YELLOW}Expected API costs: ~\$0.50-2.00 depending on providers.${NC}"
    echo -e "${YELLOW}Full test suite may take 30+ minutes.${NC}"
    echo ""
    read -p "Continue? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    echo ""
fi

# Run tests
TOTAL_PASSED=0
TOTAL_FAILED=0
TOTAL_SKIPPED=0

for test_name in "${TESTS_TO_RUN[@]}"; do
    test_script="$SCRIPT_DIR/test-$test_name.sh"

    if [[ ! -f "$test_script" ]]; then
        echo -e "${RED}Test script not found: $test_script${NC}"
        ((TOTAL_FAILED++))
        continue
    fi

    # Make sure script is executable
    chmod +x "$test_script"

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Run with specific provider or all
    if [[ -n "$PROVIDER" ]]; then
        if "$test_script" "$PROVIDER"; then
            ((TOTAL_PASSED++))
        else
            ((TOTAL_FAILED++))
        fi
    else
        if "$test_script"; then
            ((TOTAL_PASSED++))
        else
            ((TOTAL_FAILED++))
        fi
    fi
done

# Summary
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}                    Summary                      ${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  Tests passed:  ${GREEN}$TOTAL_PASSED${NC}"
echo -e "  Tests failed:  ${RED}$TOTAL_FAILED${NC}"
echo ""

if [[ $TOTAL_FAILED -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}${BOLD}Some tests failed.${NC}"
    exit 1
fi
