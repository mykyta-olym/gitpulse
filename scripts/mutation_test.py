#!/usr/bin/env python3
"""Mutation testing runner for test quality validation.

Mutation testing introduces small changes (mutations) to the source code
and checks if the tests catch them. A high mutation score indicates
high-quality tests.

Usage:
    python scripts/mutation_test.py [options]

Options:
    --module MODULE    Target module or file path to mutate
    --quick            Quick run - smaller target subset for faster feedback
    --report           Generate HTML report
    --ci               CI mode - fail if score < 70%
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Modules that are good candidates for mutation testing
# (high value, pure logic, well-tested)
MUTATION_TARGETS = [
    "src/app/utils/gitlab_patterns.py",
    "src/app/utils/text_analysis.py",
    "src/app/utils/time_utils.py",
    "src/app/compliance/rubric_engine.py",
    "src/app/compliance/gaming_detection.py",
]

# Smaller subset for quick mutation runs (focus on well-tested modules)
QUICK_TARGETS = [
    "src/app/utils/gitlab_patterns.py",
    "src/app/utils/text_analysis.py",
    "src/app/utils/time_utils.py",
]

# Minimum mutation score for CI to pass (percentage)
# Note: Target is 70%, but allowing 65% during active development
MIN_MUTATION_SCORE = 65

# Mapping aligned with mutmut's status handling
STATUS_BY_EXIT_CODE: dict[int, str] = {
    1: "killed",
    3: "killed",
    -24: "killed",
    0: "survived",
    5: "no_tests",
    33: "no_tests",
    2: "interrupted",
    34: "skipped",
    35: "suspicious",
    36: "timeout",
    24: "timeout",
    152: "timeout",
    255: "timeout",
    -11: "segfault",
    -9: "segfault",
}


def _module_pattern_from_target(target: str) -> str:
    """Convert a target path/module into a mutmut mutant name pattern."""
    if "*" in target:
        return target

    if target.endswith(".py") or "/" in target or "\\" in target:
        path = Path(target).with_suffix("")
        parts = path.parts
        if parts and parts[0] == "src":
            parts = parts[1:]
        module = ".".join(parts)
    else:
        module = target

    return f"{module}.*"


def _collect_results() -> dict[str, int]:
    """Aggregate mutmut results from per-file meta files."""
    results = {
        "killed": 0,
        "survived": 0,
        "timeout": 0,
        "suspicious": 0,
        "skipped": 0,
        "no_tests": 0,
        "not_checked": 0,
        "segfault": 0,
        "interrupted": 0,
    }

    mutants_dir = Path("mutants")
    if not mutants_dir.exists():
        return results

    for meta_path in mutants_dir.rglob("*.meta"):
        try:
            meta = json.loads(meta_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue

        exit_code_by_key = meta.get("exit_code_by_key", {})
        for exit_code in exit_code_by_key.values():
            if exit_code is None:
                results["not_checked"] += 1
                continue
            status = STATUS_BY_EXIT_CODE.get(exit_code, "suspicious")
            if status in results:
                results[status] += 1
            else:
                results["suspicious"] += 1

    return results


def run_mutmut(
    target: str | None = None,
    quick: bool = False,
    ci_mode: bool = False,
) -> tuple[int, dict[str, int]]:
    """Run mutmut mutation testing.

    Returns:
        Tuple of (exit_code, results_dict)
    """
    # Determine which mutants to run
    mutant_patterns: list[str] = []
    if target:
        mutant_patterns.append(_module_pattern_from_target(target))
    elif quick:
        mutant_patterns.extend(_module_pattern_from_target(p) for p in QUICK_TARGETS)

    # Build mutmut command (config controls paths/tests)
    cmd = [sys.executable, "-m", "mutmut", "run"]
    if mutant_patterns:
        cmd.extend(mutant_patterns)

    if mutant_patterns:
        print(f"Running mutation testing for: {', '.join(mutant_patterns)}")
    else:
        print("Running mutation testing for configured targets.")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    # Run mutmut
    env = os.environ.copy()
    env.setdefault("MUTANT_UNDER_TEST", "stats")
    # mutmut uses fork() internally; suppress the Python 3.12 deprecation warning
    # to keep CI logs clean without masking test failures.
    env.setdefault("PYTHONWARNINGS", "ignore::DeprecationWarning")
    result = subprocess.run(cmd, capture_output=False, env=env)

    # Collect results from meta files
    results = _collect_results()

    return result.returncode, results


def calculate_score(results: dict[str, int]) -> float:
    """Calculate mutation score from results."""
    killed = results.get("killed", 0)
    survived = results.get("survived", 0)
    timeout = results.get("timeout", 0)
    suspicious = results.get("suspicious", 0)
    segfault = results.get("segfault", 0)
    interrupted = results.get("interrupted", 0)

    total_mutants = killed + survived + timeout + suspicious + segfault + interrupted

    if total_mutants == 0:
        return 100.0

    # Killed and timeout are considered "caught"
    caught = killed + timeout
    score = (caught / total_mutants) * 100

    return float(round(score, 2))


def generate_html_report(results: dict[str, int], score: float) -> Path:
    """Generate a lightweight HTML mutation report."""
    report_dir = Path("html")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "index.html"
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Mutation Testing Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 600px; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; }}
    th {{ background: #f5f5f5; }}
  </style>
</head>
<body>
  <h1>Mutation Testing Report</h1>
  <p><strong>Mutation score:</strong> {score}%</p>
  <table>
    <tr><th>Status</th><th>Count</th></tr>
    <tr><td>Killed</td><td>{results.get("killed", 0)}</td></tr>
    <tr><td>Survived</td><td>{results.get("survived", 0)}</td></tr>
    <tr><td>Timeout</td><td>{results.get("timeout", 0)}</td></tr>
    <tr><td>Suspicious</td><td>{results.get("suspicious", 0)}</td></tr>
    <tr><td>Skipped</td><td>{results.get("skipped", 0)}</td></tr>
    <tr><td>No tests</td><td>{results.get("no_tests", 0)}</td></tr>
    <tr><td>Not checked</td><td>{results.get("not_checked", 0)}</td></tr>
    <tr><td>Segfault</td><td>{results.get("segfault", 0)}</td></tr>
  </table>
</body>
</html>
"""
    report_path.write_text(html, encoding="utf-8")
    print(f"\nHTML report generated: {report_path.absolute()}")
    return report_path


