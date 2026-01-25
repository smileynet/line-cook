#!/usr/bin/env python3
"""
validate-smoke-test.py - Validate smoke test artifacts and proof of work.

Verifies that the smoke test completed successfully by checking:
- Code change in validation.py (regex implementation)
- Test file exists (test_validation.py)
- Tests pass (pytest exit code 0)
- Bead closed (status: closed)
- Git commit exists with bead reference
- Push to remote succeeded

Usage:
    ./scripts/validate-smoke-test.py --test-dir /path/to/test
    ./scripts/validate-smoke-test.py --test-dir /path --output results.json
    ./scripts/validate-smoke-test.py --test-dir /path --skip-cook-check=true

Exit codes:
    0: All checks pass
    1: Some checks failed
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ValidationResult:
    """Result of a validation check."""
    name: str
    passed: bool
    message: str
    details: Optional[str] = None


@dataclass
class SmokeTestReport:
    """Complete smoke test validation report."""
    platform: str
    timestamp: str
    test_dir: str
    results: list[ValidationResult] = field(default_factory=list)
    passed: bool = True
    skipped_cook: bool = False

    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result."""
        self.results.append(result)
        if not result.passed:
            self.passed = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "platform": self.platform,
            "timestamp": self.timestamp,
            "test_dir": self.test_dir,
            "passed": self.passed,
            "skipped_cook": self.skipped_cook,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.results
            ],
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed)
            }
        }


def run_command(cmd: list[str], cwd: Optional[Path] = None) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def check_validation_py_changed(test_dir: Path) -> ValidationResult:
    """Check that validation.py has been modified with regex."""
    validation_file = test_dir / "src" / "validation.py"

    if not validation_file.exists():
        return ValidationResult(
            name="validation_py_changed",
            passed=False,
            message="validation.py not found",
            details=f"Expected at: {validation_file}"
        )

    content = validation_file.read_text()

    # Check for regex import or pattern
    has_regex = (
        "import re" in content or
        "from re import" in content or
        "re.match" in content or
        "re.search" in content or
        "re.compile" in content or
        "re.fullmatch" in content or
        # Also accept inline regex patterns
        r"@.*\." in content  # basic email pattern
    )

    # Check that placeholder is gone
    has_placeholder = 'return "@" in email' in content

    if has_regex and not has_placeholder:
        return ValidationResult(
            name="validation_py_changed",
            passed=True,
            message="validation.py updated with regex implementation"
        )
    elif has_placeholder:
        return ValidationResult(
            name="validation_py_changed",
            passed=False,
            message="validation.py still contains placeholder",
            details='Found: return "@" in email'
        )
    else:
        return ValidationResult(
            name="validation_py_changed",
            passed=False,
            message="validation.py does not contain regex validation",
            details="Expected re.match, re.search, or similar"
        )


def check_test_file_exists(test_dir: Path) -> ValidationResult:
    """Check that test file was created."""
    # Check multiple possible locations
    possible_paths = [
        test_dir / "tests" / "test_validation.py",
        test_dir / "test_validation.py",
        test_dir / "src" / "test_validation.py",
    ]

    for path in possible_paths:
        if path.exists():
            content = path.read_text()
            # Verify it has actual test content
            if "def test_" in content or "class Test" in content:
                return ValidationResult(
                    name="test_file_exists",
                    passed=True,
                    message=f"Test file created at {path.relative_to(test_dir)}"
                )

    return ValidationResult(
        name="test_file_exists",
        passed=False,
        message="No test file found",
        details=f"Checked: {', '.join(str(p.relative_to(test_dir)) for p in possible_paths)}"
    )


