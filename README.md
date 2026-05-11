# VanishDrop

[![CI](https://github.com/repobility/vanishdrop/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/repobility/vanishdrop/actions/workflows/ci.yml)
[![Repobility scan](https://img.shields.io/badge/Repobility-scan-44cc11?logo=shield&logoColor=white)](https://repobility.com/scan/254afa72-3a13-4df6-b6a7-f8a0a14a5965/)
[![Tests — 20/20 passing](https://img.shields.io/badge/tests-20%20%2F%2020-44cc11)](tests/)
[![License — MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python ≥ 3.10](https://img.shields.io/badge/python-%E2%89%A53.10-3776ab?logo=python&logoColor=white)](pyproject.toml)
[![Node ≥ 20](https://img.shields.io/badge/node-%E2%89%A520-black)](.nvmrc)

End-to-end encrypted one-time file sharing. Drop a file, get a URL. Open the URL once — the browser decrypts the file locally and the server copy is gone forever.

- **Backend** — Python 3.10+ · FastAPI · uvicorn · SQLite + filesystem.
- **Frontend** — Vue 3 + Vite + TypeScript.
- **Crypto** — Web Crypto API: AES-GCM with a 256-bit key and 96-bit IV. Key is generated in the browser and lives in the URL fragment (`#k=…`); browsers never send fragments in HTTP, so the server cannot decrypt.
- **Trust model** — if the server operator is malicious, they learn that a file of *some size* existed for *some duration*, but cannot read its contents.

---

## 🛡️ Repobility showcase: different stack, same in-the-loop workflow

This repo is the **third** Repobility-in-the-loop showcase (after [repobility/securechat](https://github.com/repobility/securechat) and [repobility/cipherlink](https://github.com/repobility/cipherlink)). The user prompt was one line — *"do another idea but change the tech used front end and backend"* — so every layer of the stack is different from the prior two showcases:

| | securechat & cipherlink | **VanishDrop** |
|---|---|---|
| Backend lang | Node.js | **Python 3.10+** |
| Backend framework | Express | **FastAPI + uvicorn** |
| Storage | In-memory `Map` | **SQLite + filesystem blobs** |
| Frontend | Vanilla HTML + ES2022 | **Vue 3 + Vite + TypeScript** (real build) |
| Crypto library | TweetNaCl | **Web Crypto API** (`crypto.subtle`) |
| AEAD primitive | XSalsa20-Poly1305 | **AES-GCM (256/96)** |
| Tests | Node native `node:test` | **pytest** |
| Lint / format | ESLint + Prettier | **ruff + black** |

Same trust-model family (server-blind storage, key in URL fragment), but every layer is different tech.

🔗 **[Read the full step-by-step journey in SHOWCASE.md →](SHOWCASE.md)**
🔗 **[See the live Repobility scan (public URL) →](https://repobility.com/scan/254afa72-3a13-4df6-b6a7-f8a0a14a5965/)**

### The Repobility-in-the-loop workflow

```
   ┌────────────────────────────────────────────────────────────────────┐
   │  1.  Claude reads the user's one-line prompt                       │
   │      → emits VanishDrop v0 (Python FastAPI + Vue 3 + Web Crypto)    │
   └────────────────────────────────────────────────────────────────────┘
                                     ↓  git push
   ┌────────────────────────────────────────────────────────────────────┐
   │  2.  Repobility submits a scan via /api/v1/public/scan/             │
   │      → unified panel: legacy + 9-layer + AI fix prompts             │
   └────────────────────────────────────────────────────────────────────┘
                                     ↓  scanner findings
   ┌────────────────────────────────────────────────────────────────────┐
   │  3.  Claude takes one finding cluster at a time, writes a focused   │
   │      commit. Commit message names the rule IDs it closes.           │
   └────────────────────────────────────────────────────────────────────┘
                                     ↓  five commits later
                              🏆  v1.0.0 tagged + GitHub Release
```

### What Repobility caught, and the commit that closed each finding

| Repobility finding family                              | Closed by commit | How                                                                                |
| ------------------------------------------------------ | ---------------- | ---------------------------------------------------------------------------------- |
| 🟠 No test files found                                 | `77fe919`        | pytest suite — 20 cases across server validation and capability-URL invariants.    |
| 🔵 `[AUC005]` No authorization-focused tests          | `77fe919`        | 7 AUTH-* cases in `tests/test_auth.py`.                                            |
| 🟠 `[AUC003]` Object-level routes lack authorization  | `77fe919`        | Capability-URL model documented in `.repobility/access.yml` with scope/owner/tenant markers. |
| 🟡 `[AUC001]` No Repobility access matrix policy      | `77fe919`        | `.repobility/access.yml` with full endpoint table + CWE/OWASP references.          |
| 🟡 No CI/CD configuration found                        | `2bd3b47`        | GH Actions: pytest matrix on Python 3.10–3.13 + Vite build matrix on Node 20/22 + ruff/black + pip-audit + npm audit. |
| 🟡 Public web app has no CSP                           | `7c172f5`        | FastAPI middleware sets strict CSP + Referrer-Policy `no-referrer` + nosniff + frame-ancestors none on every response. |
| 🔵 9-layer `fq.console-leak` / stray `print()`        | `7c172f5`        | `logging.getLogger("vanishdrop")` replaces every `print()`; per-secret debug log removed (it would have leaked file ids). |
| 🟡 Overly broad `except`                               | `7c172f5`        | `except Exception` narrowed to `OSError` / `(BinasciiError, ValueError)` with `from exc`. |
| 🔵 No robots.txt / sitemap / humans.txt / llms.txt     | `32db668`        | All four served via `frontend/public/` (Vite copies into `dist/` verbatim).        |
| 🟡 Public web service has no security.txt              | `32db668`        | RFC 9116 contact + policy URL + 1-year expiry at `/.well-known/security.txt`.      |
| Practices dimension (lint, format, dependabot, etc.)   | `2bd3b47`, `78cb44c` | ruff + black + CODEOWNERS + dependabot (pip + npm + GH actions) + PR + issue templates. |
| Documentation dimension                                | `78cb44c`        | 5 ADRs + SECURITY.md + ARCHITECTURE.md + CONTRIBUTING.md + CHANGELOG.md.            |

Each Repobility finding came with structured evidence — file path, line number, rule ID, and a copy-paste AI Fix Prompt. That scaffold is what makes the loop closable without a human in the middle.

---

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

## Development

```bash
pytest tests/ -q            # 20 tests
ruff check . && black --check .
cd frontend && npm run dev  # Vite dev server with /api proxied to :8000
```

CI runs the same matrix on every push and PR (Python 3.10/3.11/3.12/3.13 + Node 20/22) plus `pip-audit` and `npm audit --omit=dev`.

## Documentation

- [SHOWCASE.md](SHOWCASE.md) — full step-by-step journey through the Repobility loop.
- [SECURITY.md](SECURITY.md) — threat model and intentional non-goals.
- [ARCHITECTURE.md](ARCHITECTURE.md) — module-by-module reference with the full request flow.
- [.repobility/access.yml](.repobility/access.yml) — endpoint-by-endpoint authorization matrix.
- [docs/adr/](docs/adr/) — five Architecture Decision Records.
- [CHANGELOG.md](CHANGELOG.md) — versioned change history.
- [CONTRIBUTING.md](CONTRIBUTING.md) — ground rules and PR checklist.

## License

MIT — see [LICENSE](LICENSE).
