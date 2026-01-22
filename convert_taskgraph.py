#!/usr/bin/env python3
"""
Task Graph to Beads Converter

Converts capsule-to-line-cook migration task graph to beads.

Usage:
    python convert_taskgraph.py

Reads task graph from CAPSULE_MIGRATION_PLAN.md and creates beads.
"""

import re
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, silent=False):
    """Run a shell command and return output."""
    if silent:
        cmd += " --silent"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running: {cmd}")
        print(f"stderr: {result.stderr}")
        return None
    return result.stdout.strip()

def parse_task_graph(filepath):
    """Parse the task graph from CAPSULE_MIGRATION_PLAN.md."""
    with open(filepath, 'r') as encoding='utf-8') as f:
        content = f.read()

    # Extract tasks using regex
    task_pattern = r'(\d+)\.\s+\*\*(.+?)\*\*\s*\((P[0-3]), depends on (.+?)\)\s*\n```([^`]+)```'
    tasks = re.findall(task_pattern, content, re.DOTALL)

    return tasks

def create_epic(title, priority, description):
    """Create an epic bead."""
    cmd = f'bd create --title="{title}" --type=epic --priority={priority} --description="{description}"'
    epic_id = run_cmd(cmd, silent=True)
    print(f"Created epic: {epic_id}")
    return epic_id

def create_feature(title, parent_id, priority, description):
    """Create a feature bead."""
    cmd = f'bd create --title="{title}" --type=feature --parent={parent_id} --priority={priority} --description="{description}"'
    feature_id = run_cmd(cmd, silent=True)
    print(f"Created feature: {feature_id}")
    return feature_id

def create_task(title, parent_id, priority, depends_on, description):
    """Create a task bead."""
    deps = ""
    if depends_on:
        deps = f' --deps={depends_on}'

    cmd = f'bd create --title="{title}" --type=task --parent={parent_id} --priority={priority}{deps} --description="{description}"'
    task_id = run_cmd(cmd, silent=True)
    print(f"Created task: {task_id}")
    return task_id

