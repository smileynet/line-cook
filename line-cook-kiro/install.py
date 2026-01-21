#!/usr/bin/env python3
"""Install line-cook for Kiro CLI.

Usage:
    ./install.py [--global | --local]

Options:
    --global  Install to ~/.kiro/ (default)
    --local   Install to .kiro/ in current directory
"""

import argparse
import json
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Install line-cook for Kiro CLI")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        default=True,
        help="Install to ~/.kiro/ (default)",
    )
    group.add_argument(
        "--local",
        dest="global_install",
        action="store_false",
        help="Install to .kiro/ in current directory",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()

    if args.global_install:
        kiro_dir = Path.home() / ".kiro"
        print("Installing line-cook for Kiro CLI (global)...")
    else:
        kiro_dir = Path(".kiro")
        print("Installing line-cook for Kiro CLI (local)...")

    # Create directories
    (kiro_dir / "agents").mkdir(parents=True, exist_ok=True)
    (kiro_dir / "steering").mkdir(parents=True, exist_ok=True)
    (kiro_dir / "skills" / "line-cook").mkdir(parents=True, exist_ok=True)
    (kiro_dir / "scripts").mkdir(parents=True, exist_ok=True)

    # Copy agent configuration
    print("Installing agent configuration...")
    agent_src = script_dir / "agents" / "line-cook.json"
    agent_dst = kiro_dir / "agents" / "line-cook.json"

    # Load, transform paths if global, and save
    with open(agent_src) as f:
        agent_config = json.load(f)

    if args.global_install:
        # Transform .kiro/ paths to ~/.kiro/ for global install
        def transform_path(obj):
            if isinstance(obj, str):
                return obj.replace(".kiro/", "~/.kiro/")
            elif isinstance(obj, list):
                return [transform_path(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: transform_path(v) for k, v in obj.items()}
            return obj

        agent_config = transform_path(agent_config)

    with open(agent_dst, "w") as f:
        json.dump(agent_config, f, indent=2)
        f.write("\n")

    # Copy steering files
    print("Installing steering files...")
    steering_src = script_dir / "steering"
    for md_file in steering_src.glob("*.md"):
        shutil.copy(md_file, kiro_dir / "steering" / md_file.name)

    # Copy skills
    print("Installing skills...")
    skill_src = script_dir / "skills" / "line-cook" / "SKILL.md"
    if skill_src.exists():
        shutil.copy(skill_src, kiro_dir / "skills" / "line-cook" / "SKILL.md")

    # Copy hook scripts
    scripts_src = script_dir / "scripts"
    if scripts_src.exists():
        scripts = list(scripts_src.glob("*.sh")) + list(scripts_src.glob("*.py"))
        if scripts:
            print("Installing hook scripts...")
            for script in scripts:
                dst = kiro_dir / "scripts" / script.name
                shutil.copy(script, dst)
                dst.chmod(dst.stat().st_mode | 0o111)  # Make executable

    print()
    print("Installation complete!")
    print()
    print(f"Installed to: {kiro_dir}")
    print()
    print("Files installed:")
    print("  agents/line-cook.json      - Agent configuration")
    print("  steering/line-cook.md      - Workflow instructions")
    print("  steering/beads.md          - Beads quick reference")
    print("  steering/session.md        - Session protocols")
    print("  skills/line-cook/SKILL.md  - Lazy-loaded documentation")
    print()
    print("Next steps:")
    print("  1. Start Kiro CLI with: kiro-cli --agent line-cook")
    print("  2. Say 'prep' or 'work' to start the workflow")
    print()
    print("Note: Hooks are configured but hook scripts are stubs.")
    print("The workflow commands work without hooks.")


if __name__ == "__main__":
    main()
