# Architecture

A Vue 3 SPA talking to a FastAPI backend. The backend stores only
ciphertext blobs; the AES-GCM key never leaves the browser.

```
       ┌──────────────────────────────────────┐
       │           Compose page               │
       │           (frontend/src/components/  │
       │            Compose.vue)              │
       │                                      │
       │  1. user drags a file                │
       │  2. crypto.getRandomValues(32) → key │
       │  3. crypto.getRandomValues(12) → IV  │
       │  4. crypto.subtle.encrypt(           │
       │       AES-GCM, key, iv, plaintext)   │
       │  5. multipart POST { blob, iv,       │
       │     filename, ttl, max_downloads }   │
       └──────────────────────────────────────┘
                          │
                          ▼  HTTPS
   ┌────────────────────────────────────────────────────────────────────┐
   │                    FastAPI (app/main.py)                           │
   │                                                                    │
   │  POST /api/files               → mint id, stream blob to disk,     │
   │                                  insert metadata row in SQLite     │
   │  GET  /api/files/{id}          → atomic read-then-delete-or-      │
   │                                  decrement (download)              │
   │  GET  /api/files/{id}/meta     → non-consuming peek                │
   │  GET  /d/{id}                  → SPA viewer shell                  │
   │  GET  /                        → SPA compose shell                 │
   │  GET  /healthz                 → liveness probe                    │
   │                                                                    │
   │  Storage:                                                          │
   │    SQLite `files` table { id, filename, iv, size, expires,         │
   │                          downloads_remaining, created }            │
   │    data/blobs/{id} — raw ciphertext bytes (1 file per record)      │
   │                                                                    │
   │  Periodic sweep removes expired or zero-downloads records.         │
   │  The server holds NO keys. It cannot decrypt anything.             │
   └────────────────────────────────────────────────────────────────────┘
                          │
                          ▼  HTTPS
       ┌──────────────────────────────────────┐
       │           Viewer page                │
       │           (Viewer.vue)               │
       │                                      │
       │  6. parse /d/<id>#k=<key>            │
       │  7. peek /api/files/:id/meta         │
       │     → show confirm with filename     │
       │  8. user confirms                    │
       │  9. GET /api/files/:id consumes,     │
       │     returns ct + IV header           │
       │ 10. crypto.subtle.decrypt(           │
       │       AES-GCM, key, iv, ct)          │
       │ 11. trigger Blob download to disk    │
       └──────────────────────────────────────┘
```

## Layers

### 1. Crypto (`frontend/src/crypto.ts`)

Pure browser code; uses `crypto.subtle` and `crypto.getRandomValues`.

- `encryptFile(plaintext: ArrayBuffer)` — generates a 32-byte key and
  12-byte IV, encrypts via AES-GCM, returns `{ ciphertext, iv, key }`.
- `decryptFile(ct, iv, key)` — returns the plaintext `ArrayBuffer` or
  `null` on every failure mode (wrong key, tampered ciphertext, bad
  IV). Callers cannot distinguish, by design.
- Base64 + base64url helpers for putting the raw key into a URL
  fragment without URL-encoding.

### 2. Compose flow (`frontend/src/components/Compose.vue`)

State-free Vue 3 component using the Composition API (`<script setup
lang="ts">`). Reads the file as an `ArrayBuffer`, calls
`encryptFile`, posts the ciphertext + IV + filename + TTL +
max-downloads to `/api/files`, then builds
`location.origin + "/d/" + id + "#k=" + rawKeyToFragment(key)`.

The plaintext is read into memory in one chunk (max 32 MiB per server
cap). The original `File` object is dropped after submission; the
only copy of the key is in the URL we just built.

### 3. Viewer flow (`frontend/src/components/Viewer.vue`)

Reads `id` from `location.pathname` and `k` from `location.hash`.
Peeks the `/meta` endpoint to show a confirm dialog (filename, size,
remaining) *without* consuming the download. On confirm, fetches
`/api/files/:id` (which atomically decrements the counter or deletes
the record) and decrypts client-side. The decrypted bytes are wrapped
in a `Blob` and saved via a synthetic `<a download>` click.

Failure modes (`null` from decrypt, 404, 410, network error) are
rendered as distinct UI states.

### 4. Server (`app/main.py`)

FastAPI with three responsibility groups:

- **Static SPA** — mounted from `frontend/dist/` if it exists.
- **Wire validation** — `_valid_id`, IV-length check, filename
  sanitization, blob size cap, TTL clamp.
- **CRUD with atomic consume** — single SQLite transaction for the
  download flow: read the record, decide whether to delete or
  decrement, commit, then read the blob from disk and unlink it on
  the final download.

The store is a single SQLite database file at `data/vanishdrop.db`
plus one ciphertext file per record in `data/blobs/<id>`. The
in-process design is single-process by default; multi-replica
deployments would back the SQLite store with Postgres and the blob
directory with S3-compatible object storage.

### 5. Tests (`tests/`)

Three suites under `pytest`:

- `tests/test_server.py` — HTTP API: healthz, upload, peek, download,
  one-time-property, validation rejections, TTL clamping, viewer
  shell.
- `tests/test_auth.py` — capability-URL invariants: id-alone-is-not-
  decryption, atomic one-time download, ids ≥128-bit, generic
  not_found, /meta is non-consuming, no DELETE/PUT/list.
- `tests/conftest.py` — fixture spinning up a fresh app rooted in a
  per-test temp directory.

## Wire protocol summary

| Direction       | Method | Path                       | Payload                                                    |
| --------------- | ------ | -------------------------- | ---------------------------------------------------------- |
| client → server | POST   | `/api/files`               | multipart: `blob`, `iv` (b64), `filename`, `ttl_seconds`, `max_downloads` |
| client → server | GET    | `/api/files/{id}/meta`     | —                                                          |
| client → server | GET    | `/api/files/{id}`          | —                                                          |
| server → client | POST resp | —                       | `{ id, expires_at, downloads_remaining, size_bytes }`       |
| server → client | meta resp | —                       | `{ filename, size_bytes, expires_at, downloads_remaining }` |
| server → client | DL resp   | —                       | raw ciphertext body + `X-VanishDrop-IV`, `X-VanishDrop-Filename`, `X-VanishDrop-Remaining` |

## Threat model summary

See [SECURITY.md](SECURITY.md) for the full breakdown. Headline:

| Adversary                         | Defended?                               |
| --------------------------------- | --------------------------------------- |
| Honest-but-curious operator       | ✅ confidentiality and integrity        |
| Passive network observer (w/ TLS) | ✅                                      |
| Active MITM (w/ TLS)              | ✅ — AES-GCM tag catches tampering      |
| URL leakage (browser history)     | ⚠️ one-time-download is the mitigation |
| Referer leakage from viewer page  | ✅ `no-referrer` meta + CSP             |
| Compromised browser / XSS         | ⚠️ best-effort via strict CSP           |
| Compromised server delivering JS  | ⚠️ trust-the-server-once problem        |
