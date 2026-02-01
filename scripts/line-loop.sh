#!/bin/bash
# Line Cook autonomous loop - runs /line:run until no tasks remain

set -e

MAX_ITERATIONS=${1:-25}
ITERATION=0
COMPLETED=0

echo "Line Cook Loop starting (max $MAX_ITERATIONS iterations)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while true; do
  # Check for ready tasks
  READY_COUNT=$(bd ready 2>/dev/null | grep -c "^\[" || echo 0)

  if [[ $READY_COUNT -eq 0 ]]; then
    echo ""
    echo "No tasks ready. Loop complete."
    break
  fi

  if [[ $ITERATION -ge $MAX_ITERATIONS ]]; then
    echo ""
    echo "Reached iteration limit ($MAX_ITERATIONS). Stopping."
    break
  fi

  ITERATION=$((ITERATION + 1))
  echo ""
  echo "[$ITERATION/$MAX_ITERATIONS] $READY_COUNT tasks ready"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Run one task cycle via Claude
  if claude --skill line:run; then
    COMPLETED=$((COMPLETED + 1))
  else
    echo ""
    echo "Task failed. Stopping loop."
    break
  fi
done

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  LOOP COMPLETE                                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Iterations: $ITERATION / $MAX_ITERATIONS"
echo "Tasks completed: $COMPLETED"
echo "Remaining ready: $(bd ready 2>/dev/null | grep -c "^\[" || echo 0)"
