"""Regression tests for the local supply-chain scan wrapper."""

from __future__ import annotations

from scripts.security_scan import _parse_json_prefix, _utc_timestamp


def test_parse_json_prefix_ignores_tool_advisory_text() -> None:
    output = 'No known vulnerabilities found\n{"dependencies": [], "fixes": []}\n'

    assert _parse_json_prefix(output) == {"dependencies": [], "fixes": []}


def test_utc_timestamp_uses_z_suffix_without_naive_utcnow() -> None:
    timestamp = _utc_timestamp()

    assert timestamp.endswith("Z")
    assert "+00:00" not in timestamp
