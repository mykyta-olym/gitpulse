#!/usr/bin/env python3
"""
Local supply-chain security scanning script.
Run this before commits to catch vulnerabilities early.

Usage:
    python scripts/security_scan.py [--sbom] [--audit] [--container IMAGE]
"""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def run_command(cmd: list[str], capture: bool = True) -> tuple[int, str]:
    """Run a command and return exit code and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=300,
        )
        return result.returncode, result.stdout + result.stderr
    except FileNotFoundError:
        return 1, f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 1, "Command timed out"


def check_tool_installed(tool: str) -> bool:
    """Check if a tool is installed."""
    code, _ = run_command(["which", tool] if sys.platform != "win32" else ["where", tool])
    return code == 0


def _utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp with a stable ``Z`` suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _parse_json_prefix(output: str) -> Any:
    """Parse the first JSON document embedded in command output.

    Some tools print valid JSON to stdout and advisory text to stderr.  Because
    ``run_command`` returns both streams for diagnostic commands, parse the JSON
    payload and ignore surrounding non-JSON text.
    """
    decoder = json.JSONDecoder()
    starts = [idx for idx in (output.find("{"), output.find("[")) if idx >= 0]
    if not starts:
        raise json.JSONDecodeError("No JSON document found", output, 0)
    data, _idx = decoder.raw_decode(output[min(starts) :].lstrip())
    return data


def run_pip_audit() -> dict[str, Any]:
    """Run pip-audit and return results."""
    print("[SCAN] Running pip-audit dependency scan...")

    if not check_tool_installed("pip-audit"):
        print("  [WARN]  pip-audit not installed. Install with: pip install pip-audit")
        return {"status": "skipped", "reason": "not installed"}

    lockfile = ROOT / "requirements.lock"
    audit_target = "environment"
    cmd = ["pip-audit", "--format", "json"]
    if lockfile.exists():
        audit_target = "requirements.lock"
        cmd = [
            "pip-audit",
            "-r",
            str(lockfile),
            "--format",
            "json",
            "--no-deps",
            "--disable-pip",
        ]

    code, output = run_command(cmd)
    if code not in (0, 1) and audit_target == "requirements.lock":
        print("  [WARN]  Lockfile audit failed; falling back to current environment")
        audit_target = "environment"
        code, output = run_command(["pip-audit", "--format", "json"])

    try:
        data = _parse_json_prefix(output)
        vulns = []
        for dep in data.get("dependencies", []):
            for vuln in dep.get("vulns", []):
                vulns.append(
                    {
                        "package": dep.get("name"),
                        "version": dep.get("version"),
                        "id": vuln.get("id"),
                        "fix_versions": vuln.get("fix_versions", []),
                    }
                )

        critical = sum(1 for v in vulns if "CRITICAL" in str(v))
        high = sum(1 for v in vulns if "HIGH" in str(v))

        print(
            f"  Found {len(vulns)} vulnerabilities in {audit_target} "
            f"(Critical: {critical}, High: {high})"
        )

        return {
            "status": "completed",
            "target": audit_target,
            "total": len(vulns),
            "critical": critical,
            "high": high,
            "vulnerabilities": vulns,
        }
    except json.JSONDecodeError:
        print(f"  [WARN]  Could not parse output: {output[:200]}")
        return {"status": "error", "output": output}


def generate_sbom(output_path: Path) -> dict[str, Any]:
    """Generate CycloneDX SBOM."""
    print("[SBOM] Generating SBOM (CycloneDX)...")

    if not check_tool_installed("cyclonedx-py"):
        print("  [WARN]  cyclonedx-bom not installed. Install with: pip install cyclonedx-bom")
        return {"status": "skipped", "reason": "not installed"}

    json_path = output_path / "sbom-cyclonedx.json"
    code, output = run_command(
        [
            "cyclonedx-py",
            "environment",
            "--spec-version",
            "1.5",
            "--output-format",
            "JSON",
            "--output-file",
            str(json_path),
        ]
    )

    if code == 0:
        print(f"  [OK] SBOM generated: {json_path}")

        # Count components
        try:
            with open(json_path) as f:
                sbom = json.load(f)
            components = len(sbom.get("components", []))
            print(f"  [INFO] Components: {components}")
            return {"status": "completed", "path": str(json_path), "components": components}
        except Exception as e:
            return {"status": "completed", "path": str(json_path), "error": str(e)}
    else:
        print(f"  [FAIL] SBOM generation failed: {output}")
        return {"status": "error", "output": output}


def scan_container(image: str, output_path: Path) -> dict[str, Any]:
    """Scan container image with Trivy."""
    print(f"[SCAN] Scanning container image: {image}...")

    if not check_tool_installed("trivy"):
        print("  [WARN]  Trivy not installed. Install from: https://trivy.dev")
        return {"status": "skipped", "reason": "not installed"}

    json_path = output_path / "trivy-scan.json"
    code, output = run_command(
        ["trivy", "image", "--format", "json", "--output", str(json_path), image]
    )

    # Also print table summary
    run_command(["trivy", "image", "--severity", "HIGH,CRITICAL", image], capture=False)

    try:
        with open(json_path) as f:
            data = json.load(f)

        critical = high = medium = low = 0
        for result in data.get("Results", []):
            for vuln in result.get("Vulnerabilities", []):
                sev = vuln.get("Severity", "").upper()
                if sev == "CRITICAL":
                    critical += 1
                elif sev == "HIGH":
                    high += 1
                elif sev == "MEDIUM":
                    medium += 1
                else:
                    low += 1

        print(f"  [INFO] Critical: {critical}, High: {high}, Medium: {medium}, Low: {low}")

        return {
            "status": "completed",
            "path": str(json_path),
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Local security scanning")
    parser.add_argument("--sbom", action="store_true", help="Generate SBOM")
    parser.add_argument("--audit", action="store_true", help="Run pip-audit")
    parser.add_argument("--container", type=str, help="Scan container image")
    parser.add_argument("--output", type=str, default="./security-reports", help="Output directory")
    parser.add_argument("--all", action="store_true", help="Run all scans")

    args = parser.parse_args()

    # Default to all if nothing specified
    if not any([args.sbom, args.audit, args.container, args.all]):
        args.all = True

    output_path = Path(args.output)
    output_path.mkdir(exist_ok=True)

    print("=" * 60)
    print("[SECURITY] GitPulse - Security Scan")
    print(f"   Timestamp: {_utc_timestamp()}")
    print("=" * 60)
    print()

    results = {}
    exit_code = 0

    # Dependency audit
    if args.audit or args.all:
        results["pip_audit"] = run_pip_audit()
        if results["pip_audit"].get("critical", 0) > 0:
            exit_code = 1
        print()

    # SBOM generation
    if args.sbom or args.all:
        results["sbom"] = generate_sbom(output_path)
        print()

    # Container scanning
    if args.container:
        results["container"] = scan_container(args.container, output_path)
        if results["container"].get("critical", 0) > 0:
            exit_code = 1
        print()

    # Summary
    print("=" * 60)
    print("[SUMMARY] Summary")
    print("=" * 60)

    # Save results
    report_path = output_path / "security-scan-results.json"
    with open(report_path, "w") as f:
        json.dump(
            {
                "timestamp": _utc_timestamp(),
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"  Report saved to: {report_path}")

    if exit_code == 0:
        print("  [OK] No critical vulnerabilities found")
    else:
        print("  [FAIL] Critical vulnerabilities detected!")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
