#!/usr/bin/env python3
"""Install line-cook for Kiro CLI.

Usage:
    ./install.py [--global | --local]
    ./install.py --version

Options:
    --global   Install to ~/.kiro/ (default)
    --local    Install to .kiro/ in current directory
    --version  Print version and exit
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

VERSION = "0.14.0"


def main() -> None:
    parser = argparse.ArgumentParser(description="Install line-cook for Kiro CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=f"line-cook v{VERSION} (Kiro)",
    )
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
        print(f"Installing line-cook v{VERSION} for Kiro CLI (global)...")
        # Warn if local .kiro/ would shadow global install
        local_kiro = Path.cwd() / ".kiro"
        if local_kiro.is_dir():
            print()
            print(f"  ⚠  Local .kiro/ directory detected at {local_kiro}")
            print("     Local installations take precedence over global. Consider:")
            print(f"     - Remove local: rm -rf {local_kiro}")
            print("     - Or re-run with --local")
            print()
    else:
        kiro_dir = Path(".kiro")
        print(f"Installing line-cook v{VERSION} for Kiro CLI (local)...")

    # Create directories
    (kiro_dir / "agents").mkdir(parents=True, exist_ok=True)
    (kiro_dir / "steering").mkdir(parents=True, exist_ok=True)
    (kiro_dir / "skills" / "line-cook").mkdir(parents=True, exist_ok=True)
    (kiro_dir / "scripts").mkdir(parents=True, exist_ok=True)
    (kiro_dir / "prompts").mkdir(parents=True, exist_ok=True)

    # Path transformer for global install (converts .kiro/ to absolute paths)
    if args.global_install:
        home_kiro = str(Path.home() / ".kiro")

        def transform_path(obj):
            """Transform .kiro/ paths to absolute paths for global install.
            Use full path instead of ~ because skill:// URIs don't expand tilde."""
            if isinstance(obj, str):
                return obj.replace(".kiro/", f"{home_kiro}/")
            if isinstance(obj, list):
                return [transform_path(item) for item in obj]
            if isinstance(obj, dict):
                return {k: transform_path(v) for k, v in obj.items()}
            return obj
    else:
        def transform_path(obj):
            return obj

    # Copy agent configurations
    agents_src = script_dir / "agents"
    agent_files = sorted(agents_src.glob("*.json"))
    if not agent_files:
        sys.exit(f"Error: No agent JSON files found in {agents_src}")
    print(f"Installing agent configurations ({len(agent_files)} agents)...")
    for agent_file in agent_files:
        try:
            with open(agent_file) as f:
                agent_config = json.load(f)
        except json.JSONDecodeError as e:
            sys.exit(f"Error: Invalid JSON in {agent_file}: {e}")

        agent_config = transform_path(agent_config)
        agent_dst = kiro_dir / "agents" / agent_file.name
        with open(agent_dst, "w") as f:
            json.dump(agent_config, f, indent=2)
            f.write("\n")

    # Copy steering files
    steering_src = script_dir / "steering"
    steering_files = list(steering_src.glob("*.md"))
    if steering_files:
        print("Installing steering files...")
        for md_file in steering_files:
            shutil.copy(md_file, kiro_dir / "steering" / md_file.name)
    else:
        print("  Warning: No steering files found")

    # Copy skills
    print("Installing skills...")
    skill_src = script_dir / "skills" / "line-cook" / "SKILL.md"
    if skill_src.exists():
        shutil.copy(skill_src, kiro_dir / "skills" / "line-cook" / "SKILL.md")
    else:
        print("  Warning: SKILL.md not found")

    # Copy prompts
    prompts_src = script_dir / "prompts"
    if prompts_src.exists():
        prompt_files = list(prompts_src.glob("*.md"))
        if prompt_files:
            print("Installing prompts...")
            for prompt_file in prompt_files:
                shutil.copy(prompt_file, kiro_dir / "prompts" / prompt_file.name)
        else:
            print("  Warning: No prompt files found")
    else:
        print("  Warning: prompts directory not found")

    # Copy hook scripts (supports both .sh and .py scripts)
    scripts_src = script_dir / "scripts"
    if scripts_src.exists():
        hook_scripts = list(scripts_src.glob("*.sh")) + list(scripts_src.glob("*.py"))
        if hook_scripts:
            print("Installing hook scripts...")
            for script in hook_scripts:
                script_dst = kiro_dir / "scripts" / script.name
                shutil.copy(script, script_dst)
                script_dst.chmod(script_dst.stat().st_mode | 0o100)  # Make executable (user only)

    print()
    print("Installation complete!")
    print()
    print(f"Installed to: {kiro_dir}")
    print()
    print("Files installed:")
    for agent_file in agent_files:
        print(f"  agents/{agent_file.name}")
    print("  steering/*.md              - Workflow instructions")
    print("  skills/line-cook/SKILL.md  - Lazy-loaded documentation")
    prompt_count = len(list((kiro_dir / "prompts").glob("*.md")))
    print(f"  prompts/line-*.md          - {prompt_count} @prompt invocations")
    print()
    print("Next steps:")
    print("  1. Start Kiro CLI with: kiro-cli --agent line-cook")
    print("  2. Use @line-prep, @line-cook, etc. or natural language")
    print()
    print("Available @prompts:")
    print("  @line-brainstorm      - Explore problem space")
    print("  @line-scope           - Structure work breakdown")
    print("  @line-finalize        - Convert plan to beads")
    print("  @line-mise            - Full planning (brainstorm→scope→finalize)")
    print("  @line-prep            - Sync state, show ready tasks")
    print("  @line-cook            - Execute task with TDD cycle")
    print("  @line-serve           - Review changes")
    print("  @line-tidy            - Commit and push")
    print("  @line-plate           - Validate feature")
    print("  @line-close-service   - Validate and close epic")
    print("  @line-run             - Full workflow cycle")
    print("  @line-decision        - Manage architecture decisions")
    print("  @line-architecture-audit - Audit codebase architecture")
    print("  @line-plan-audit      - Audit planning quality")
    print("  @line-help            - Show help")
    print("  @line-loop            - Manage autonomous loop")
    print("  @line-getting-started - Show workflow guide")


if __name__ == "__main__":
    main()
