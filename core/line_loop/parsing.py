"""Output parsing functions for line-loop.

Functions for parsing Claude output:
- parse_serve_result: Extract SERVE_RESULT block
- parse_serve_feedback: Extract detailed review feedback
- parse_intent_block: Extract INTENT block
- parse_stream_json_event: Parse streaming JSON events
- extract_text_from_event: Get text from streaming event
- extract_actions_from_event: Get tool actions from event
- update_action_from_result: Update actions with tool results
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Optional

from .config import OUTPUT_SUMMARY_MAX_LENGTH
from .models import ActionRecord, ServeFeedback, ServeFeedbackIssue, ServeResult


def parse_serve_result(output: str) -> Optional[ServeResult]:
    """Parse SERVE_RESULT block from serve phase output.

    Extracts the structured verdict information that the serve phase emits
    to communicate code review results back to the loop.

    Expected format in output:
        SERVE_RESULT
        verdict: APPROVED|NEEDS_CHANGES|BLOCKED|SKIPPED
        continue: true|false
        next_step: /line:tidy (optional)
        blocking_issues: 0

    Args:
        output: Raw output from the serve phase (may contain stream-json events).

    Returns:
        ServeResult with verdict, continue flag, next_step, and blocking_issues.
        Returns None if SERVE_RESULT block cannot be parsed.
    """
    # Look for the SERVE_RESULT block
    pattern = r"SERVE_RESULT\s*\n(?:│\s*)?verdict:\s*(\w+).*?(?:│\s*)?continue:\s*(true|false).*?(?:│\s*)?(?:next_step:\s*(\S+))?.*?(?:│\s*)?blocking_issues:\s*(\d+)"
    match = re.search(pattern, output, re.DOTALL | re.IGNORECASE)

    if match:
        return ServeResult(
            verdict=match.group(1).upper(),
            continue_=match.group(2).lower() == "true",
            next_step=match.group(3),
            blocking_issues=int(match.group(4))
        )

    # Try simpler patterns for each field
    verdict_match = re.search(r"verdict:\s*(APPROVED|NEEDS_CHANGES|BLOCKED|SKIPPED)", output, re.IGNORECASE)
    if verdict_match:
        continue_match = re.search(r"continue:\s*(true|false)", output, re.IGNORECASE)
        blocking_match = re.search(r"blocking_issues:\s*(\d+)", output, re.IGNORECASE)
        next_step_match = re.search(r"next_step:\s*(\S+)", output, re.IGNORECASE)

        return ServeResult(
            verdict=verdict_match.group(1).upper(),
            continue_=continue_match.group(1).lower() == "true" if continue_match else True,
            next_step=next_step_match.group(1) if next_step_match else None,
            blocking_issues=int(blocking_match.group(1)) if blocking_match else 0
        )

    return None


def parse_serve_feedback(output: str, task_id: Optional[str] = None, task_title: Optional[str] = None, attempt: int = 1) -> Optional[ServeFeedback]:
    """Parse detailed feedback from serve output for retry context.

    Extracts:
    - Summary from the "Summary:" section
    - Issues from "Issues to file" or issue list sections
    - Severity markers like [critical], [major], [minor], [nit], [P1], [P2], etc.

    Returns ServeFeedback or None if parsing fails.
    """
    # Extract summary - look for Summary: section
    summary = ""
    summary_match = re.search(
        r"Summary:\s*\n\s*(.+?)(?:\n\n|\nAuto-fixed:|\nIssues|\nPositive)",
        output,
        re.DOTALL | re.IGNORECASE
    )
    if summary_match:
        summary = summary_match.group(1).strip()

    # Extract issues - look for various patterns
    issues: list[ServeFeedbackIssue] = []

    # Pattern 1: Issues to file in /tidy section with severity markers
    # e.g., "- [P1] "title" - description" or "- [major] file:line - issue"
    issue_section_match = re.search(
        r"Issues to file[^\n]*:\s*\n((?:\s*-[^\n]+\n?)+)",
        output,
        re.IGNORECASE
    )

    # Pattern 2: Issues found section from sous-chef
    # e.g., "Issues found:\n  - Severity: major\n    File/line: src/foo.py:42\n    Issue: desc"
    issues_found_match = re.search(
        r"Issues found:\s*\n((?:.*?\n)+?)(?:\n\n|Positive|$)",
        output,
        re.DOTALL | re.IGNORECASE
    )

    # Parse simple issue list (Pattern 1)
    if issue_section_match:
        issue_text = issue_section_match.group(1)
        # Match lines like: - [P1] "title" - description or - [major] description
        issue_pattern = re.compile(
            r'-\s*\[([^\]]+)\]\s*(?:"([^"]+)"\s*-\s*)?(.+?)(?=\n\s*-|\n\n|$)',
            re.MULTILINE | re.DOTALL
        )
        for match in issue_pattern.finditer(issue_text):
            severity_raw = match.group(1).lower()
            # Normalize severity: P1/P2 -> major, P3 -> minor, P4 -> nit
            if severity_raw in ('p1', 'p2', 'critical'):
                severity = 'critical' if severity_raw in ('p1', 'critical') else 'major'
            elif severity_raw in ('p3', 'minor'):
                severity = 'minor'
            elif severity_raw in ('p4', 'nit', 'retro'):
                severity = 'nit'
            else:
                severity = severity_raw

            title = match.group(2)
            description = match.group(3).strip()

            issues.append(ServeFeedbackIssue(
                severity=severity,
                location=title,  # Use title as location hint
                problem=description,
                suggestion=None
            ))

    # Parse detailed issue format (Pattern 2) from sous-chef
    if issues_found_match and not issues:
        issue_text = issues_found_match.group(1)
        # Look for structured issue blocks
        severity_matches = re.findall(
            r"Severity:\s*(\w+).*?(?:File/line:|Location:)\s*([^\n]+).*?Issue:\s*([^\n]+)(?:.*?Suggestion:\s*([^\n]+))?",
            issue_text,
            re.DOTALL | re.IGNORECASE
        )
        for sev, loc, prob, sugg in severity_matches:
            issues.append(ServeFeedbackIssue(
                severity=sev.lower(),
                location=loc.strip(),
                problem=prob.strip(),
                suggestion=sugg.strip() if sugg else None
            ))

    # If we found a summary or issues, create feedback
    if summary or issues:
        # Get verdict from serve result
        serve_result = parse_serve_result(output)
        verdict = serve_result.verdict if serve_result else "NEEDS_CHANGES"

        return ServeFeedback(
            verdict=verdict,
            summary=summary,
            issues=issues,
            task_id=task_id,
            task_title=task_title,
            attempt=attempt
        )

    return None


def parse_intent_block(output: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Parse INTENT and BEFORE -> AFTER from cook output.

    Looks for:
      INTENT:
        <description>
        Goal: <deliverable>

      BEFORE -> AFTER:
        <before> -> <after>

    Returns: (intent, before_state, after_state)
    """
    intent = None
    before_state = None
    after_state = None

    # Parse INTENT block
    intent_match = re.search(
        r"INTENT:\s*\n\s*(.+?)(?:\n\s*Goal:\s*(.+?))?(?:\n\n|\nBEFORE)",
        output,
        re.DOTALL
    )
    if intent_match:
        intent = intent_match.group(1).strip()
        if intent_match.group(2):
            intent = f"{intent} | Goal: {intent_match.group(2).strip()}"

    # Parse BEFORE -> AFTER block
    before_after_match = re.search(
        r"BEFORE\s*→\s*AFTER:\s*\n\s*(.+?)\s*→\s*(.+?)(?:\n|$)",
        output,
        re.IGNORECASE
    )
    if before_after_match:
        before_state = before_after_match.group(1).strip()
        after_state = before_after_match.group(2).strip()

    return intent, before_state, after_state


