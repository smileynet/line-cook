#!/usr/bin/env python3
"""
release.py - Automate mechanical steps of releasing a new line-cook version.

Handles version sync, CHANGELOG transformation, validation, and commit creation.
Preserves human judgment for content quality - the script only handles mechanics.

Usage:
    ./dev/release.py 0.8.2              # Prepare release (interactive)
    ./dev/release.py 0.8.2 --push       # Prepare + push (triggers GH release)
    ./dev/release.py 0.8.2 --dry-run    # Show what would change, no modifications
    ./dev/release.py --check            # Validate current state only
    ./dev/release.py --bundle           # Bundle line_loop only (for dev testing)

Exit codes:
    0: Success
    1: Pre-flight check failed
    2: Version update failed
    3: CHANGELOG update failed
    4: Bundling failed
    5: Validation failed
    6: Commit failed
    7: Push failed
"""

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

# Module dependency order for bundling line_loop package
LINE_LOOP_MODULES = ["config", "models", "parsing", "phase", "iteration", "loop"]


# ANSI colors for terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def color(text: str, color_code: str) -> str:
    """Wrap text in ANSI color codes."""
    return f"{color_code}{text}{Colors.ENDC}"


@dataclass
class PreflightResult:
    """Result of pre-flight checks."""
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ReleaseConfig:
    """Configuration for a release."""
    version: str
    dry_run: bool = False
    push: bool = False
    yes: bool = False
    repo_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    previous_version: Optional[str] = None  # Set before updating versions