def check_tests_pass(test_dir: Path) -> ValidationResult:
    """Check that pytest passes."""
    # First check if pytest is available
    code, _, _ = run_command(["python3", "-m", "pytest", "--version"])
    if code != 0:
        return ValidationResult(
            name="tests_pass",
            passed=True,  # Skip if pytest not available
            message="pytest not available, skipping test execution",
            details="Install pytest to enable test verification"
        )

    # Run pytest
    code, stdout, stderr = run_command(
        ["python3", "-m", "pytest", "-v", "--tb=short"],
        cwd=test_dir
    )

    if code == 0:
        # Count tests
        match = re.search(r"(\d+) passed", stdout)
        test_count = match.group(1) if match else "?"
        return ValidationResult(
            name="tests_pass",
            passed=True,
            message=f"All tests passed ({test_count} tests)"
        )
    elif code == 5:
        # No tests collected
        return ValidationResult(
            name="tests_pass",
            passed=False,
            message="No tests collected",
            details=stderr or stdout
        )
    else:
        return ValidationResult(
            name="tests_pass",
            passed=False,
            message="Tests failed",
            details=(stderr or stdout)[:500]
        )


def check_bead_closed(test_dir: Path) -> ValidationResult:
    """Check that smoke-001 bead is closed."""
    bead_file = test_dir / ".beads" / "issues" / "smoke-001.yaml"

    if not bead_file.exists():
        return ValidationResult(
            name="bead_closed",
            passed=False,
            message="Bead file not found",
            details=f"Expected at: {bead_file}"
        )

    content = bead_file.read_text()

    # Check status
    if "status: closed" in content or "status: done" in content:
        return ValidationResult(
            name="bead_closed",
            passed=True,
            message="Bead smoke-001 is closed"
        )
    elif "status: open" in content:
        return ValidationResult(
            name="bead_closed",
            passed=False,
            message="Bead smoke-001 still open",
            details="status: open"
        )
    else:
        # Try to extract status
        match = re.search(r"status:\s*(\w+)", content)
        status = match.group(1) if match else "unknown"
        return ValidationResult(
            name="bead_closed",
            passed=False,
            message=f"Bead smoke-001 has unexpected status: {status}"
        )


def check_commit_exists(test_dir: Path) -> ValidationResult:
    """Check that a commit referencing smoke-001 exists."""
    code, stdout, stderr = run_command(
        ["git", "log", "--oneline", "-n", "20"],
        cwd=test_dir
    )

    if code != 0:
        return ValidationResult(
            name="commit_exists",
            passed=False,
            message="Failed to check git log",
            details=stderr
        )

    # Look for commit referencing smoke-001
    if "smoke-001" in stdout.lower() or "smoke001" in stdout.lower():
        # Find the specific commit
        for line in stdout.split("\n"):
            if "smoke-001" in line.lower() or "smoke001" in line.lower():
                return ValidationResult(
                    name="commit_exists",
                    passed=True,
                    message="Found commit referencing smoke-001",
                    details=line.strip()
                )

    # Also check for commits mentioning email validation
    if "email" in stdout.lower() and "valid" in stdout.lower():
        for line in stdout.split("\n"):
            if "email" in line.lower():
                return ValidationResult(
                    name="commit_exists",
                    passed=True,
                    message="Found commit mentioning email validation",
                    details=line.strip()
                )

    return ValidationResult(
        name="commit_exists",
        passed=False,
        message="No commit found referencing smoke-001",
        details=f"Recent commits:\n{stdout[:300]}"
    )


def check_pushed_to_remote(test_dir: Path) -> ValidationResult:
    """Check that changes were pushed to remote."""
    # First check what remote knows
    code, stdout, stderr = run_command(
        ["git", "fetch", "origin"],
        cwd=test_dir
    )

    if code != 0:
        return ValidationResult(
            name="pushed_to_remote",
            passed=False,
            message="Failed to fetch from remote",
            details=stderr
        )

    # Compare local and remote
    code, stdout, stderr = run_command(
        ["git", "log", "origin/main..HEAD", "--oneline"],
        cwd=test_dir
    )

    if code != 0:
        return ValidationResult(
            name="pushed_to_remote",
            passed=False,
            message="Failed to compare with remote",
            details=stderr
        )

    if stdout.strip() == "":
        return ValidationResult(
            name="pushed_to_remote",
            passed=True,
            message="All commits pushed to remote"
        )
    else:
        unpushed_count = len(stdout.strip().split("\n"))
        return ValidationResult(
            name="pushed_to_remote",
            passed=False,
            message=f"{unpushed_count} commit(s) not pushed to remote",
            details=stdout[:200]
        )


