#!/usr/bin/env python3
"""Test that issue-agent reads inspect feedback on re-trigger."""

import json
import os
import tempfile
from pathlib import Path


def test_issue_agent_reads_feedback():
    """Verify issue-agent template includes feedback reading step."""
    template_path = Path("core/templates/agents/issue-agent.md.template")
    assert template_path.exists(), "issue-agent template not found"
    
    content = template_path.read_text()
    
    # Check for feedback reading step
    assert ".beads/inspect-feedback" in content, \
        "Template should reference .beads/inspect-feedback directory"
    assert "issue-{{ISSUE_NUMBER}}.json" in content or "issue-$" in content, \
        "Template should reference feedback file by issue number"
    
    # Check it's in the right place (before classification)
    lines = content.split("\n")
    feedback_line = None
    classify_line = None
    
    for i, line in enumerate(lines):
        if "inspect-feedback" in line.lower():
            feedback_line = i
        if "### Step 2: Classify" in line:
            classify_line = i
    
    assert feedback_line is not None, "Feedback reading not found in template"
    assert classify_line is not None, "Classification step not found"
    assert feedback_line < classify_line, \
        "Feedback reading should happen before classification"


def test_feedback_file_format():
    """Verify feedback file format is referenced in issue-agent template."""
    # The feedback file format is defined in inspect.md (T2 work)
    # This test just verifies the issue-agent knows to read it
    template_path = Path("core/templates/agents/issue-agent.md.template")
    content = template_path.read_text()
    
    # Check that issue-agent references the feedback structure
    assert "verdict" in content.lower(), "Template should reference verdict"
    assert "dimensions" in content.lower(), "Template should reference dimensions"
    assert "rationale" in content.lower(), "Template should reference rationale"


if __name__ == "__main__":
    test_issue_agent_reads_feedback()
    test_feedback_file_format()
    print("✓ All tests passed")
