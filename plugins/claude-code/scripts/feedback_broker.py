#!/usr/bin/env python3
"""Feedback broker - synthesizes feedback from multiple agents."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def read_inspect_feedback(repo_root: Path, issue_number: int) -> Optional[dict[str, Any]]:
    """Read inspect feedback for a given issue number."""
    feedback_file = repo_root / ".beads" / "inspect-feedback" / f"issue-{issue_number}.json"

    if not feedback_file.exists():
        return None

    try:
        return json.loads(feedback_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def read_loop_feedback(repo_root: Path, task_id: str) -> Optional[dict[str, Any]]:
    """Read loop feedback for a given task ID.

    The loop writes retry context to .line-cook/retry-context.json (a single
    file, not per-task).  We also check the legacy per-task path under
    .beads/loop-feedback/ for backwards compatibility.
    """
    # Primary: single retry-context file written by the loop
    retry_file = repo_root / ".line-cook" / "retry-context.json"
    if retry_file.exists():
        try:
            data = json.loads(retry_file.read_text())
        except (json.JSONDecodeError, OSError):
            data = None
        if data is not None and data.get("task_id") == task_id:
            return data

    # Fallback: per-task feedback file (used by tests and future writers)
    feedback_file = repo_root / ".beads" / "loop-feedback" / f"{task_id}.json"
    if feedback_file.exists():
        try:
            return json.loads(feedback_file.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    return None


def find_inspect_feedback_by_pr(repo_root: Path, pr_number: int) -> Optional[dict[str, Any]]:
    """Scan inspect feedback files to find one matching a PR number."""
    feedback_dir = repo_root / ".beads" / "inspect-feedback"
    if not feedback_dir.is_dir():
        return None

    for feedback_file in feedback_dir.glob("issue-*.json"):
        try:
            data = json.loads(feedback_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("pr_number") == pr_number:
            return data

    return None


def read_issue_agent_feedback(repo_root: Path, issue_number: int) -> Optional[dict[str, Any]]:
    """Read issue-agent feedback for a given issue number."""
    feedback_file = repo_root / ".beads" / "issue-agent-feedback" / f"issue-{issue_number}.json"

    if not feedback_file.exists():
        return None

    try:
        return json.loads(feedback_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def synthesize_feedback(
    repo_root: Path,
    issue_number: Optional[int] = None,
    task_id: Optional[str] = None,
    pr_number: Optional[int] = None
) -> dict[str, Any]:
    """Synthesize feedback from multiple sources into a unified view."""
    feedback_sources = {}

    # Determine context type and ID (use `is not None` to handle zero values)
    if issue_number is not None:
        context_type = "issue"
        context_id = str(issue_number)

        # Read inspect feedback
        inspect = read_inspect_feedback(repo_root, issue_number)
        if inspect:
            feedback_sources["inspect"] = inspect

        # Read issue-agent feedback
        issue_agent = read_issue_agent_feedback(repo_root, issue_number)
        if issue_agent:
            feedback_sources["issue_agent"] = issue_agent

    elif task_id is not None:
        context_type = "task"
        context_id = task_id

        # Read loop feedback
        loop = read_loop_feedback(repo_root, task_id)
        if loop:
            feedback_sources["loop"] = loop

    elif pr_number is not None:
        context_type = "pr"
        context_id = str(pr_number)

        # Cross-reference: scan inspect feedback for matching PR number
        inspect = find_inspect_feedback_by_pr(repo_root, pr_number)
        if inspect:
            feedback_sources["inspect"] = inspect

    else:
        raise ValueError("Must provide issue_number, task_id, or pr_number")

    # Synthesize summary
    total_count = len(feedback_sources)
    latest_verdict = None
    escalation_needed = False
    key_concerns = []

    # Extract latest verdict and check for escalation
    if "inspect" in feedback_sources:
        inspect = feedback_sources["inspect"]
        latest_verdict = inspect.get("verdict")

        # Check for escalation (3+ polish attempts)
        if inspect.get("polish_attempts", 0) >= 3:
            escalation_needed = True

        # Extract key concerns from dimensions
        dimensions = inspect.get("dimensions", {})
        for key, value in dimensions.items():
            if "needs" in value.lower() or "concern" in value.lower():
                key_concerns.append(key)

    if "loop" in feedback_sources:
        loop = feedback_sources["loop"]
        if not latest_verdict:
            latest_verdict = loop.get("verdict")

    return {
        "context_type": context_type,
        "context_id": context_id,
        "feedback_sources": feedback_sources,
        "summary": {
            "total_feedback_count": total_count,
            "latest_verdict": latest_verdict,
            "escalation_needed": escalation_needed,
            "key_concerns": key_concerns
        },
        "synthesized_at": datetime.now().isoformat()
    }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Feedback broker - synthesize agent feedback")
    parser.add_argument("--issue", type=int, help="Issue number")
    parser.add_argument("--task", type=str, help="Task ID")
    parser.add_argument("--pr", type=int, help="PR number")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root")

    args = parser.parse_args()

    if args.issue is None and args.task is None and args.pr is None:
        parser.error("Must provide --issue, --task, or --pr")

    unified = synthesize_feedback(
        args.repo,
        issue_number=args.issue,
        task_id=args.task,
        pr_number=args.pr
    )

    print(json.dumps(unified, indent=2))


if __name__ == "__main__":
    main()