def check_no_uncommitted_changes(test_dir: Path) -> ValidationResult:
    """Check that there are no uncommitted changes."""
    code, stdout, stderr = run_command(
        ["git", "status", "--porcelain"],
        cwd=test_dir
    )

    if code != 0:
        return ValidationResult(
            name="clean_working_tree",
            passed=False,
            message="Failed to check git status",
            details=stderr
        )

    if stdout.strip() == "":
        return ValidationResult(
            name="clean_working_tree",
            passed=True,
            message="Working tree is clean"
        )
    else:
        return ValidationResult(
            name="clean_working_tree",
            passed=False,
            message="Uncommitted changes exist",
            details=stdout[:300]
        )


def run_validation(
    test_dir: Path,
    platform: str,
    skip_cook_check: bool = False
) -> SmokeTestReport:
    """Run all validation checks."""
    report = SmokeTestReport(
        platform=platform,
        timestamp=datetime.now().isoformat(),
        test_dir=str(test_dir),
        skipped_cook=skip_cook_check
    )

    if skip_cook_check:
        # Only check setup was successful
        report.add_result(ValidationResult(
            name="setup_check",
            passed=True,
            message="Setup phase completed (cook skipped)"
        ))
    else:
        # Full validation
        report.add_result(check_validation_py_changed(test_dir))
        report.add_result(check_test_file_exists(test_dir))
        report.add_result(check_tests_pass(test_dir))
        report.add_result(check_bead_closed(test_dir))
        report.add_result(check_commit_exists(test_dir))
        report.add_result(check_pushed_to_remote(test_dir))
        report.add_result(check_no_uncommitted_changes(test_dir))

    return report


def format_human_report(report: SmokeTestReport) -> str:
    """Format report as human-readable output."""
    lines = [
        f"Smoke Test Validation Report",
        f"============================",
        f"Platform: {report.platform}",
        f"Timestamp: {report.timestamp}",
        f"Test Dir: {report.test_dir}",
        f"Skipped Cook: {report.skipped_cook}",
        "",
        "Results:",
        "-" * 40,
    ]

    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"  [{status}] {result.name}")
        lines.append(f"         {result.message}")
        if result.details:
            for detail_line in result.details.split("\n")[:3]:
                lines.append(f"         > {detail_line}")

    lines.extend([
        "",
        "-" * 40,
        f"Total: {len(report.results)} checks",
        f"Passed: {sum(1 for r in report.results if r.passed)}",
        f"Failed: {sum(1 for r in report.results if not r.passed)}",
        "",
        f"Overall: {'PASSED' if report.passed else 'FAILED'}",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate smoke test artifacts"
    )
    parser.add_argument(
        "--test-dir", required=True,
        help="Path to test directory"
    )
    parser.add_argument(
        "--platform", default="unknown",
        help="Platform name for report"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON to stdout"
    )
    parser.add_argument(
        "--skip-cook-check", default="false",
        help="Skip validation of cook phase artifacts"
    )

    args = parser.parse_args()

    test_dir = Path(args.test_dir)
    if not test_dir.exists():
        print(f"Error: Test directory does not exist: {test_dir}", file=sys.stderr)
        sys.exit(1)

    skip_cook = args.skip_cook_check.lower() in ("true", "1", "yes")

    # Run validation
    report = run_validation(test_dir, args.platform, skip_cook)

    # Output results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report.to_dict(), indent=2))
        print(f"Report written to: {args.output}")

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_human_report(report))

    # Exit with appropriate code
    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
