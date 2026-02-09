#!/usr/bin/env python3
"""
eval-report.py - Aggregate eval results and compute statistics.

Loads all JSON result files from tests/results/eval/, groups by
provider and scenario, computes mean/stddev for wall time and tokens,
and renders a markdown report table plus JSON summary.

Usage:
    ./tests/eval/eval-report.py
    ./tests/eval/eval-report.py --results-dir tests/results/eval/
    ./tests/eval/eval-report.py --json
    ./tests/eval/eval-report.py --output report.md
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# Approximate cost per 1M tokens (Sonnet-class pricing, rough estimates only).
# Actual costs depend on each provider's model and pricing tier.
COST_PER_1M_INPUT = {
    "claude": 3.00,
    "opencode": 3.00,
    "kiro": 3.00,
}
COST_PER_1M_OUTPUT = {
    "claude": 15.00,
    "opencode": 15.00,
    "kiro": 15.00,
}


@dataclass
class StepResult:
    """Single step within a narrative run."""
    step: int
    name: str
    command: str
    wall_time_ms: int
    exit_code: int
    agent_passed: bool
    agent_reasoning: str
    step_goal: str
    checks: list


@dataclass
class RunResult:
    """Single eval run result."""
    provider: str
    scenario: str
    run_id: str
    wall_time_ms: int
    exit_code: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    actual_cost_usd: float
    timestamp: str
    result_file: str
    is_narrative: bool = False
    steps: list[StepResult] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Single validation result."""
    provider: str
    scenario: str
    run_id: str
    passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    checks: list
    validate_file: str


@dataclass
class ScenarioStats:
    """Aggregated statistics for a provider+scenario combination."""
    provider: str
    scenario: str
    runs: int = 0
    pass_count: int = 0
    fail_count: int = 0
    wall_times_ms: list = field(default_factory=list)
    input_tokens_list: list = field(default_factory=list)
    output_tokens_list: list = field(default_factory=list)
    actual_costs_usd: list = field(default_factory=list)
    failure_modes: list = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.pass_count / self.runs if self.runs > 0 else 0.0

    @property
    def mean_wall_time_s(self) -> float:
        if not self.wall_times_ms:
            return 0.0
        return sum(self.wall_times_ms) / len(self.wall_times_ms) / 1000.0

    @property
    def stddev_wall_time_s(self) -> float:
        return _stddev(self.wall_times_ms) / 1000.0

    @property
    def mean_input_tokens(self) -> float:
        return _mean(self.input_tokens_list)

    @property
    def mean_output_tokens(self) -> float:
        return _mean(self.output_tokens_list)

    @property
    def mean_cost_usd(self) -> float:
        # Use actual cost from provider if available, otherwise estimate
        actual_costs = [cost for cost in self.actual_costs_usd if cost > 0]
        if actual_costs:
            return _mean(actual_costs)
        input_cost = self.mean_input_tokens / 1_000_000 * COST_PER_1M_INPUT.get(self.provider, 3.00)
        output_cost = self.mean_output_tokens / 1_000_000 * COST_PER_1M_OUTPUT.get(self.provider, 15.00)
        return input_cost + output_cost

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "scenario": self.scenario,
            "runs": self.runs,
            "pass_rate": round(self.pass_rate, 2),
            "wall_time_s": {
                "mean": round(self.mean_wall_time_s, 1),
                "stddev": round(self.stddev_wall_time_s, 1),
            },
            "tokens": {
                "input_mean": round(self.mean_input_tokens),
                "output_mean": round(self.mean_output_tokens),
            },
            "cost_usd_mean": round(self.mean_cost_usd, 3),
            "failure_modes": self.failure_modes,
        }


def _mean(values: list) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _stddev(values: list) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def load_run_results(results_dir: Path) -> list[RunResult]:
    """Load all run result JSON files (excludes validation files)."""
    results = []
    for result_file in sorted(results_dir.glob("*.json")):
        if "validate" in result_file.name:
            continue
        try:
            data = json.loads(result_file.read_text())
            if "scenario" not in data:
                continue
            tokens = data.get("tokens", {})
            is_narrative = data.get("is_narrative", False)

            # Parse step results for narratives (backward-compatible with old signal_found format)
            steps = []
            if is_narrative:
                for step_data in data.get("steps", []):
                    # Support both new (agent_passed) and old (signal_found) field names
                    agent_passed = step_data.get("agent_passed", step_data.get("signal_found", True))
                    agent_reasoning = step_data.get("agent_reasoning", "")
                    step_goal = step_data.get("step_goal", step_data.get("expected_signal", ""))
                    steps.append(StepResult(
                        step=step_data.get("step", 0),
                        name=step_data.get("name", ""),
                        command=step_data.get("command", ""),
                        wall_time_ms=step_data.get("wall_time_ms", 0),
                        exit_code=step_data.get("exit_code", 0),
                        agent_passed=agent_passed,
                        agent_reasoning=agent_reasoning,
                        step_goal=step_goal,
                        checks=step_data.get("checks", []),
                    ))

            results.append(RunResult(
                provider=data.get("provider", "unknown"),
                scenario=data.get("scenario", "unknown"),
                run_id=data.get("run_id", "0"),
                wall_time_ms=data.get("wall_time_ms", 0),
                exit_code=data.get("exit_code", -1),
                input_tokens=tokens.get("input", 0),
                output_tokens=tokens.get("output", 0),
                cache_read_tokens=tokens.get("cache_read", 0),
                cache_creation_tokens=tokens.get("cache_creation", 0),
                actual_cost_usd=tokens.get("cost_usd", 0.0),
                timestamp=data.get("timestamp", ""),
                result_file=str(result_file),
                is_narrative=is_narrative,
                steps=steps,
            ))
        except (json.JSONDecodeError, KeyError):
            print(f"Warning: skipping malformed file: {result_file}", file=sys.stderr)
    return results


