#!/bin/bash
# Menu Plan to Beads Converter
#
# Converts menu plan YAML to beads issues using the `bd` CLI.
# Also generates BDD feature specs and TDD test specs.
#
# Usage:
#   ./scripts/menu-plan-to-beads.sh docs/planning/menu-plan.yaml
#
# Outputs:
#   - Beads in .beads/
#   - BDD specs in tests/features/*.feature
#   - TDD specs in tests/specs/*.md

set -e

MENU_PLAN_FILE="${1:-docs/planning/menu-plan.yaml}"

if [ ! -f "$MENU_PLAN_FILE" ]; then
    echo "Error: Menu plan file not found: $MENU_PLAN_FILE"
    echo "Usage: $0 <menu-plan.yaml>"
    exit 1
fi

echo "Converting menu plan to beads and test specs..."
echo "Menu plan: $MENU_PLAN_FILE"
echo

# Track created IDs for dependency linking
declare -A PHASE_IDS
declare -A FEATURE_IDS
declare -A TASK_IDS

# Parse YAML and create beads
# Note: This is a simplified parser using Python for YAML parsing
python3 - <<PYTHON_SCRIPT
import yaml
import subprocess
import sys
import os
import re
from pathlib import Path

menu_plan_file = Path("$MENU_PLAN_FILE")

if not menu_plan_file.exists():
    print(f"Error: Menu plan file not found: {menu_plan_file}")
    sys.exit(1)

with open(menu_plan_file, 'r') as f:
    menu_plan = yaml.safe_load(f)

def run_bd_cmd(cmd):
    """Run a bd command and return the output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running: {cmd}")
        print(f"stderr: {result.stderr}")
        return None
    # Extract bead ID from output (typically last line or specific format)
    output = result.stdout.strip()
    # Try to extract ID like "lc-abc"
    match = re.search(r'lc-[a-z0-9]+', output)
    if match:
        return match.group(0)
    return output

def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def ensure_dir(path):
    """Ensure directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)

# Track created beads
phases = {}
features = {}
tasks = {}

# Track test specs
feature_specs = []
task_specs = []

# Create phases (epics)
print("Creating phases (epics)...")
for phase in menu_plan.get('phases', []):
    phase_id = phase['id']
    title = phase['title']
    description = phase.get('description', '')
    priority = 1  # Default priority for epics

    cmd = f'bd create --title="{title}" --type=epic --priority={priority} --description="{description}"'
    bead_id = run_bd_cmd(cmd)
    if bead_id:
        phases[phase_id] = bead_id
        print(f"  Created epic: {bead_id} - {title}")
    else:
        print(f"  Failed to create epic: {title}")

print()

# Create features
print("Creating features...")
for phase in menu_plan.get('phases', []):
    phase_id = phase['id']
    epic_id = phases.get(phase_id)

    if not epic_id:
        print(f"  Warning: Epic {phase_id} not found, skipping features")
        continue

    for feature in phase.get('features', []):
        feature_id = feature['id']
        title = feature['title']
        user_story = feature.get('user_story', '')
        acceptance_criteria = feature.get('acceptance_criteria', [])
        priority = feature.get('priority', 2)

        # Build description with user story and acceptance criteria
        desc_lines = [user_story] if user_story else []
        if acceptance_criteria:
            desc_lines.append("Acceptance Criteria:")
            for i, ac in enumerate(acceptance_criteria, 1):
                desc_lines.append(f"{i}. {ac}")
        description = '\\n'.join(desc_lines)

        cmd = f'bd create --title="{title}" --type=feature --parent={epic_id} --priority={priority} --description="{description}"'
        bead_id = run_bd_cmd(cmd)
        if bead_id:
            features[feature_id] = bead_id
            print(f"  Created feature: {bead_id} - {title}")

            # Track for BDD spec generation
            feature_specs.append({
                'id': feature_id,
                'bead_id': bead_id,
                'title': title,
                'user_story': user_story,
                'acceptance_criteria': acceptance_criteria
            })

            # Add feature dependencies (blocks)
            blocks = feature.get('blocks', [])
            for blocked_feature_id in blocks:
                if blocked_feature_id in features:
                    blocked_id = features[blocked_feature_id]
                    print(f"    Feature {bead_id} blocks {blocked_id}")
                    # Note: beads doesn't have a "blocks" command, this is for documentation
                else:
                    print(f"    Warning: Blocked feature {blocked_feature_id} not found yet")
        else:
            print(f"  Failed to create feature: {title}")

print()

