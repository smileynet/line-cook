#!/usr/bin/env python3
"""Test that issue-agent surfaces confidence score in Path B."""

from pathlib import Path


def test_confidence_assessment_step_exists():
    """Verify issue-agent template includes confidence assessment."""
    template_path = Path("core/templates/agents/issue-agent.md.template")
    assert template_path.exists(), "issue-agent template not found"
    
    content = template_path.read_text()
    
    # Check for confidence assessment step (should be between Step 4 and Step 5)
    assert "confidence" in content.lower(), \
        "Template should include confidence assessment"
    
    lines = content.split("\n")
    step4_line = None
    step5_line = None
    confidence_line = None
    
    for i, line in enumerate(lines):
        if "### Step 4:" in line:
            step4_line = i
        if "### Step 5:" in line:
            step5_line = i
        if "confidence" in line.lower() and "###" in line:
            confidence_line = i
    
    assert step4_line is not None, "Step 4 not found"
    assert step5_line is not None, "Step 5 not found"
    assert confidence_line is not None, "Confidence assessment step not found"
    assert step4_line < confidence_line < step5_line, \
        "Confidence assessment should be between Step 4 and Step 5"


def test_path_b_includes_confidence():
    """Verify Path B comment template includes confidence indicator."""
    template_path = Path("core/templates/agents/issue-agent.md.template")
    content = template_path.read_text()
    
    # Find Path B comment section
    lines = content.split("\n")
    path_b_start = None
    
    for i, line in enumerate(lines):
        if "**Path B" in line and "no fix" in line.lower():
            path_b_start = i
            break
    
    assert path_b_start is not None, "Path B comment template not found"
    
    # Check next 30 lines for confidence indicator
    path_b_section = "\n".join(lines[path_b_start:path_b_start + 30])
    
    assert "confidence" in path_b_section.lower(), \
        "Path B comment should include confidence indicator"
    assert "**" in path_b_section, \
        "Path B comment should use markdown formatting for confidence"


def test_confidence_levels_defined():
    """Verify confidence levels are clearly defined."""
    template_path = Path("core/templates/agents/issue-agent.md.template")
    content = template_path.read_text()
    
    # Should define what HIGH/MEDIUM/LOW confidence means
    content_lower = content.lower()
    
    # At minimum, should mention different confidence levels
    assert "high" in content_lower or "low" in content_lower, \
        "Template should define confidence levels"