def load_validation_results(results_dir: Path) -> list[ValidationResult]:
    """Load all validation result JSON files."""
    results = []
    for validate_file in sorted(results_dir.glob("*-validate.json")):
        try:
            data = json.loads(validate_file.read_text())
            results.append(ValidationResult(
                provider=data.get("provider", "unknown"),
                scenario=data.get("scenario", "unknown"),
                run_id=data.get("run_id", "0"),
                passed=data.get("passed", False),
                total_checks=data.get("summary", {}).get("total", 0),
                passed_checks=data.get("summary", {}).get("passed", 0),
                failed_checks=data.get("summary", {}).get("failed", 0),
                checks=data.get("checks", []),
                validate_file=str(validate_file),
            ))
        except (json.JSONDecodeError, KeyError):
            print(f"Warning: skipping malformed file: {validate_file}", file=sys.stderr)
    return results


def compute_stats(
    run_results: list[RunResult],
    validation_results: list[ValidationResult],
) -> dict[tuple[str, str], ScenarioStats]:
    """Compute aggregated statistics per provider per scenario."""
    stats: dict[tuple[str, str], ScenarioStats] = {}

    # Index validations by (provider, scenario, run_id)
    validation_index: dict[tuple[str, str, str], ValidationResult] = {}
    for validation in validation_results:
        validation_index[(validation.provider, validation.scenario, validation.run_id)] = validation

    for run in run_results:
        key = (run.provider, run.scenario)
        if key not in stats:
            stats[key] = ScenarioStats(provider=run.provider, scenario=run.scenario)

        scenario_stats = stats[key]
        scenario_stats.runs += 1
        scenario_stats.wall_times_ms.append(run.wall_time_ms)
        scenario_stats.input_tokens_list.append(run.input_tokens)
        scenario_stats.output_tokens_list.append(run.output_tokens)
        scenario_stats.actual_costs_usd.append(run.actual_cost_usd)

        # Check validation result
        validation = validation_index.get((run.provider, run.scenario, run.run_id))
        if validation:
            if validation.passed:
                scenario_stats.pass_count += 1
            else:
                scenario_stats.fail_count += 1
                # Categorize failure modes from failed checks
                for check in validation.checks:
                    if not check.get("passed"):
                        scenario_stats.failure_modes.append(check.get("name", "unknown"))
        elif run.exit_code == 0:
            scenario_stats.pass_count += 1
        else:
            scenario_stats.fail_count += 1
            scenario_stats.failure_modes.append(f"exit_code_{run.exit_code}")

    return stats


def _render_per_step_timing(narrative_runs: list[RunResult]) -> list[str]:
    """Render per-step timing breakdown for narrative runs."""
    lines = []

    # Group runs by scenario
    runs_by_scenario: dict[str, list[RunResult]] = {}
    for run in narrative_runs:
        runs_by_scenario.setdefault(run.scenario, []).append(run)

    for scenario in sorted(runs_by_scenario.keys()):
        runs = runs_by_scenario[scenario]
        if not runs or not runs[0].steps:
            continue

        # Collect unique providers across runs
        providers = sorted({run.provider for run in runs})

        lines.extend(["", f"### {scenario}", ""])

        # Header
        header = "| Step | Command |"
        sep = "|------|---------|"
        for provider in providers:
            header += f" {provider} (s) |"
            sep += "------------|"
        lines.append(header)
        lines.append(sep)

        # Get step names from first run (all runs for same scenario have same steps)
        step_names = [(step.step, step.command) for step in runs[0].steps]

        for step_num, command in step_names:
            row = f"| {step_num} | {command} |"
            for provider in providers:
                provider_runs = [run for run in runs if run.provider == provider]
                times = []
                for run in provider_runs:
                    for step in run.steps:
                        if step.step == step_num:
                            times.append(step.wall_time_ms / 1000.0)
                if times:
                    mean_time = sum(times) / len(times)
                    row += f" {mean_time:.1f} |"
                else:
                    row += " N/A |"
            lines.append(row)

    return lines