def run_git(args: list[str], capture: bool = True) -> tuple[int, str]:
    """Run a git command and return exit code and output."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=capture,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    return result.returncode, result.stdout.strip() if capture else ""


def get_current_version(repo_root: Path) -> Optional[str]:
    """Get current version from plugin.json."""
    plugin_path = repo_root / "plugins" / "claude-code" / ".claude-plugin" / "plugin.json"
    if not plugin_path.exists():
        return None
    try:
        data = json.loads(plugin_path.read_text())
        return data.get("version")
    except (json.JSONDecodeError, KeyError):
        return None


def parse_version(version: str) -> tuple[int, ...]:
    """Parse semver string into tuple of ints for comparison."""
    return tuple(int(x) for x in version.split("."))


def version_is_newer(new_version: str, current_version: str) -> bool:
    """Check if new_version > current_version using semver comparison."""
    try:
        return parse_version(new_version) > parse_version(current_version)
    except (ValueError, AttributeError):
        return False


def git_working_tree_clean() -> bool:
    """Check if git working tree is clean."""
    code, output = run_git(["status", "--porcelain"])
    return code == 0 and output == ""


def on_main_branch() -> bool:
    """Check if on main branch."""
    code, output = run_git(["branch", "--show-current"])
    return code == 0 and output == "main"


def up_to_date_with_remote() -> bool:
    """Check if local main is up to date with origin/main."""
    # Fetch first
    run_git(["fetch", "origin", "main"], capture=False)

    # Compare HEAD with origin/main
    code, local = run_git(["rev-parse", "HEAD"])
    if code != 0:
        return False

    code, remote = run_git(["rev-parse", "origin/main"])
    if code != 0:
        return False

    return local == remote


def changelog_has_unreleased_content(repo_root: Path) -> bool:
    """Check if CHANGELOG has content in [Unreleased] section."""
    changelog_path = repo_root / "CHANGELOG.md"
    if not changelog_path.exists():
        return False

    content = changelog_path.read_text()

    # Find [Unreleased] section and check if it has content before next version
    unreleased_match = re.search(
        r"## \[Unreleased\]\s*\n(.*?)(?=## \[\d+\.\d+\.\d+\]|\Z)",
        content,
        re.DOTALL
    )

    if not unreleased_match:
        return False

    unreleased_content = unreleased_match.group(1).strip()
    # Check if there's actual content (not just whitespace)
    return len(unreleased_content) > 0


def preflight_checks(config: ReleaseConfig) -> PreflightResult:
    """Run all pre-flight checks."""
    result = PreflightResult(passed=True)

    # Git state checks
    if not git_working_tree_clean():
        result.errors.append("Working tree not clean. Commit or stash changes.")
        result.passed = False

    if not on_main_branch():
        result.errors.append("Not on main branch.")
        result.passed = False

    if not up_to_date_with_remote():
        result.errors.append("Local main behind origin/main. Pull first.")
        result.passed = False

    # Version validation
    current = get_current_version(config.repo_root)
    if current is None:
        result.errors.append("Could not read current version from plugin.json")
        result.passed = False
    elif not version_is_newer(config.version, current):
        result.errors.append(f"Version {config.version} not newer than {current}")
        result.passed = False

    # Changelog check
    if not changelog_has_unreleased_content(config.repo_root):
        result.errors.append("CHANGELOG [Unreleased] section is empty")
        result.passed = False

    return result


def update_json_file(file_path: Path, updates: dict[str, str], dry_run: bool = False) -> bool:
    """Update version fields in a JSON file.

    Args:
        file_path: Path to JSON file
        updates: Dict mapping JSON path to new value (e.g., {"version": "0.8.2", "opencode.version": "0.8.2"})
        dry_run: If True, don't actually write changes

    Returns:
        True if successful
    """
    try:
        data = json.loads(file_path.read_text())

        for path, value in updates.items():
            keys = path.split(".")
            obj = data
            for key in keys[:-1]:
                obj = obj[key]
            obj[keys[-1]] = value

        if not dry_run:
            # Preserve formatting with 2-space indent
            file_path.write_text(json.dumps(data, indent=2) + "\n")

        return True
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"  {color('✗', Colors.RED)} Error updating {file_path}: {e}")
        return False


def update_versions(config: ReleaseConfig) -> bool:
    """Update version in all required files."""
    success = True

    # Update plugin.json
    plugin_path = config.repo_root / "plugins" / "claude-code" / ".claude-plugin" / "plugin.json"
    if update_json_file(plugin_path, {"version": config.version}, config.dry_run):
        print(f"  {color('✓', Colors.GREEN)} plugins/claude-code/.claude-plugin/plugin.json")
    else:
        success = False

    # Update package.json (two locations)
    package_path = config.repo_root / "plugins" / "opencode" / "package.json"
    if update_json_file(package_path, {
        "version": config.version,
        "opencode.version": config.version
    }, config.dry_run):
        print(f"  {color('✓', Colors.GREEN)} plugins/opencode/package.json (2 locations)")
    else:
        success = False

    return success


def update_changelog(config: ReleaseConfig) -> bool:
    """Update CHANGELOG.md with new version section."""
    changelog_path = config.repo_root / "CHANGELOG.md"

    try:
        content = changelog_path.read_text()
        today = date.today().isoformat()

        # Replace [Unreleased] content with new version section
        # Pattern: ## [Unreleased]\n<content>\n## [X.Y.Z]
        pattern = r"(## \[Unreleased\])\s*\n"
        replacement = f"## [Unreleased]\n\n## [{config.version}] - {today}\n"

        new_content = re.sub(pattern, replacement, content, count=1)

        if new_content == content:
            print(f"  {color('✗', Colors.RED)} Could not find [Unreleased] section")
            return False

        # Update comparison links at bottom
        # Use previous_version (captured before version files were updated)
        previous = config.previous_version

        # Update existing [Unreleased] link
        unreleased_link_pattern = r"\[Unreleased\]: (https://github\.com/[^/]+/[^/]+)/compare/v[\d.]+\.\.\.HEAD"
        unreleased_link_replacement = f"[Unreleased]: \\1/compare/v{config.version}...HEAD"
        updated_content = re.sub(unreleased_link_pattern, unreleased_link_replacement, new_content)
        if updated_content == new_content:
            print(f"  {color('⚠', Colors.YELLOW)} Could not update [Unreleased] comparison link (format mismatch)")
        new_content = updated_content

        # Extract repo URL from [Unreleased] link (avoids hardcoding)
        repo_url_match = re.search(r"\[Unreleased\]: (https://github\.com/[^/]+/[^/]+)/compare/", new_content)
        if repo_url_match:
            repo_url = repo_url_match.group(1)
        else:
            # Fallback: derive from git remote
            _, remote_url = run_git(["remote", "get-url", "origin"])
            repo_url = re.sub(r'\.git$', '', remote_url.replace("git@github.com:", "https://github.com/"))

        # Add new version link after [Unreleased] link
        new_version_link = f"[{config.version}]: {repo_url}/compare/v{previous}...v{config.version}"

        # Insert after [Unreleased] link line
        before_insert = new_content
        new_content = re.sub(
            r"(\[Unreleased\]: https://github\.com/[^\n]+\n)",
            f"\\1{new_version_link}\n",
            new_content
        )
        if new_content == before_insert:
            print(f"  {color('⚠', Colors.YELLOW)} Could not insert version comparison link")

        if not config.dry_run:
            changelog_path.write_text(new_content)

        print(f"  {color('✓', Colors.GREEN)} Converted [Unreleased] → [{config.version}] - {today}")
        print(f"  {color('✓', Colors.GREEN)} Added new [Unreleased] section")
        print(f"  {color('✓', Colors.GREEN)} Updated comparison links")

        return True

    except FileNotFoundError:
        print(f"  {color('✗', Colors.RED)} CHANGELOG.md not found")
        return False
    except Exception as e:
        print(f"  {color('✗', Colors.RED)} Error updating CHANGELOG: {e}")
        return False


def strip_all_imports(content: str) -> str:
    """Strip all import statements and module-level boilerplate from content.

    Since imports are consolidated at the top of the bundled file,
    we strip them from individual module sections to avoid duplication.
    Also strips logger assignments since the CLI entry point sets up logging.
    """
    lines = content.split('\n')
    filtered_lines = []
    in_multiline_import = False

    for line in lines:
        stripped = line.strip()

        # Handle multiline imports (with parentheses)
        if in_multiline_import:
            if ')' in line:
                in_multiline_import = False
            continue

        # Skip all import statements
        if stripped.startswith('from ') or stripped.startswith('import '):
            if '(' in line and ')' not in line:
                in_multiline_import = True
            continue

        # Skip logger assignments (will be set up in CLI entry point)
        if stripped.startswith('logger = logging.getLogger'):
            continue

        filtered_lines.append(line)

    return '\n'.join(filtered_lines)


def extract_cli_main(cli_content: str) -> str:
    """Extract the CLI portion from line-loop.py.

    Gets everything after the line_loop imports through to the end,
    skipping the shebang, module docstring, and all import statements.
    """
    lines = cli_content.split('\n')
    result_lines = []

    # State tracking
    skip_until_import_close = False
    in_module_docstring = False
    past_imports = False
    skip_header = True  # Skip shebang and module docstring

    for line in lines:
        stripped = line.strip()

        # Skip shebang
        if stripped.startswith('#!'):
            continue

        # Track module-level docstring (first triple-quoted block at start)
        if skip_header and not in_module_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                quote = stripped[:3]
                # Single-line docstring
                if stripped.count(quote) >= 2:
                    continue
                # Start of multi-line docstring
                in_module_docstring = True
                continue
            # Skip comments before docstring (like the Python version comment)
            if stripped.startswith('#'):
                continue

        if in_module_docstring:
            if '"""' in stripped or "'''" in stripped:
                in_module_docstring = False
                skip_header = False
            continue

        # Skip all import statements (both stdlib and line_loop package)
        if stripped.startswith('import ') or stripped.startswith('from '):
            if 'from line_loop import' in line:
                skip_until_import_close = True
            elif '(' in line and ')' not in line:
                skip_until_import_close = True
            continue

        if skip_until_import_close:
            if ')' in line:
                skip_until_import_close = False
                past_imports = True
            continue

        # Once we've seen content after imports, we're in CLI code
        if stripped and not past_imports:
            past_imports = True

        if past_imports:
            # Skip comments that reference the package structure (not applicable in bundled version)
            if '# Import everything from the line_loop package' in line:
                continue
            result_lines.append(line)

    return '\n'.join(result_lines)