def parse_stream_json_event(line: str) -> Optional[dict]:
    """Parse a single line of Claude's stream-json output format.

    Claude CLI with --output-format stream-json emits one JSON object
    per line, representing conversation events (assistant messages,
    tool uses, tool results, etc.).

    Args:
        line: A single line from stream-json output.

    Returns:
        Parsed event dict if valid JSON, None otherwise.
        Empty or whitespace-only lines return None.
    """
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def extract_text_from_event(event: dict) -> str:
    """Extract text content from a stream-json assistant message event.

    Claude's stream-json output format wraps messages in event objects.
    This extracts the human-readable text from assistant responses,
    concatenating all text content blocks.

    Args:
        event: Parsed JSON event from stream-json output.
               Expected structure: {"type": "assistant", "message": {"content": [...]}}

    Returns:
        Concatenated text from all text content blocks, or empty string
        if event is not an assistant message or has no text content.
    """
    if event.get("type") != "assistant":
        return ""
    content = event.get("message", {}).get("content", [])
    return "\n".join(
        b.get("text", "") for b in content if b.get("type") == "text"
    )


def extract_actions_from_event(
    event: dict,
    pending_actions: dict[str, ActionRecord]
) -> list[ActionRecord]:
    """Extract tool_use blocks from a stream-json assistant message event.

    Parses tool calls from the assistant's response and tracks them in
    pending_actions for later correlation with tool_result events. This
    enables action tracking and idle detection during phase execution.

    Args:
        event: Parsed JSON event from stream-json output.
               Expected structure for tool calls:
               {"type": "assistant", "message": {"content": [{"type": "tool_use", ...}]}}
        pending_actions: Mutable dict mapping tool_use_id to ActionRecord.
                        New tool uses are added here for correlation with results.

    Returns:
        List of new ActionRecords created from tool_use blocks in this event.
        Empty list if event is not an assistant message or has no tool calls.
    """
    actions = []
    if event.get("type") != "assistant":
        return actions

    message = event.get("message", {})
    content = message.get("content", [])

    for block in content:
        if block.get("type") == "tool_use":
            action = ActionRecord.from_tool_use(block)
            actions.append(action)
            # Track for correlation with tool_result
            pending_actions[action.tool_use_id] = action

    return actions


