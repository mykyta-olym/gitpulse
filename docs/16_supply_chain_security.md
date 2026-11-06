# Software Supply Chain Security

> **Documentation Status (2026-05-31):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.


This document describes the supply-chain security practices implemented for the GitPulse project.

## Overview

The project implements modern software supply-chain security following industry best practices:

| Practice | Tool | Standard |
|----------|------|----------|
| SBOM Generation | cyclonedx-bom | CycloneDX 1.5 |
| Dependency Scanning | pip-audit | OSV Database |
| Container Scanning | Trivy | CVE/NVD |
| Provenance | Custom SLSA-lite | SLSA v0.2 |

## CI Pipeline Stages

```
lint -> security -> test -> build -> scan -> publish
```

### Security Stage Jobs

1. **dependency-scan**: Scans Python dependencies for known vulnerabilities
2. **sbom-generate**: Creates Software Bill of Materials in CycloneDX format

### Scan Stage Jobs

1. **container-scan-api**: Scans the API container image with Trivy
2. **container-scan-worker**: Scans the Worker container image with Trivy

### Publish Stage Jobs

1. **publish-artifacts**: Uploads SBOM and provenance to GitLab Package Registry
2. **security-summary**: Generates aggregated security report

## Artifacts Generated

Each pipeline run produces the following security artifacts:

| Artifact | Format | Purpose |
|----------|--------|---------|
| `sbom-cyclonedx.json` | CycloneDX JSON | Software inventory |
| `sbom-cyclonedx.xml` | CycloneDX XML | Alternative SBOM format |
| `pip-audit-report.json` | JSON | Dependency vulnerabilities |
| `pip-audit-cyclonedx.json` | CycloneDX | Vulnerabilities as SBOM |
| `build-provenance.json` | SLSA v0.2 | Build attestation |
| `trivy-api-report.json` | Trivy JSON | Container vulnerabilities |
| `trivy-api-sbom.json` | CycloneDX | Container SBOM |
| `security-report.md` | Markdown | Human-readable summary |

## Local Development

### Install Security Tools

```bash
pip install -e ".[security]"
```

The `security` extra intentionally contains only `pip-audit` and CycloneDX
tooling. Load-test tooling is isolated in the `load` extra so dependency scans
for normal development and security work do not include load-test-only packages.

### Run Dependency Scan Locally

```bash
# Scan installed packages
pip-audit

# Output as JSON
pip-audit --format json --output audit-report.json

# Output as CycloneDX
pip-audit --format cyclonedx-json --output audit-cyclonedx.json
```

### Generate SBOM Locally

```bash
# From installed environment
cyclonedx-py environment --spec-version 1.5 --output-format JSON --output-file sbom.json

# From requirements file
pip freeze > requirements-lock.txt
cyclonedx-py requirements requirements-lock.txt --spec-version 1.5 --output-format JSON --output-file sbom-reqs.json
```

### Scan Container Image Locally

```bash
# Install Trivy (macOS)
brew install trivy

# Install Trivy (Linux)
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Scan built image
docker build -t gitpulse:local .
trivy image gitpulse:local

# Output as JSON
trivy image gitpulse:local --format json --output trivy-local.json

# Generate container SBOM
trivy image gitpulse:local --format cyclonedx --output container-sbom.json
```

## SLSA Provenance

The build process generates SLSA (Supply-chain Levels for Software Artifacts) provenance attestation. This provides:

- **Build Identity**: Links artifacts to specific CI pipeline and job
- **Source Identity**: Links to exact Git commit
- **Build Configuration**: Records Dockerfile and build context
- **Reproducibility**: Captures build environment details

### Provenance Schema

```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "subject": [
    {
      "name": "gitpulse:<commit-sha>",
      "digest": { "sha256": "<image-digest>" }
    }
  ],
  "predicate": {
    "builder": { "id": "gitlab-runner" },
    "buildType": "https://gitlab.com/gitlab-ci",
    "invocation": {
      "configSource": {
        "uri": "git+<repo-url>@refs/heads/<branch>",
        "digest": { "sha1": "<commit-sha>" },
        "entryPoint": ".gitlab-ci.yml:docker-build"
      }
    },
    "materials": [
      {
        "uri": "git+<repo-url>",
        "digest": { "sha1": "<commit-sha>" }
      }
    ]
  }
}
```

