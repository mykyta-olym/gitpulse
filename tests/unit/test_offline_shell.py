"""The offline shell's cached HTML must authorize its own theme bootstrap."""

import re

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import _mount_static
from app.middleware.security import SecurityHeadersMiddleware


def test_offline_shell_nonce_matches_its_strict_policy() -> None:
    app = FastAPI()
    _mount_static(app)
    app.add_middleware(SecurityHeadersMiddleware)
    client = TestClient(app)

    nonces = []
    for _ in range(2):
        response = client.get("/static/offline.html")
        assert response.status_code == 200
        match = re.search(r'<script nonce="([^"]+)"', response.text)
        assert match is not None
        nonce = match[1]
        policy = response.headers["content-security-policy"]
        assert f"'nonce-{nonce}'" in policy
        assert "'strict-dynamic'" in policy
        assert "{{ csp_nonce }}" not in response.text
        nonces.append(nonce)
    assert nonces[0] != nonces[1]