def update_action_from_result(
    event: dict,
    pending_actions: dict[str, ActionRecord]
) -> None:
    """Update pending actions with tool_result data from user message events.

    In Claude's conversation protocol, tool results are sent as user messages.
    This function correlates tool_result blocks with previously recorded
    tool_use actions via tool_use_id, updating the ActionRecord with the
    outcome (success/error) and a truncated output summary.

    Args:
        event: Parsed JSON event from stream-json output.
               Expected structure for tool results:
               {"type": "user", "message": {"content": [{"type": "tool_result", ...}]}}
        pending_actions: Mutable dict mapping tool_use_id to ActionRecord.
                        Matching entries are updated and removed after processing.

    Side Effects:
        - Updates ActionRecord.success based on is_error flag
        - Updates ActionRecord.output_summary with truncated result content
        - Removes processed actions from pending_actions dict
    """
    if event.get("type") != "user":
        return

    message = event.get("message", {})
    content = message.get("content", [])

    for block in content:
        if block.get("type") == "tool_result":
            tool_use_id = block.get("tool_use_id", "")
            if tool_use_id in pending_actions:
                action = pending_actions[tool_use_id]
                # Compute duration from start timestamp
                try:
                    start = datetime.fromisoformat(action.timestamp)
                    action.duration_ms = (datetime.now() - start).total_seconds() * 1000
                except (ValueError, TypeError):
                    pass
                # Check for error
                is_error = block.get("is_error", False)
                action.success = not is_error
                # Extract output summary
                result_content = block.get("content", "")
                if isinstance(result_content, list):
                    # Handle array of content blocks
                    text_parts = []
                    for part in result_content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                    result_content = "\n".join(text_parts)
                if isinstance(result_content, str):
                    # Truncate output summary
                    if len(result_content) > OUTPUT_SUMMARY_MAX_LENGTH:
                        action.output_summary = result_content[:OUTPUT_SUMMARY_MAX_LENGTH] + "..."
                    else:
                        action.output_summary = result_content
                    # Prefix with ERROR: if this was an error result
                    if is_error and not action.output_summary.startswith("ERROR:"):
                        action.output_summary = f"ERROR: {action.output_summary}"
                # Remove from pending after processing
                del pending_actions[tool_use_id]

