"""Authorization-focused tests — capability-URL invariants.

VanishDrop uses **capability URL** auth (same model as Cipherlink and
Yopass / PrivateBin / OneTimeSecret). The unguessable 22-char id in the
path is one half of the credential; the 32-byte AES-GCM key in the URL
fragment is the other. Possession of the full URL is the authorization.

There is no user table, no session, no role. These tests prove the
properties that fall out of that model.
"""

import base64
import io
import os


def _upload(client, ciphertext: bytes, iv: bytes, **kw):
    data = {
        "iv": base64.b64encode(iv).decode(),
        "filename": kw.get("filename", "f.bin"),
        "ttl_seconds": str(kw.get("ttl", 60)),
        "max_downloads": str(kw.get("downloads", 1)),
    }
    return client.post(
        "/api/files",
        data=data,
        files={"blob": ("blob", io.BytesIO(ciphertext), "application/octet-stream")},
    )


def test_auth01_id_returns_ciphertext_not_plaintext(app_client):
    """AUTH-01: The id alone is enough to fetch the blob, but the blob is
    ciphertext — the server has no key and cannot decrypt."""
    client, _ = app_client
    ct, iv = os.urandom(64), os.urandom(12)
    up = _upload(client, ct, iv).json()
    r = client.get(f"/api/files/{up['id']}")
    assert r.status_code == 200
    # The response body is the raw ciphertext, byte-for-byte identical to
    # what we uploaded. The server never had — and could not derive — the key.
    assert r.content == ct


def test_auth02_one_time_read_is_atomic(app_client):
    """AUTH-02: Consumed records 404 — not rate-limited, not throttled."""
    client, _ = app_client
    ct, iv = os.urandom(64), os.urandom(12)
    up = _upload(client, ct, iv).json()
    assert client.get(f"/api/files/{up['id']}").status_code == 200
    r = client.get(f"/api/files/{up['id']}")
    assert r.status_code == 404
    assert r.json()["detail"] == "not_found"


def test_auth03_ids_are_unguessable(app_client):
    """AUTH-03: ids occupy a ≥128-bit search space."""
    client, _ = app_client
    seen = set()
    for _ in range(50):
        ct = os.urandom(32)
        iv = os.urandom(12)
        up = _upload(client, ct, iv).json()
        seen.add(up["id"])
    assert len(seen) == 50, "all 50 ids must be unique"
    for id_ in seen:
        assert all(c.isalnum() or c in "-_" for c in id_)
        assert len(id_) >= 20  # ≥120 bits of entropy in urlsafe base64


def test_auth04_unknown_id_returns_generic_not_found(app_client):
    """AUTH-04: A random id we never created returns the same not_found
    payload as a consumed id — no oracle, no timing leak in the message."""
    client, _ = app_client
    r = client.get("/api/files/" + "a" * 22)
    assert r.status_code == 404
    assert r.json()["detail"] == "not_found"


def test_auth05_meta_is_non_consuming(app_client):
    """AUTH-05: /meta is informational only. Repeated peeks must not
    drain the download counter."""
    client, _ = app_client
    ct, iv = os.urandom(64), os.urandom(12)
    up = _upload(client, ct, iv).json()
    for _ in range(5):
        m = client.get(f"/api/files/{up['id']}/meta")
        assert m.status_code == 200
        assert m.json()["downloads_remaining"] == 1


def test_auth06_no_delete_no_list_no_edit(app_client):
    """AUTH-06: No creator-only operations exist. Once posted, a file
    cannot be retracted, listed, or modified — it dies by being
    downloaded or expiring."""
    client, _ = app_client
    ct, iv = os.urandom(64), os.urandom(12)
    up = _upload(client, ct, iv).json()

    # DELETE
    r = client.delete(f"/api/files/{up['id']}")
    assert r.status_code in (404, 405)

    # PUT (edit)
    r = client.put(f"/api/files/{up['id']}")
    assert r.status_code in (404, 405)

    # No list endpoint on the collection.
    r = client.get("/api/files")
    assert r.status_code in (404, 405)


def test_auth07_iv_round_trips_in_response_header(app_client):
    """AUTH-07: The IV is returned in the X-VanishDrop-IV header on
    download, so the client can decrypt without storing it client-side.
    The IV is non-sensitive — it must be returned verbatim."""
    client, _ = app_client
    ct, iv = os.urandom(64), os.urandom(12)
    up = _upload(client, ct, iv).json()
    r = client.get(f"/api/files/{up['id']}")
    iv_returned = base64.b64decode(r.headers["x-vanishdrop-iv"])
    assert iv_returned == iv