def collect_stdlib_imports(modules: list[tuple[str, str]], cli_content: str) -> list[str]:
    """Collect all stdlib/external imports from modules and CLI wrapper.

    Returns deduplicated and merged list of import statements.
    Merges 'from X import a, b' statements for the same module.
    """
    # Track simple imports and from imports separately
    simple_imports = set()  # import X
    from_imports: dict[str, set[str]] = {}  # from X import -> set of names

    all_content = [content for _, content in modules] + [cli_content]

    for content in all_content:
        for line in content.split('\n'):
            stripped = line.strip()
            # Skip internal imports (from .xxx)
            if stripped.startswith('from .'):
                continue
            # Skip line_loop package imports
            if 'line_loop' in stripped:
                continue
            # Skip TYPE_CHECKING imports for now, handle specially
            if 'TYPE_CHECKING' in stripped:
                continue
            # Skip __future__ imports, we don't need them with Python 3.9+
            if '__future__' in stripped:
                continue

            if stripped.startswith('import '):
                # Simple import: import X or import X, Y
                modules_part = stripped[7:].strip()
                for mod in modules_part.split(','):
                    simple_imports.add(mod.strip())
            elif stripped.startswith('from '):
                # From import: from X import a, b, c
                match = re.match(r'from\s+(\S+)\s+import\s+(.+)', stripped)
                if match:
                    module = match.group(1)
                    names = match.group(2)
                    if module not in from_imports:
                        from_imports[module] = set()
                    for name in names.split(','):
                        name = name.strip()
                        if name:
                            from_imports[module].add(name)

    # Build output: simple imports first, then from imports
    result = []

    # Simple imports sorted
    for mod in sorted(simple_imports):
        result.append(f"import {mod}")

    # From imports sorted by module, names sorted within
    for module in sorted(from_imports.keys()):
        names = sorted(from_imports[module])
        result.append(f"from {module} import {', '.join(names)}")

    return result