def _render_compliance_matrix(
    narrative_runs: list[RunResult],
    validation_results: list[ValidationResult],
) -> list[str]:
    """Render a compliance matrix showing signal/check pass rates per provider."""
    lines = []

    # Collect all unique check names across all narrative validations
    narrative_scenarios = {run.scenario for run in narrative_runs}
    narrative_validations = [
        validation for validation in validation_results if validation.scenario in narrative_scenarios
    ]

    if not narrative_validations:
        return lines

    # Build check pass counts: check_name -> provider -> [passed_count, total_count]
    check_stats: dict[str, dict[str, list[int]]] = {}
    providers = sorted({validation.provider for validation in narrative_validations})

    for validation in narrative_validations:
        for check in validation.checks:
            check_name = check.get("name", "unknown")
            if check_name not in check_stats:
                check_stats[check_name] = {}
            if validation.provider not in check_stats[check_name]:
                check_stats[check_name][validation.provider] = [0, 0]
            check_stats[check_name][validation.provider][1] += 1
            if check.get("passed"):
                check_stats[check_name][validation.provider][0] += 1

    if not check_stats:
        return lines

    lines.extend(["", "## Compliance Matrix", ""])

    header = "| Check |"
    sep = "|-------|"
    for provider in providers:
        header += f" {provider} |"
        sep += "--------|"
    lines.append(header)
    lines.append(sep)

    for check_name in sorted(check_stats.keys()):
        row = f"| {check_name} |"
        for provider in providers:
            if provider in check_stats[check_name]:
                passed, total = check_stats[check_name][provider]
                row += f" {passed}/{total} |"
            else:
                row += " - |"
        lines.append(row)

    return lines


def render_markdown_table(
    stats: dict[tuple[str, str], ScenarioStats],
    run_results: list[RunResult] | None = None,
    validation_results: list[ValidationResult] | None = None,
) -> str:
    """Render aggregated statistics as a markdown table."""
    lines = [
        "# Eval Report",
        "",
        "| Provider | Scenario | Runs | Pass Rate | Wall Time (s) | Input Tokens | Output Tokens | Avg Cost |",
        "|----------|----------|------|-----------|---------------|--------------|---------------|-----------|",
    ]

    for key in sorted(stats.keys()):
        scenario_stats = stats[key]
        wall_str = f"{scenario_stats.mean_wall_time_s:.1f} +/- {scenario_stats.stddev_wall_time_s:.1f}"
        lines.append(
            f"| {scenario_stats.provider} | {scenario_stats.scenario} | {scenario_stats.runs} | "
            f"{scenario_stats.pass_rate:.0%} | {wall_str} | "
            f"{scenario_stats.mean_input_tokens:.0f} | {scenario_stats.mean_output_tokens:.0f} | "
            f"${scenario_stats.mean_cost_usd:.3f} |"
        )

    # Per-step timing for narrative runs
    if run_results:
        narrative_runs = [r for r in run_results if r.is_narrative]
        if narrative_runs:
            lines.extend(["", "## Per-Step Timing"])
            lines.extend(_render_per_step_timing(narrative_runs))

    # Compliance matrix for narrative runs
    if run_results and validation_results:
        narrative_runs = [r for r in run_results if r.is_narrative]
        if narrative_runs:
            lines.extend(_render_compliance_matrix(narrative_runs, validation_results))

    # Failure modes section
    any_failures = any(scenario_stats.failure_modes for scenario_stats in stats.values())
    if any_failures:
        lines.extend(["", "## Failure Modes", ""])
        for key in sorted(stats.keys()):
            scenario_stats = stats[key]
            if scenario_stats.failure_modes:
                # Count occurrences of each failure mode
                failure_counts: dict[str, int] = {}
                for mode in scenario_stats.failure_modes:
                    failure_counts[mode] = failure_counts.get(mode, 0) + 1
                modes_str = ", ".join(f"{mode} ({count}x)" for mode, count in sorted(failure_counts.items()))
                lines.append(f"- **{scenario_stats.provider}/{scenario_stats.scenario}**: {modes_str}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Aggregate eval results and compute statistics")
    parser.add_argument(
        "--results-dir",
        default="tests/results/eval",
        help="Directory containing eval result JSON files",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON summary")
    parser.add_argument("--output", "-o", help="Write markdown report to file")

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}", file=sys.stderr)
        print("Run some evals first with eval.sh", file=sys.stderr)
        sys.exit(1)

    run_results = load_run_results(results_dir)
    validation_results = load_validation_results(results_dir)

    if not run_results:
        print("No run results found.", file=sys.stderr)
        sys.exit(1)

    stats = compute_stats(run_results, validation_results)

    if args.json:
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_runs": len(run_results),
            "total_validations": len(validation_results),
            "stats": [s.to_dict() for s in sorted(stats.values(), key=lambda s: (s.provider, s.scenario))],
        }
        print(json.dumps(summary, indent=2))
    else:
        report = render_markdown_table(stats, run_results, validation_results)
        if args.output:
            Path(args.output).write_text(report + "\n")
            print(f"Report written to: {args.output}")
        else:
            print(report)


if __name__ == "__main__":
    main()
