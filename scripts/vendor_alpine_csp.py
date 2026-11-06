"""Vendor pinned Alpine CSP and its matching collapse plugin.

Usage: python scripts/vendor_alpine_csp.py [--check | --force]

Alpine 3.17.5 still reads window.fence while collecting global values for its
CSP evaluator. Skip that unused, deprecated advertising API in the existing
upstream exclusion list. Verify both downloaded and patched bytes.
Upstream: https://github.com/alpinejs/alpine/blob/v3.17.5/packages/csp/src/parser.js
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

ALPINE_VERSION = "3.17.5"
ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "src/app/templates/static/vendor"
# package: (upstream SHA-256, installed SHA-256)
ASSETS = {
    "csp": (
        "48c170c92032e527cbae71b8ce75cf1f96ca06fa869a6120ef0fe438d8e92c36",
        "7c58fa94714b0266cf1fd0f7026bcfd7b9e33911d12a74c4ee39539a745fac50",
    ),
    "collapse": (
        "c7661d4e2cf0465e3cd693190debb5f592ac72dcc4cfe650581273767558b27b",
        "c7661d4e2cf0465e3cd693190debb5f592ac72dcc4cfe650581273767558b27b",
    ),
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _patch_csp(data: bytes) -> bytes:
    exclusion = b'e==="styleMedia"||e==="sharedStorage"'
    if data.count(exclusion) != 1:
        raise ValueError("Alpine global exclusion list changed; review the upstream source")
    return data.replace(exclusion, exclusion + b'||e==="fence"')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--force", action="store_true", help="Download even if already verified")
    mode.add_argument(
        "--check", action="store_true", help="Verify installed files without downloading"
    )
    args = parser.parse_args(argv)
    for package, (upstream_hash, installed_hash) in ASSETS.items():
        target = VENDOR / f"alpine-{package}-{ALPINE_VERSION}.min.js"
        if not args.force and target.is_file() and _sha256(target.read_bytes()) == installed_hash:
            print(f"[OK] {target.relative_to(ROOT)} matches pinned SHA-256")
            continue
        if args.check:
            print(f"[FAIL] {target.relative_to(ROOT)} missing or changed", file=sys.stderr)
            return 1
        url = f"https://cdn.jsdelivr.net/npm/@alpinejs/{package}@{ALPINE_VERSION}/dist/cdn.min.js"
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 - pinned URL and hash
            payload = response.read()
        if _sha256(payload) != upstream_hash:
            print(f"[FAIL] Upstream SHA-256 mismatch: {package}", file=sys.stderr)
            return 1
        if package == "csp":
            payload = _patch_csp(payload)
        if _sha256(payload) != installed_hash:
            print(f"[FAIL] Installed SHA-256 mismatch: {package}", file=sys.stderr)
            return 1
        target.write_bytes(payload)
        print(f"[OK] Wrote {target.relative_to(ROOT)} ({len(payload)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