# Create tasks
print("Creating tasks (courses)...")
for phase in menu_plan.get('phases', []):
    for feature in phase.get('features', []):
        feature_id = feature['id']
        parent_id = features.get(feature_id)

        if not parent_id:
            print(f"  Warning: Feature {feature_id} not found, skipping tasks")
            continue

        for task in feature.get('tasks', []):
            title = task['title']
            tracer = task.get('tracer', '')
            description = task.get('description', '')
            deliverable = task.get('deliverable', '')
            priority = task.get('priority', 1)
            depends_on_titles = task.get('depends_on', [])
            tdd = task.get('tdd', False)

            # Build description with tracer, deliverable, and details
            desc_lines = []
            if tracer:
                desc_lines.append(f"Tracer: {tracer}")
            if description:
                desc_lines.append(description.strip())
            if deliverable:
                desc_lines.append(f"Deliverable: {deliverable}")

            full_description = '\\n'.join(desc_lines)

            cmd = f'bd create --title="{title}" --type=task --parent={parent_id} --priority={priority} --description="{full_description}"'
            bead_id = run_bd_cmd(cmd)
            if bead_id:
                tasks[title] = bead_id
                print(f"  Created task: {bead_id} - {title}")

                # Track for TDD spec generation
                if tdd:
                    task_specs.append({
                        'title': title,
                        'bead_id': bead_id,
                        'tracer': tracer,
                        'description': description,
                        'deliverable': deliverable
                    })
            else:
                print(f"  Failed to create task: {title}")

print()

# Add task dependencies
print("Adding task dependencies...")
for phase in menu_plan.get('phases', []):
    for feature in phase.get('features', []):
        for task in feature.get('tasks', []):
            title = task['title']
            task_id = tasks.get(title)
            depends_on_titles = task.get('depends_on', [])

            if task_id and depends_on_titles:
                for dep_title in depends_on_titles:
                    dep_id = tasks.get(dep_title)
                    if dep_id:
                        cmd = f'bd dep add {task_id} {dep_id}'
                        result = run_bd_cmd(cmd)
                        if result:
                            print(f"  {task_id} depends on {dep_id}")
                    else:
                        print(f"  Warning: Dependency task '{dep_title}' not found for '{title}'")

print()

# Generate BDD feature specs (Gherkin)
print("Generating BDD feature specs...")
ensure_dir('tests/features')

for spec in feature_specs:
    if not spec['acceptance_criteria']:
        print(f"  Skipping {spec['id']} - no acceptance criteria")
        continue

    filename = f"tests/features/{spec['id']}-{slugify(spec['title'])}.feature"

    # Parse user story for Gherkin format
    user_story = spec['user_story']
    role = 'user'
    action = 'perform the action'
    benefit = 'achieve the goal'

    # Try to parse "As a X, I want Y so that Z" format
    story_match = re.match(r'As an? ([^,]+),\s*I want (?:to )?(.+?)\s*so that (.+)', user_story, re.IGNORECASE)
    if story_match:
        role = story_match.group(1).strip()
        action = story_match.group(2).strip()
        benefit = story_match.group(3).strip()

    # Clean title for feature name
    feature_title = spec['title']
    if ':' in feature_title:
        feature_title = feature_title.split(':', 1)[1].strip()

    content = f"""# {spec['bead_id']} - {spec['title']}
Feature: {feature_title}
  As a {role}
  I want to {action}
  So that {benefit}

  Background:
    Given the system is in a known state

"""

    for i, criterion in enumerate(spec['acceptance_criteria'], 1):
        # Create scenario name from criterion
        scenario_name = criterion.strip()
        if scenario_name.startswith('Can '):
            scenario_name = scenario_name[4:]
        scenario_name = scenario_name[0].upper() + scenario_name[1:]

        content += f"""  Scenario: {scenario_name}
    Given the preconditions are met
    When the action is performed
    Then {criterion.lower()}

"""

    with open(filename, 'w') as f:
        f.write(content)

    print(f"  Created: {filename}")

print()

# Generate TDD test specs
print("Generating TDD test specs...")
ensure_dir('tests/specs')

for spec in task_specs:
    filename = f"tests/specs/{slugify(spec['title'])}.md"

    content = f"""# Test Specification: {spec['title']}

**Bead:** {spec['bead_id']}

## Tracer

{spec['tracer'] or 'No tracer strategy defined.'}

## Context

{spec['description'] or 'No description provided.'}

**Deliverable:** {spec['deliverable'] or 'Not specified.'}

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| TODO | TODO | Define based on tracer strategy |

## Edge Cases

- [ ] Define edge cases based on implementation
- [ ] Consider error conditions
- [ ] Consider boundary values

## Implementation Notes

These specs will be translated to language-specific tests during /cook RED phase.

Reference the tracer strategy to determine:
1. What minimal test proves the layer works?
2. What would be the simplest way to verify success?
3. What's the first thing that could go wrong?
"""

    with open(filename, 'w') as f:
        f.write(content)

    print(f"  Created: {filename}")

print()
print("="*60)
print("Menu plan conversion complete!")
print("="*60)
print()
print("Summary:")
print(f"  Phases (epics): {len(phases)}")
print(f"  Features: {len(features)}")
print(f"  Tasks: {len(tasks)}")
print(f"  BDD specs: {len([s for s in feature_specs if s['acceptance_criteria']])}")
print(f"  TDD specs: {len(task_specs)}")
print()
print("Artifacts created:")
print("  - .beads/ (beads)")
print("  - tests/features/*.feature (BDD specs)")
print("  - tests/specs/*.md (TDD specs)")
print()
print("Next steps:")
print("  1. Review beads: bd list")
print("  2. Check hierarchy: bd show <epic-id>")
print("  3. Verify dependencies: bd ready")
print("  4. Review test specs: ls tests/features/ tests/specs/")
print("  5. Sync to git: bd sync && git add .beads/ tests/ && git commit")
PYTHON_SCRIPT