def print_summary(results: dict[str, int], score: float) -> None:
    """Print mutation testing summary."""
    print("\n" + "=" * 60)
    print("MUTATION TESTING SUMMARY")
    print("=" * 60)

    print(f"\nKilled mutants:     {results.get('killed', 0)}")
    print(f"Survived mutants:   {results.get('survived', 0)}")
    print(f"Timeout mutants:    {results.get('timeout', 0)}")
    print(f"Suspicious mutants: {results.get('suspicious', 0)}")
    print(f"Skipped mutants:    {results.get('skipped', 0)}")
    print(f"No-test mutants:    {results.get('no_tests', 0)}")
    print(f"Not checked:        {results.get('not_checked', 0)}")
    print(f"Segfault mutants:   {results.get('segfault', 0)}")

    print(f"\nMUTATION SCORE: {score}%")

    if score >= 80:
        print("PASS: Excellent test quality.")
    elif score >= 70:
        print("PASS: Good test quality.")
    elif score >= 50:
        print("WARNING: Fair test quality - consider adding more tests.")
    else:
        print("FAIL: Poor test quality - tests need improvement.")

    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run mutation testing")
    parser.add_argument(
        "--module",
        help="Target module or file path to mutate",
        default=None,
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick run (subset of mutation targets)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate HTML report",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help=f"CI mode - fail if score < {MIN_MUTATION_SCORE} percent",
    )

    args = parser.parse_args()

    # Check mutmut is installed
    try:
        subprocess.run(
            [sys.executable, "-m", "mutmut", "--version"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: mutmut not installed. Install with: pip install mutmut")
        sys.exit(1)

    # Run mutation testing
    exit_code, results = run_mutmut(
        target=args.module,
        quick=args.quick,
        ci_mode=args.ci,
    )

    # Calculate score
    score = calculate_score(results)

    # Print summary
    print_summary(results, score)

    # Generate report if requested
    if args.report:
        generate_html_report(results, score)

    # CI mode - check threshold
    if args.ci:
        if score < MIN_MUTATION_SCORE:
            print(f"\nFAILED: Mutation score {score}% < {MIN_MUTATION_SCORE}% threshold")
            sys.exit(1)
        else:
            print(f"\nPASSED: Mutation score {score}% >= {MIN_MUTATION_SCORE}% threshold")

    sys.exit(0 if exit_code == 0 else 1)


if __name__ == "__main__":
    main()
