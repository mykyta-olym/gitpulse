"""Tests for supply-chain security tooling."""

import importlib.util
import json
from pathlib import Path

import pytest


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".gitlab-ci.yml").exists():
            return candidate
    return start


REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)


class TestSupplyChainSecurity:
    """Test security scanning configuration and scripts."""

    def test_pyproject_has_security_deps(self) -> None:
        """Verify security tools are defined in pyproject.toml."""
        pyproject_path = REPO_ROOT / "pyproject.toml"
        content = pyproject_path.read_text()

        assert "pip-audit" in content, "pip-audit should be in security dependencies"
        assert "cyclonedx-bom" in content, "cyclonedx-bom should be in security dependencies"

    def test_gitlab_ci_has_security_stages(self) -> None:
        """Verify GitLab CI retains dependency (SCA) vulnerability scanning.

        The pipeline was trimmed to a lean, best-practice essentials set: the
        heavier / niche supply-chain jobs (SBOM generation, container image
        scanning, SLSA provenance, publish + summary aggregation) were removed.
        Dependency scanning with pip-audit (a runtime-CVE gate) is the retained
        security essential.
        """
        ci_path = REPO_ROOT / ".gitlab-ci.yml"
        content = ci_path.read_text(encoding="utf-8")

        # Retained security stage + dependency (SCA) scan
        assert "security" in content, "CI should have security stage"
        assert "dependency-scan" in content, "CI should have dependency-scan job"

        # Retained tooling: pip-audit + its CycloneDX report
        assert "pip-audit" in content, "CI should use pip-audit"
        assert "cyclonedx" in content, "CI should emit a CycloneDX report"

    def test_gitlab_ci_has_oci_labels(self) -> None:
        """Verify Docker builds include OCI labels for provenance."""
        ci_path = REPO_ROOT / ".gitlab-ci.yml"
        content = ci_path.read_text(encoding="utf-8")

        # OCI annotation labels
        assert "org.opencontainers.image.created" in content
        assert "org.opencontainers.image.revision" in content
        assert "org.opencontainers.image.source" in content
        assert "org.opencontainers.image.version" in content

    def test_security_scan_script_exists(self) -> None:
        """Verify security scan script exists and is valid Python."""
        script_path = REPO_ROOT / "scripts" / "security_scan.py"
        assert script_path.exists(), "security_scan.py should exist"

        # Check it's valid Python by compiling (use UTF-8 encoding)
        content = script_path.read_text(encoding="utf-8")
        compile(content, str(script_path), "exec")

    def test_pip_audit_ignore_file_exists(self) -> None:
        """Verify pip-audit ignore file exists."""
        ignore_path = REPO_ROOT / ".pip-audit-ignore.toml"
        assert ignore_path.exists(), ".pip-audit-ignore.toml should exist"

    def test_security_documentation_exists(self) -> None:
        """Verify security documentation exists."""
        doc_path = REPO_ROOT / "docs" / "16_supply_chain_security.md"
        assert doc_path.exists(), "Supply chain security docs should exist"

        content = doc_path.read_text()
        assert "SBOM" in content, "Docs should cover SBOM"
        assert "CycloneDX" in content, "Docs should cover CycloneDX"
        assert "pip-audit" in content, "Docs should cover pip-audit"
        assert "Trivy" in content, "Docs should cover Trivy"
        assert "SLSA" in content, "Docs should cover SLSA"

    def test_ci_artifacts_configured(self) -> None:
        """Verify CI still produces the dependency-audit artifact.

        Trimmed to the lean essentials set - the SBOM / container-scan / SLSA
        provenance / security-summary artifacts were removed with their jobs.
        The pip-audit dependency report is the retained supply-chain artifact.
        """
        ci_path = REPO_ROOT / ".gitlab-ci.yml"
        content = ci_path.read_text(encoding="utf-8")

        assert "pip-audit-report.json" in content, "CI should produce pip-audit-report.json"

    def test_ci_gitlab_reports_configured(self) -> None:
        """Verify GitLab native reporting is configured."""
        ci_path = REPO_ROOT / ".gitlab-ci.yml"
        content = ci_path.read_text(encoding="utf-8")

        # GitLab native reports
        assert "reports:" in content
        assert "cyclonedx:" in content, "Should use CycloneDX reports"

    def test_redeploy_script_does_not_hardcode_ssh_password(self) -> None:
        """Verify production redeploy credentials are supplied at runtime."""
        script_path = REPO_ROOT / "redeploy.py"
        content = script_path.read_text(encoding="utf-8")

        assert "paramiko" not in content.lower()
        assert "DEPLOY_SSH_KEY_FILENAME" in content
        assert "StrictHostKeyChecking=" in content
        assert "'yes' if strict_host_key else 'accept-new'" in content
        assert "DEPLOY_SSH_PASSWORD is intentionally unsupported" in content
        assert 'password="' not in content
        assert "password='" not in content


class TestSBOMFormat:
    """Test SBOM generation format compliance."""

    @pytest.mark.skipif(
        importlib.util.find_spec("cyclonedx") is None,
        reason="cyclonedx not installed",
    )
    def test_sbom_generation_produces_valid_json(self, tmp_path) -> None:
        """Verify SBOM generation produces valid CycloneDX JSON."""
        output_file = tmp_path / "test-sbom.json"
        from cyclonedx.model.bom import Bom
        from cyclonedx.model.component import Component, ComponentType
        from cyclonedx.output import make_outputter
        from cyclonedx.schema import OutputFormat, SchemaVersion

        bom = Bom()
        bom.components.add(Component(type=ComponentType.LIBRARY, name="demo", version="1.0.0"))
        outputter = make_outputter(bom, OutputFormat.JSON, SchemaVersion.V1_6)
        content = outputter.output_as_string()
        output_file.write_text(content, encoding="utf-8")

        sbom = json.loads(content)

        # CycloneDX required fields
        assert "bomFormat" in sbom, "SBOM should have bomFormat"
        assert sbom["bomFormat"] == "CycloneDX", "Should be CycloneDX format"
        assert "specVersion" in sbom, "SBOM should have specVersion"
        assert "components" in sbom, "SBOM should have components"
