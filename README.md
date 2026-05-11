# VanishDrop

End-to-end encrypted one-time file sharing. Drop a file, get a URL. Open the URL once — the browser decrypts the file locally and the server copy is gone forever.

- **Backend** — Python 3.10+ · FastAPI · uvicorn · SQLite + filesystem.
- **Frontend** — Vue 3 + Vite + TypeScript.
- **Crypto** — Web Crypto API: AES-GCM with a 256-bit key and 96-bit IV. Key is generated in the browser and lives in the URL fragment (`#k=…`); browsers never send fragments in HTTP, so the server cannot decrypt.
- **Trust model** — if the server operator is malicious, they learn that a file of *some size* existed for *some duration*, but cannot read its contents.

## Quick start

```bash
git clone https://github.com/repobility/vanishdrop.git
cd vanishdrop

# Backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Frontend (build once)
cd frontend && npm install && npm run build && cd ..

# Run
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>, drag a file, copy the URL.

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/files` | multipart: `blob`, `iv`, `filename`, `ttl_seconds`, `max_downloads` | `{ id, expires_at, downloads_remaining, size_bytes }` |
| `GET`  | `/api/files/{id}` | — | raw ciphertext body + `X-VanishDrop-IV` / `X-VanishDrop-Filename` / `X-VanishDrop-Remaining` headers; decrements the download counter |
| `GET`  | `/api/files/{id}/meta` | — | non-consuming peek at filename, size, expiry, remaining |
| `GET`  | `/d/{id}` | — | viewer SPA (key parsed from URL fragment client-side) |
| `GET`  | `/healthz` | — | liveness probe |

## License

MIT.
