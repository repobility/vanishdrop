"""
VanishDrop — end-to-end encrypted one-time file sharing.

Trust model: the server holds only ciphertext blobs and metadata. The
AES-GCM key is generated in the browser and travels in the URL fragment
(#k=...), which browsers never send in HTTP requests. The server cannot
decrypt a file even with full access to its own disk and logs.
"""

import base64
import logging
import os
import secrets
import sqlite3
import time
from binascii import Error as BinasciiError
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

log = logging.getLogger("vanishdrop")

# ----- config -----
PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "127.0.0.1")
ROOT = Path(__file__).resolve().parent.parent
BLOBS_DIR = ROOT / "data" / "blobs"
DB_PATH = ROOT / "data" / "vanishdrop.db"
FRONTEND_DIR = ROOT / "frontend" / "dist"
MAX_BLOB_BYTES = 32 * 1024 * 1024  # 32 MiB
MIN_TTL_SECONDS = 60
MAX_TTL_SECONDS = 7 * 24 * 3600  # 7 days
DEFAULT_TTL_SECONDS = 24 * 3600
MAX_DOWNLOADS = 100

BLOBS_DIR.mkdir(parents=True, exist_ok=True)


# ----- store -----
def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            iv TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            downloads_remaining INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        )
        """)
    return conn


def gen_id() -> str:
    # 16 random bytes, urlsafe base64. ~128-bit search space.
    return base64.urlsafe_b64encode(secrets.token_bytes(16)).rstrip(b"=").decode("ascii")


def blob_path(id_: str) -> Path:
    # IDs are validated before this is called; the filename is bounded
    # and contains only urlsafe base64 characters.
    return BLOBS_DIR / id_


# ----- app -----
app = FastAPI(title="VanishDrop", description="Encrypted one-time file sharing.")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Strict security headers on every response.

    - Content-Security-Policy locks the page down to same-origin scripts
      and styles (no third-party origins, no inline JS).
    - Referrer-Policy 'no-referrer' prevents the URL fragment from
      leaking via the Referer header when the viewer page links out.
    - X-Frame-Options + frame-ancestors block embedding.
    """
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; "
        "script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "connect-src 'self'; base-uri 'self'; "
        "form-action 'none'; frame-ancestors 'none'"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/healthz")
def healthz():
    with db() as conn:
        n = conn.execute("SELECT COUNT(*) AS c FROM files").fetchone()["c"]
    return {"ok": True, "stored": n}


@app.post("/api/files")
async def upload(
    blob: UploadFile = File(...),
    iv: str = Form(...),
    filename: str = Form(...),
    ttl_seconds: int = Form(DEFAULT_TTL_SECONDS),
    max_downloads: int = Form(1),
):
    # Server-side validation. Browser already enforces these but never trust the client.
    if len(filename) > 255 or "\x00" in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="invalid_filename")

    # IV is base64 of a 12-byte AES-GCM nonce.
    try:
        iv_bytes = base64.b64decode(iv, validate=True)
    except (BinasciiError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="invalid_iv") from exc
    if len(iv_bytes) != 12:
        raise HTTPException(status_code=400, detail="invalid_iv")

    ttl = min(max(int(ttl_seconds), MIN_TTL_SECONDS), MAX_TTL_SECONDS)
    downloads = min(max(int(max_downloads), 1), MAX_DOWNLOADS)

    # Stream the blob to disk with a size cap.
    id_ = gen_id()
    out_path = blob_path(id_)
    total = 0
    try:
        with open(out_path, "wb") as f:
            while True:
                chunk = await blob.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BLOB_BYTES:
                    f.close()
                    out_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="blob_too_large")
                f.write(chunk)
    except HTTPException:
        raise
    except OSError as exc:
        log.warning("upload write failed: %s", exc)
        out_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="upload_failed") from exc

    now = int(time.time())
    with db() as conn:
        conn.execute(
            "INSERT INTO files (id, filename, iv, size_bytes, expires_at, downloads_remaining, created_at) VALUES (?,?,?,?,?,?,?)",
            (id_, filename, iv, total, now + ttl, downloads, now),
        )
        conn.commit()

    # Deliberately NOT logging the id — even debug logs would leak the
    # server half of the capability URL.
    return {
        "id": id_,
        "expires_at": now + ttl,
        "downloads_remaining": downloads,
        "size_bytes": total,
    }


@app.get("/api/files/{file_id}/meta")
def meta(file_id: str):
    if not _valid_id(file_id):
        raise HTTPException(status_code=400, detail="invalid_id")
    with db() as conn:
        row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    if row["expires_at"] <= int(time.time()):
        _purge(file_id)
        raise HTTPException(status_code=410, detail="expired")
    return {
        "filename": row["filename"],
        "size_bytes": row["size_bytes"],
        "expires_at": row["expires_at"],
        "downloads_remaining": row["downloads_remaining"],
    }


@app.get("/api/files/{file_id}")
def download(file_id: str):
    if not _valid_id(file_id):
        raise HTTPException(status_code=400, detail="invalid_id")
    with db() as conn:
        row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="not_found")
        if row["expires_at"] <= int(time.time()):
            _purge(file_id)
            raise HTTPException(status_code=410, detail="expired")

        remaining = row["downloads_remaining"] - 1
        if remaining <= 0:
            conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
        else:
            conn.execute(
                "UPDATE files SET downloads_remaining = ? WHERE id = ?",
                (remaining, file_id),
            )
        conn.commit()

    path = blob_path(file_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="not_found")

    # Build the response with the IV and remaining count in headers; body is the
    # raw ciphertext.
    data = path.read_bytes()
    if remaining <= 0:
        try:
            path.unlink()
        except OSError as exc:
            log.warning("unlink failed for %s: %s", file_id, exc)

    headers = {
        "X-VanishDrop-IV": row["iv"],
        "X-VanishDrop-Filename": row["filename"],
        "X-VanishDrop-Remaining": str(remaining if remaining > 0 else 0),
    }
    return Response(content=data, media_type="application/octet-stream", headers=headers)


def _purge(file_id: str) -> None:
    """Remove a file's DB row and blob on disk."""
    with db() as conn:
        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
    p = blob_path(file_id)
    try:
        p.unlink()
    except OSError as exc:
        log.warning("purge unlink failed for %s: %s", file_id, exc)


def _valid_id(s: str) -> bool:
    if not isinstance(s, str):
        return False
    if not 20 <= len(s) <= 32:
        return False
    # urlsafe base64 alphabet
    return all(c.isalnum() or c in "-_" for c in s)


# ----- SPA viewer route — falls back to the built index.html -----
@app.get("/d/{file_id}")
def viewer_page(file_id: str):
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"error": "frontend not built"}, status_code=503)


# Mount the built Vue frontend at /
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