def get_original_cli_wrapper(repo_root: Path) -> str:
    """Get the original thin CLI wrapper content.

    The thin CLI wrapper is stored separately in line-loop-cli.py to avoid
    the chicken-and-egg problem where bundling overwrites line-loop.py,
    which would then be read as the source for the next bundle.
    """
    cli_file = repo_root / "core" / "line-loop-cli.py"
    if not cli_file.exists():
        raise FileNotFoundError(
            f"CLI wrapper not found: {cli_file}\n"
            "This file contains the thin wrapper that imports from line_loop package."
        )
    return cli_file.read_text()


def bundle_line_loop(repo_root: Path, dry_run: bool = False) -> bool:
    """Bundle line_loop package into line-loop.py for distribution.

    The Claude Code plugin ships a single bundled line-loop.py rather than
    the full package directory. This function bundles the modular line_loop package
    into a single self-contained line-loop.py for distribution.

    Args:
        repo_root: Path to repository root
        dry_run: If True, don't actually write the bundled file

    Returns:
        True if bundling succeeded, False otherwise
    """
    package_dir = repo_root / "core" / "line_loop"
    output_file = repo_root / "plugins" / "claude-code" / "scripts" / "line-loop.py"

    # Read all module contents
    modules: list[tuple[str, str]] = []
    for module_name in LINE_LOOP_MODULES:
        module_path = package_dir / f"{module_name}.py"
        if not module_path.exists():
            print(f"  {color('✗', Colors.RED)} Module not found: {module_path}")
            return False
        modules.append((module_name, module_path.read_text()))

    # Read CLI wrapper from git HEAD (since bundling overwrites it)
    cli_content = get_original_cli_wrapper(repo_root)

    # Collect all stdlib imports
    stdlib_imports = collect_stdlib_imports(modules, cli_content)

    # Build bundled content
    bundled_lines = [
        "#!/usr/bin/env python3",
        "# Requires Python 3.9+ for dataclasses and type hints (list[str] syntax)",
        '"""Line Cook autonomous loop - runs individual phase skills until no tasks remain.',
        "",
        "This file is auto-generated by dev/release.py from the line_loop package.",
        "Do not edit directly - edit the source modules in core/line_loop/ instead.",
        "",
        "Platform Support:",
        "    Linux, macOS, WSL - Fully supported",
        "    Windows - NOT supported (select.select() requires Unix file descriptors)",
        '"""',
        "",
        "# === Standard library imports ===",
    ]

    # Add collected imports
    for imp in stdlib_imports:
        bundled_lines.append(imp)

    # Add typing TYPE_CHECKING import for Protocol (used in models.py)
    bundled_lines.append("")
    bundled_lines.append("from typing import TYPE_CHECKING")
    bundled_lines.append("if TYPE_CHECKING:")
    bundled_lines.append("    from typing import Protocol")
    bundled_lines.append("")

    # Add module contents
    bundled_lines.append("# === Bundled from line_loop package ===")

    for module_name, content in modules:
        bundled_lines.append("")
        bundled_lines.append(f"# --- {module_name}.py ---")
        bundled_lines.append("")

        # Strip all imports (consolidated at top) and module docstring
        stripped = strip_all_imports(content)

        # Remove module-level docstring (first triple-quoted string)
        stripped = re.sub(r'^""".*?"""\s*\n', '', stripped, count=1, flags=re.DOTALL)

        # Remove __future__ imports (we'll put one at the top if needed)
        stripped = re.sub(r'^from __future__ import annotations\s*\n', '', stripped, flags=re.MULTILINE)

        bundled_lines.append(stripped)

    # Add CLI entry point
    bundled_lines.append("")
    bundled_lines.append("# === CLI Entry Point ===")
    bundled_lines.append("")

    cli_portion = extract_cli_main(cli_content)
    bundled_lines.append(cli_portion)

    # Join and write
    bundled_content = '\n'.join(bundled_lines)

    # Clean up excessive blank lines
    bundled_content = re.sub(r'\n{4,}', '\n\n\n', bundled_content)

    if not dry_run:
        output_file.write_text(bundled_content)
        print(f"  {color('✓', Colors.GREEN)} Bundled line_loop package into line-loop.py")

        # Verify bundled Python is syntactically valid
        try:
            ast.parse(output_file.read_text())
            print(f"  {color('✓', Colors.GREEN)} Syntax check passed")
        except SyntaxError as e:
            print(f"  {color('✗', Colors.RED)} Syntax error in bundled file: {e}")
            return False

        # Check bundle size to catch duplication regressions (v0.9.3 doubled to ~7000 lines)
        line_count = len(bundled_content.splitlines())
        if not (1000 <= line_count <= 8000):
            print(f"  {color('✗', Colors.RED)} Bundle size suspect: {line_count} lines (expected 1000-8000)")
            return False
        print(f"  {color('✓', Colors.GREEN)} Bundle size: {line_count} lines")

        # Smoke test: verify the bundled script actually executes
        try:
            result = subprocess.run(
                [sys.executable, str(output_file), "--help"],
                capture_output=True, text=True, timeout=10
            )
        except subprocess.TimeoutExpired:
            print(f"  {color('✗', Colors.RED)} Smoke test timed out (--help hung for 10s)")
            return False
        if result.returncode != 0:
            print(f"  {color('✗', Colors.RED)} Smoke test failed (--help returned {result.returncode})")
            if result.stderr:
                for line in result.stderr.strip().splitlines()[:5]:
                    print(f"      {line}")
            return False
        print(f"  {color('✓', Colors.GREEN)} Smoke test passed (--help)")
    else:
        print(f"  {color('○', Colors.BLUE)} Would bundle line_loop package into line-loop.py")

    return True


