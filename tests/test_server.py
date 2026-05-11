"""HTTP-level tests for the FastAPI server."""

import base64
import io
import os


def _make_blob(size: int = 64) -> tuple[bytes, bytes]:
    """Return (ciphertext, iv) — opaque bytes that match the server's shape
    requirements (12-byte IV, non-empty ciphertext)."""
    return os.urandom(size), os.urandom(12)


def _upload(
    client, ciphertext: bytes, iv: bytes, filename: str = "f.bin", ttl: int = 60, downloads: int = 1
):
    return client.post(
        "/api/files",
        data={
            "iv": base64.b64encode(iv).decode(),
            "filename": filename,
            "ttl_seconds": str(ttl),
            "max_downloads": str(downloads),
        },
        files={"blob": ("blob", io.BytesIO(ciphertext), "application/octet-stream")},
    )


def test_healthz_returns_ok(app_client):
    client, _ = app_client
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_upload_returns_unguessable_id(app_client):
    client, _ = app_client
    ct, iv = _make_blob()
    r = _upload(client, ct, iv)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["id"], str)
    # 16 random bytes -> 22-char urlsafe base64.
    assert 20 <= len(body["id"]) <= 32
    assert body["downloads_remaining"] == 1
    assert body["size_bytes"] == len(ct)


def test_download_returns_ciphertext_verbatim(app_client):
    client, _ = app_client
    ct, iv = _make_blob(128)
    up = _upload(client, ct, iv, filename="secret.bin").json()
    r = client.get(f"/api/files/{up['id']}")
    assert r.status_code == 200
    assert r.content == ct  # server must echo bytes verbatim
    assert r.headers["x-vanishdrop-iv"] == base64.b64encode(iv).decode()
    assert r.headers["x-vanishdrop-filename"] == "secret.bin"


def test_second_download_returns_404(app_client):
    client, _ = app_client
    ct, iv = _make_blob()
    up = _upload(client, ct, iv).json()
    assert client.get(f"/api/files/{up['id']}").status_code == 200
    r2 = client.get(f"/api/files/{up['id']}")
    assert r2.status_code == 404
    assert r2.json()["detail"] == "not_found"


def test_max_downloads_three(app_client):
    client, _ = app_client
    ct, iv = _make_blob()
    up = _upload(client, ct, iv, downloads=3).json()
    for i in range(3):
        assert client.get(f"/api/files/{up['id']}").status_code == 200, f"read {i+1}"
    assert client.get(f"/api/files/{up['id']}").status_code == 404


def test_meta_is_non_consuming(app_client):
    client, _ = app_client
    ct, iv = _make_blob()
    up = _upload(client, ct, iv).json()
    for _ in range(5):
        m = client.get(f"/api/files/{up['id']}/meta")
        assert m.status_code == 200
        assert m.json()["downloads_remaining"] == 1
    # Now actually consume.
    assert client.get(f"/api/files/{up['id']}").status_code == 200
    # And meta must 404 after consumption.
    assert client.get(f"/api/files/{up['id']}/meta").status_code == 404


def test_rejects_invalid_iv(app_client):
    client, _ = app_client
    ct = os.urandom(64)
    r = client.post(
        "/api/files",
        data={
            "iv": "not-base64!",
            "filename": "x",
            "ttl_seconds": "60",
            "max_downloads": "1",
        },
        files={"blob": ("blob", io.BytesIO(ct), "application/octet-stream")},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "invalid_iv"


def test_rejects_short_iv(app_client):
    client, _ = app_client
    ct = os.urandom(64)
    r = client.post(
        "/api/files",
        data={
            "iv": base64.b64encode(b"\x00" * 11).decode(),  # 11 bytes, not 12
            "filename": "x",
            "ttl_seconds": "60",
            "max_downloads": "1",
        },
        files={"blob": ("blob", io.BytesIO(ct), "application/octet-stream")},
    )
    assert r.status_code == 400


def test_rejects_invalid_filename(app_client):
    client, _ = app_client
    ct, iv = _make_blob()
    for bad in ["../escape", "a/b", "a\\b", "a\x00b"]:
        r = _upload(client, ct, iv, filename=bad)
        assert r.status_code == 400


def test_rejects_blob_too_large(app_client):
    client, app_module = app_client
    # Set a tiny cap so we don't have to allocate 32 MiB in a test.
    monkey_cap = 256
    app_module.MAX_BLOB_BYTES = monkey_cap
    ct = os.urandom(monkey_cap + 1)
    iv = os.urandom(12)
    r = _upload(client, ct, iv)
    assert r.status_code == 413


def test_ttl_clamped_to_minimum(app_client):
    client, _ = app_client
    ct, iv = _make_blob()
    r = _upload(client, ct, iv, ttl=1).json()  # below 60s floor
    import time as _time

    assert r["expires_at"] - int(_time.time()) >= 50


def test_invalid_id_returns_400(app_client):
    client, _ = app_client
    r = client.get("/api/files/has%21bang%21chars")
    assert r.status_code in (400, 404)
    r = client.get("/api/files/short")
    assert r.status_code in (400, 404)


def test_viewer_route_returns_html(app_client):
    """The /d/<id> SPA shell falls back to the built index.html, or 503 if
    the frontend isn't built. In the test env we tolerate either — what we
    care about is that the route is wired up and doesn't 404 on a valid id.
    """
    client, _ = app_client
    r = client.get("/d/aaaaaaaaaaaaaaaaaaaaaa")
    assert r.status_code in (200, 503)
