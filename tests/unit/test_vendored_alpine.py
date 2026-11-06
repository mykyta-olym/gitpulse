"""The pinned upstream runtime receives only the documented compatibility fix."""

from scripts import vendor_alpine_csp as vendor


def test_vendored_runtime_and_plugin_match_their_integrity_pins():
    assert vendor.main(["--check"]) == 0
    installed = (vendor.VENDOR / f"alpine-csp-{vendor.ALPINE_VERSION}.min.js").read_bytes()
    upstream = installed.replace(b'||e==="fence"', b"")
    assert vendor._sha256(upstream) == vendor.ASSETS["csp"][0]
    assert vendor._patch_csp(upstream) == installed


def test_integrity_check_rejects_a_changed_runtime(tmp_path, monkeypatch):
    for package in vendor.ASSETS:
        filename = f"alpine-{package}-{vendor.ALPINE_VERSION}.min.js"
        (tmp_path / filename).write_bytes((vendor.VENDOR / filename).read_bytes())
    (tmp_path / f"alpine-csp-{vendor.ALPINE_VERSION}.min.js").write_bytes(b"changed")
    monkeypatch.setattr(vendor, "VENDOR", tmp_path)
    monkeypatch.setattr(vendor, "ROOT", tmp_path)
    assert vendor.main(["--check"]) == 1