def run_validation_scripts(config: ReleaseConfig) -> bool:
    """Run validation scripts and report results."""
    scripts = [
        ("check-plugin-health.py", ["--skip-changelog"]),  # Skip changelog since we just updated it
        ("check-platform-parity.py", []),
        ("doctor-docs.py", []),
    ]

    all_passed = True

    for script_name, args in scripts:
        script_path = config.repo_root / "dev" / script_name
        if not script_path.exists():
            print(f"  {color('⚠', Colors.YELLOW)} {script_name} not found (skipped)")
            continue

        result = subprocess.run(
            [sys.executable, str(script_path)] + args,
            capture_output=True,
            text=True,
            cwd=config.repo_root
        )

        if result.returncode == 0:
            # Check for warnings in output
            if "warning" in result.stdout.lower():
                print(f"  {color('✓', Colors.GREEN)} {script_name} passed (with warnings)")
            else:
                print(f"  {color('✓', Colors.GREEN)} {script_name} passed")
        else:
            print(f"  {color('✗', Colors.RED)} {script_name} failed")
            # Show first few lines of error output
            error_lines = result.stdout.split("\n")[:5]
            for line in error_lines:
                if line.strip():
                    print(f"      {line}")
            all_passed = False

    return all_passed


def create_commit(config: ReleaseConfig) -> bool:
    """Create release commit."""
    if config.dry_run:
        print(f"  {color('○', Colors.BLUE)} Would create commit: \"chore(release): v{config.version}\"")
        return True

    # Stage changes
    files_to_stage = [
        "plugins/claude-code/.claude-plugin/plugin.json",
        "plugins/opencode/package.json",
        "CHANGELOG.md",
        "plugins/claude-code/scripts/line-loop.py"  # Bundled for distribution
    ]

    for file in files_to_stage:
        code, _ = run_git(["add", file])
        if code != 0:
            print(f"  {color('✗', Colors.RED)} Failed to stage {file}")
            return False

    # Create commit
    commit_message = f"chore(release): v{config.version}"
    code, output = run_git(["commit", "-m", commit_message])

    if code != 0:
        print(f"  {color('✗', Colors.RED)} Failed to create commit")
        return False

    # Get commit hash
    code, commit_hash = run_git(["rev-parse", "--short", "HEAD"])

    print(f"  {color('✓', Colors.GREEN)} Created: {commit_hash} \"{commit_message}\"")
    return True


