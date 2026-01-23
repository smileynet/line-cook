#!/bin/bash
# Menu Plan to Beads Converter
#
# Converts menu plan YAML to beads issues using the `bd` CLI.
#
# Usage:
#   ./scripts/menu-plan-to-beads.sh docs/planning/menu-plan.yaml

set -e

MENU_PLAN_FILE="${1:-docs/planning/menu-plan.yaml}"

if [ ! -f "$MENU_PLAN_FILE" ]; then
    echo "Error: Menu plan file not found: $MENU_PLAN_FILE"
    echo "Usage: $0 <menu-plan.yaml>"
    exit 1
fi

echo "Converting menu plan to beads..."
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
    import re
    match = re.search(r'lc-[a-z0-9]+', output)
    if match:
        return match.group(0)
    return output

# Track created beads
phases = {}
features = {}
tasks = {}

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
print("="*60)
print("Menu plan conversion complete!")
print("="*60)
print()
print("Summary:")
print(f"  Phases (epics): {len(phases)}")
print(f"  Features: {len(features)}")
print(f"  Tasks: {len(tasks)}")
print()
print("Next steps:")
echo "  1. Review beads: bd list"
echo "  2. Check hierarchy: bd show <epic-id>"
echo "  3. Verify dependencies: bd ready"
echo "  4. Sync to git: bd sync && git add .beads/ && git commit"
PYTHON_SCRIPT