def main():
    print("Converting task graph to beads...")
    print()

    # Manual mapping based on task graph structure
    # Phase 1 Epics
    epic1_id = create_epic(
        "Phase 1: Core Workflow Enhancement",
        "1",
        "Enhance existing line-cook commands with capsule methodology."
    )

    epic2_id = create_epic(
        "Phase 2: Agent Subsystem",
        "1",
        "Define all subagents for automatic quality gates."
    )

    epic3_id = create_epic(
        "Phase 3: Documentation System",
        "2",
        "Create comprehensive guidance documentation with kitchen theming."
    )

    epic4_id = create_epic(
        "Phase 4: Integration and Documentation",
        "2",
        "Update core docs and integrate with OpenCode and Kiro."
    )

    epic5_id = create_epic(
        "Phase 5: Testing and Validation",
        "2",
        "Test all commands, agents, and workflow."
    )

    # Phase 1 Features
    feature1_1_id = create_feature(
        "Core Command Enhancement",
        epic1_id,
        "1",
        "Update prep, cook, serve, tidy, work commands."
    )

    feature1_2_id = create_feature(
        "New Command Creation",
        epic1_id,
        "1",
        "Create plan and dessert commands."
    )

    # Phase 2 Feature
    feature2_1_id = create_feature(
        "Subagent Definitions",
        epic2_id,
        "1",
        "Define chef, sous-chef, quality-control, sommelier, kitchen-manager agents."
    )

    # Phase 3 Features
    feature3_1_id = create_feature(
        "Guidance Documentation",
        epic3_id,
        "2",
        "Create 8 guidance docs with kitchen theming."
    )

    feature3_2_id = create_feature(
        "Testing Documentation",
        epic3_id,
        "2",
        "Create feature completion template."
    )

    # Phase 4 Features
    feature4_1_id = create_feature(
        "Core Documentation Updates",
        epic4_id,
        "1",
        "Update AGENTS.md, README.md, CHANGELOG.md."
    )

    feature4_2_id = create_feature(
        "OpenCode Integration",
        epic4_id,
        "2",
        "Update all 7 OpenCode commands."
    )

    feature4_3_id = create_feature(
        "Kiro Integration",
        epic4_id,
        "2",
        "Update Kiro skill and steering docs."
    )

    # Phase 5 Feature
    feature5_1_id = create_feature(
        "Integration Testing",
        epic5_id,
        "1",
        "Test all components end-to-end."
    )

    # Phase 1 Tasks (Core Command Enhancement)
    print("\nPhase 1 Tasks (Core Command Enhancement)")
    create_task(
        "Update cook command with TDD and quality-control integration",
        feature1_1_id,
        "1",
        "",
        "Add TDD cycle (RED-GREEN-REFACTOR) with automatic quality-control subagent delegation to commands/cook.md."
    )

    create_task(
        "Update serve command with automatic sous-chef review",
        feature1_1_id,
        "1",
        f"{feature1_1_id}.1",  # Depends on cook
        "Add automatic sous-chef (reviewer) subagent delegation to commands/serve.md."
    )

    create_task(
        "Update tidy command with kitchen log format",
        feature1_1_id,
        "1",
        f"{feature1_1_id}.1",  # Depends on cook
        "Update commands/tidy.md with kitchen log commit message format."
    )

    create_task(
        "Create plan command (recipe planning)",
        feature1_2_id,
        "1",
        "",
        "Create commands/plan.md from capsule mission-planning.md."
    )

    create_task(
        "Create dessert command (feature validation)",
        feature1_2_id,
        "1",
        f"{feature1_2_id}.1",  # Depends on plan
        "Create commands/dessert.md from capsule mission-complete.md."
    )

    create_task(
        "Update prep command with branching strategy",
        feature1_1_id,
        "1",
        f"{feature1_1_id}.1",  # Depends on cook
        "Add branching strategy check and kitchen manual loading to commands/prep.md."
    )

    create_task(
        "Update work command with kitchen-manager orchestration",
        feature1_1_id,
        "2",
        f"{feature1_1_id}.1,{feature1_1_id}.2,{feature1_1_id}.3,{feature1_1_id}.4",  # Depends on cook, serve, tidy, prep
        "Update commands/work.md as kitchen-manager orchestrator."
    )

    # Phase 2 Tasks (Agent Subsystem)
    print("\nPhase 2 Tasks (Agent Subsystem)")
    create_task(
        "Define quality-control agent (test-quality)",
        feature2_1_id,
        "1",
        f"{feature1_1_id}.1",  # Depends on cook
        "Create quality-control agent definition from capsule test-quality."
    )

    create_task(
        "Define sous-chef agent (reviewer)",
        feature2_1_id,
        "1",
        f"{feature1_1_id}.1",  # Depends on cook
        "Create sous-chef agent definition from capsule reviewer."
    )

    create_task(
        "Define sommelier agent (bdd-quality)",
        feature2_1_id,
        "2",
        f"{feature1_2_id}.1",  # Depends on dessert command
        "Create sommelier agent definition from capsule bdd-quality."
    )

    create_task(
        "Define chef agent (pilot)",
        feature2_1_id,
        "2",
        f"{feature2_1_id}.1",  # Depends on quality-control
        "Create chef agent definition from capsule pilot."
    )

    create_task(
        "Define kitchen-manager agent (orchestrator)",
        feature2_1_id,
        "2",
        f"{feature2_1_id}.3,{feature1_1_id}.5",  # Depends on chef and work command
        "Create kitchen-manager agent definition from capsule mission-orchestrator."
    )

    # Phase 3 Tasks (Documentation System)
    print("\nPhase 3 Tasks (Documentation System)")
    create_task(
        "Create workflow guidance (core work structure)",
        feature3_1_id,
        "2",
        "",
        "Create docs/guidance/workflow.md from capsule work-structure/README.md."
    )

    create_task(
        "Create tracer-dishes guidance",
        feature3_1_id,
        "2",
        f"{feature3_1_id}.1",  # Depends on workflow
        "Create docs/guidance/tracer-dishes.md from capsule tracer-bullets.md."
    )

    create_task(
        "Create test-prep guidance",
        feature3_1_id,
        "2",
        f"{feature3_1_id}.1",  # Depends on workflow
        "Create docs/guidance/test-prep.md from capsule test-writing/README.md."
    )

    create_task(
        "Create TDD/BDD integration guidance",
        feature3_1_id,
        "2",
        f"{feature3_1_id}.1,{feature3_1_id}.3",  # Depends on workflow and test-prep
        "Create docs/guidance/tdd-bdd.md from capsule work-structure/tdd-bdd.md."
    )

    create_task(
        "Create kitchen-logs guidance",
        feature3_1_id,
        "2",
        f"{feature3_1_id}.1",  # Depends on workflow
        "Create docs/guidance/kitchen-logs.md from capsule commit-messages.md."
    )

    create_task(
        "Create station-management guidance",
        feature3_1_id,
        "2",
        f"{feature3_1_id}.1",  # Depends on workflow
        "Create docs/guidance/station-management.md from capsule git-branching.md."
    )

    create_task(
        "Create menu-changes guidance",
        feature3_1_id,
        "3",
        f"{feature3_1_id}.1",  # Depends on workflow
        "Create docs/guidance/menu-changes.md from capsule changelog.md."
    )

    create_task(
        "Create order-priorities guidance",
        feature3_1_id,
        "3",
        f"{feature3_1_id}.1",  # Depends on workflow
        "Create docs/guidance/order-priorities.md from capsule work-structure/priorities.md."
    )

    create_task(
        "Create feature completion template",
        feature3_2_id,
        "2",
        f"{feature1_2_id}.1",  # Depends on dessert command
        "Create docs/testing/feature-completion-template.md from capsule feature-acceptance-template.md."
    )

    # Phase 4 Tasks (Integration and Documentation)
    print("\nPhase 4 Tasks (Integration and Documentation)")
    create_task(
        "Update AGENTS.md with enhanced workflow",
        feature4_1_id,
        "1",
        f"{feature1_1_id},{feature1_2_id},{feature2_1_id},{feature3_1_id}",  # Depends on all phase 1-3 features
        "Update AGENTS.md workflow section with enhanced commands and kitchen theming."
    )

    create_task(
        "Update README.md with new workflow",
        feature4_1_id,
        "2",
        f"{feature4_1_id}.1",  # Depends on AGENTS.md
        "Update README.md with enhanced workflow and kitchen terminology glossary."
    )

    create_task(
        "Update CHANGELOG.md",
        feature4_1_id,
        "3",
        f"{feature4_1_id}.1,{feature4_1_id}.2",  # Depends on AGENTS.md and README
        "Update CHANGELOG.md with all capsule migration features."
    )

    create_task(
        "Create/update OpenCode commands",
        feature4_2_id,
        "2",
        f"{feature4_1_id}.1",  # Depends on AGENTS.md
        "Update all 7 OpenCode commands to match enhanced Claude Code commands."
    )

    create_task(
        "Update Kiro skill and steering docs",
        feature4_3_id,
        "2",
        f"{feature4_1_id}.1,{feature4_1_id}.2",  # Depends on AGENTS.md and README
        "Update Kiro skill and steering docs to work with enhanced line-cook workflow."
    )

    # Phase 5 Tasks (Testing and Validation)
    print("\nPhase 5 Tasks (Testing and Validation)")
    create_task(
        "Test enhanced workflow cycle",
        feature5_1_id,
        "1",
        f"{feature1_1_id},{feature1_2_id},{feature2_1_id},{feature4_1_id},{feature4_2_id},{feature4_3_id}",  # Depends on all previous phases
        "Test full enhanced workflow cycle from plan through tidy."
    )

    create_task(
        "Test feature completion workflow",
        feature5_1_id,
        "1",
        f"{feature5_1_id}.1",  # Depends on enhanced workflow test
        "Test dessert service workflow for feature completion and documentation."
    )

    create_task(
        "Test agent delegation",
        feature5_1_id,
        "2",
        f"{feature5_1_id}.1",  # Depends on enhanced workflow test
        "Test all automatic agent delegations in workflow."
    )

    create_task(
        "Verify documentation consistency",
        feature5_1_id,
        "3",
        f"{feature5_1_id}.1,{feature5_1_id}.2,{feature5_1_id}.3,{feature3_1_id},{feature3_2_id}",  # Depends on all tests and docs
        "Audit all documentation for kitchen theming consistency and cross-reference accuracy."
    )

    print("\n" + "="*50)
    print("Task graph conversion complete!")
    print("Run 'bd ready' to see available work.")
    print("="*50)

if __name__ == "__main__":
    main()