def push_to_remote(config: ReleaseConfig) -> bool:
    """Push to remote to trigger GitHub release workflow."""
    if config.dry_run:
        print(f"  {color('○', Colors.BLUE)} Would push to origin/main")
        return True

    code, _ = run_git(["push", "origin", "main"])

    if code != 0:
        print(f"  {color('✗', Colors.RED)} Failed to push to remote")
        return False

    print(f"  {color('✓', Colors.GREEN)} Pushed to origin/main")
    return True


def print_header(version: str, dry_run: bool = False):
    """Print release header."""
    mode = " (DRY RUN)" if dry_run else ""
    print()
    print(color("╔══════════════════════════════════════════════════════════════╗", Colors.BOLD))
    print(color(f"║  RELEASE: line-cook v{version}{mode:<30}║", Colors.BOLD))
    print(color("╚══════════════════════════════════════════════════════════════╝", Colors.BOLD))
    print()


def print_checklist():
    """Print pre-release checklist reminder."""
    print()
    print(color("Before releasing, verify:", Colors.YELLOW))
    print("  [ ] All notable changes documented")
    print("  [ ] Changes categorized correctly")
    print("  [ ] User-friendly language used")
    print("  [ ] Breaking changes highlighted (if any)")
    print()


def confirm_release(config: ReleaseConfig) -> bool:
    """Ask for confirmation before proceeding."""
    if config.yes:
        return True

    if config.dry_run:
        return True

    try:
        response = input(f"Proceed with release v{config.version}? [y/N] ")
        return response.lower() in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def run_check_only(repo_root: Path) -> int:
    """Run validation checks only, without making changes."""
    print()
    print(color("Checking release readiness...", Colors.BOLD))
    print()

    errors = []
    warnings = []

    # Check git state
    print("Git state:")
    if git_working_tree_clean():
        print(f"  {color('✓', Colors.GREEN)} Working tree clean")
    else:
        print(f"  {color('✗', Colors.RED)} Working tree not clean")
        errors.append("Working tree not clean")

    if on_main_branch():
        print(f"  {color('✓', Colors.GREEN)} On main branch")
    else:
        print(f"  {color('✗', Colors.RED)} Not on main branch")
        errors.append("Not on main branch")

    if up_to_date_with_remote():
        print(f"  {color('✓', Colors.GREEN)} Up to date with origin/main")
    else:
        print(f"  {color('⚠', Colors.YELLOW)} Behind origin/main")
        warnings.append("Behind origin/main")

    # Check versions
    print()
    print("Versions:")
    current = get_current_version(repo_root)
    if current:
        print(f"  Current version: {current}")
    else:
        print(f"  {color('✗', Colors.RED)} Could not read version")
        errors.append("Could not read version")

    # Check changelog
    print()
    print("Changelog:")
    if changelog_has_unreleased_content(repo_root):
        print(f"  {color('✓', Colors.GREEN)} [Unreleased] section has content")
    else:
        print(f"  {color('✗', Colors.RED)} [Unreleased] section is empty")
        errors.append("[Unreleased] section is empty")

    # Run validation scripts
    print()
    print("Validation scripts:")

    # Create a dummy config for validation
    config = ReleaseConfig(version="0.0.0", repo_root=repo_root)
    run_validation_scripts(config)

    # Summary
    print()
    if errors:
        print(color(f"✗ {len(errors)} error(s) found", Colors.RED))
        for err in errors:
            print(f"  - {err}")
        return 1
    elif warnings:
        print(color(f"✓ Ready to release (with {len(warnings)} warning(s))", Colors.YELLOW))
        return 0
    else:
        print(color("✓ Ready to release", Colors.GREEN))
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Automate mechanical steps of releasing a new line-cook version"
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="Version to release (e.g., 0.8.2)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without making modifications"
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push to remote after commit (triggers GitHub release)"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate current state only, don't release"
    )
    parser.add_argument(
        "--bundle",
        action="store_true",
        help="Bundle line_loop package only (for dev testing)"
    )

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent

    # Check-only mode
    if args.check:
        return run_check_only(repo_root)

    # Bundle-only mode
    if args.bundle:
        print()
        print("Bundling line_loop package:")
        if bundle_line_loop(repo_root):
            print()
            print(color("✓ Bundle complete", Colors.GREEN))
            return 0
        else:
            return 4

    # Version required for release
    if not args.version:
        parser.error("version is required (or use --check for validation only)")

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", args.version):
        print(color(f"Error: Invalid version format '{args.version}'. Use X.Y.Z", Colors.RED))
        return 1

    config = ReleaseConfig(
        version=args.version,
        dry_run=args.dry_run,
        push=args.push,
        yes=args.yes,
        repo_root=repo_root
    )

    # Print header
    print_header(config.version, config.dry_run)

    # Pre-flight checks
    print("Pre-flight checks:")
    preflight = preflight_checks(config)

    current = get_current_version(repo_root)

    if git_working_tree_clean():
        print(f"  {color('✓', Colors.GREEN)} Working tree clean")
    else:
        print(f"  {color('✗', Colors.RED)} Working tree not clean")

    if on_main_branch():
        print(f"  {color('✓', Colors.GREEN)} On main branch")
    else:
        print(f"  {color('✗', Colors.RED)} Not on main branch")

    if up_to_date_with_remote():
        print(f"  {color('✓', Colors.GREEN)} Up to date with origin")
    else:
        print(f"  {color('✗', Colors.RED)} Behind origin/main")

    if current and version_is_newer(config.version, current):
        print(f"  {color('✓', Colors.GREEN)} Version {config.version} > {current}")
    else:
        print(f"  {color('✗', Colors.RED)} Version {config.version} not newer than {current}")

    if changelog_has_unreleased_content(repo_root):
        print(f"  {color('✓', Colors.GREEN)} CHANGELOG has unreleased content")
    else:
        print(f"  {color('✗', Colors.RED)} CHANGELOG [Unreleased] is empty")

    if not preflight.passed:
        print()
        print(color("Pre-flight checks failed. Fix errors before releasing.", Colors.RED))
        return 1

    # Show checklist and confirm
    print_checklist()

    if not confirm_release(config):
        print("Release cancelled.")
        return 0

    # Capture current version before updating (for changelog links)
    config.previous_version = current

    def rollback(exit_code: int) -> int:
        """Rollback file changes and return the provided exit code."""
        if config.dry_run:
            return exit_code
        print(f"  {color('↩', Colors.YELLOW)} Rolling back file changes...")
        code, _ = run_git(["checkout", "--", "."])
        if code == 0:
            print(f"  {color('✓', Colors.GREEN)} Rolled back to clean state")
        else:
            print(f"  {color('⚠', Colors.YELLOW)} Rollback failed — run: git checkout -- .")
        return exit_code

    # Update versions
    print()
    print("Updating versions:")
    if not update_versions(config):
        print(color("Version update failed.", Colors.RED))
        return rollback(2)

    # Update changelog
    print()
    print("Updating CHANGELOG:")
    if not update_changelog(config):
        print(color("CHANGELOG update failed.", Colors.RED))
        return rollback(3)

    # Bundle line_loop package
    print()
    print("Bundling line_loop package:")
    if not bundle_line_loop(config.repo_root, config.dry_run):
        print(color("Bundling failed.", Colors.RED))
        return rollback(4)

    # Run validation
    print()
    print("Validation:")
    if not run_validation_scripts(config):
        print(color("Validation failed.", Colors.RED))
        return rollback(5)

    # Create commit
    print()
    print("Commit:")
    if not create_commit(config):
        print(color("Commit failed.", Colors.RED))
        return 6

    # Push if requested
    if config.push:
        print()
        print("Push:")
        if not push_to_remote(config):
            print(color("Push failed.", Colors.RED))
            return 7

    # Success summary
    print()
    print(color("━" * 64, Colors.BOLD))
    print()

    if config.dry_run:
        print(color("DRY RUN COMPLETE", Colors.BLUE))
        print("No changes were made. Run without --dry-run to execute.")
    elif config.push:
        print(color(f"✓ Release v{config.version} complete and pushed!", Colors.GREEN))
        print("GitHub release workflow should be triggered.")
    else:
        print(color(f"✓ Release v{config.version} committed!", Colors.GREEN))
        print()
        print(color("NEXT STEP:", Colors.YELLOW), "git push (will trigger GitHub release workflow)")
        print()
        print(f"Or run: ./dev/release.py {config.version} --push")

    return 0


if __name__ == "__main__":
    sys.exit(main())