### SLSA Level Achieved

This implementation achieves **SLSA Level 1** (Build):
- Build process is defined in version-controlled config
- Provenance is generated automatically
- Provenance includes source and build info

For SLSA Level 2+, you would need:
- Hosted build service with isolation
- Signed provenance
- Build service hardening

## Vulnerability Response

### Critical Vulnerabilities

If critical vulnerabilities are found:

1. **Immediate**: Pipeline continues but marks job as failed
2. **Review**: Check `pip-audit-report.json` for details
3. **Remediate**: Update affected dependency
4. **Verify**: Re-run pipeline to confirm fix

### Suppressing False Positives

Create `.pip-audit-ignore.toml` to suppress known false positives:

```toml
[[vulnerabilities]]
id = "PYSEC-2024-XXXX"
reason = "Not applicable: feature not used"
```

Then run:
```bash
pip-audit --ignore-vulns .pip-audit-ignore.toml
```

## Integration with Security Tools

### GitLab Security Dashboard

The CI artifacts are configured to integrate with GitLab's Security Dashboard:
- CycloneDX reports are uploaded to `reports.cyclonedx`
- SARIF reports can be viewed in MR security widgets

### External SBOM Consumers

SBOMs can be consumed by:
- Dependency-Track
- OWASP Dependency-Check
- Snyk
- Sonatype Nexus

Download from GitLab Package Registry:
```bash
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.example.com/api/v4/projects/<id>/packages/generic/sbom/<version>/sbom-cyclonedx.json"
```

## Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONTAINER_SCANNING_DISABLED` | `false` | Skip container scanning |
| `SBOM_FORMAT` | `cyclonedx` | SBOM output format |

To disable container scanning for faster pipelines:
```yaml
variables:
  CONTAINER_SCANNING_DISABLED: "true"
```

## Operational Runbook

### Viewing Scan Results

1. Navigate to CI/CD -> Pipelines -> Select pipeline
2. Download artifacts from security jobs
3. Review `security-report.md` for summary

### Downloading SBOM

```bash
# From pipeline artifacts
curl --header "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.example.com/api/v4/projects/<id>/jobs/<job_id>/artifacts/sbom-cyclonedx.json"

# From package registry (after publish)
curl --header "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.example.com/api/v4/projects/<id>/packages/generic/sbom/<version>/sbom-cyclonedx.json"
```

### Investigating Vulnerabilities

```bash
# Get detailed vulnerability info
pip-audit --format json | jq '.dependencies[] | select(.vulns | length > 0)'

# Check specific package
pip-audit --requirement <(echo "package==version")
```

### Emergency Patching

If critical vulnerability requires immediate action:

```bash
# 1. Identify affected package
pip-audit --format json | jq '.dependencies[] | select(.vulns[].id == "CVE-XXXX-YYYY")'

# 2. Check for fixed version
pip index versions <package>

# 3. Update pyproject.toml with minimum safe version
# Edit: "package>=X.Y.Z"  # CVE-XXXX-YYYY fix

# 4. Rebuild and verify
pip install -e "."
pip-audit

# 5. Commit and push
git commit -am "fix(security): patch CVE-XXXX-YYYY in <package>"
git push
```

## Compliance Mapping

| Requirement | Implementation |
|-------------|----------------|
| EO 14028 (US) | SBOM generation, vulnerability scanning |
| NIST SP 800-218 | Secure development practices |
| CIS Controls | Software inventory, vulnerability management |
| SOC 2 | Change management, security monitoring |

## References

- [CycloneDX Specification](https://cyclonedx.org/specification/overview/)
- [SLSA Framework](https://slsa.dev/)
- [pip-audit Documentation](https://github.com/pypa/pip-audit)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [GitLab Security Scanning](https://docs.gitlab.com/ee/user/application_security/)
