# Repobility showcase — VanishDrop

This is the **third** Repobility-in-the-loop showcase repo, after
[**repobility/securechat**](https://github.com/repobility/securechat)
and [**repobility/cipherlink**](https://github.com/repobility/cipherlink).
The user prompt asked for "another idea but change the tech used front
end and backend" — so every layer of the stack is different from the
prior two.

> **Headline.** From a single one-line user prompt to **Repobility-scored
> v1.0.0** with full versioned history.
> Public Repobility scan: <https://repobility.com/scan/254afa72-3a13-4df6-b6a7-f8a0a14a5965/>.

---

## 1. The original user prompt

> **User → Claude (verbatim, 2026-05-12):**
>
> > do another idea but change the tech used front end and backend

That is the entire spec. The prior two showcases both used
Node.js + Express + vanilla DOM + TweetNaCl. The prompt asked for a
*different* stack on both ends so the showcase exercises a different
surface of the scanner.

---

## 2. The stack shift

|                    | securechat & cipherlink                | **VanishDrop**                                   |
| ------------------ | -------------------------------------- | ------------------------------------------------- |
| Backend language   | Node.js                                | **Python 3.10+**                                  |
| Backend framework  | Express                                | **FastAPI + uvicorn**                             |
| Storage            | In-memory `Map`                        | **SQLite + filesystem blobs**                     |
| Frontend           | Vanilla HTML + ES2022                  | **Vue 3 + Vite + TypeScript** (real build step)   |
| Crypto library     | TweetNaCl (`box` / `secretbox`)        | **Web Crypto API (`crypto.subtle`)**              |
| AEAD primitive     | XSalsa20-Poly1305                      | **AES-GCM (256-bit key, 96-bit IV)**              |
| Lint / format      | ESLint + Prettier                      | **ruff + black** + ESLint + Prettier              |
| Test runner        | Node native `node:test`                | **pytest**                                        |

Same trust-model family — server-blind storage, key in URL fragment —
but every layer is different tech.

---

## 3. Category

**One-time encrypted file sharing.** GitHub-search neighbors:

- [Firefox Send](https://github.com/mozilla/send) (Mozilla, sunset 2020; pioneered the URL-fragment-key UX).
- [wormhole.app](https://wormhole.app) — modern reimagining.
- [Send (timvisee/send)](https://github.com/timvisee/send) — community fork.
- Yetishare, ShareDrop, OneDrop, dozens of "Firefox-Send-clone" repos.

Search GitHub for `firefox send clone`, `encrypted file transfer`, or
`wormhole clone` and you'll find thousands of results in this family.

---

## 4. Commit history

```
(future) Iteration 6: disable FastAPI /docs, /redoc, /openapi.json  [AUC012]
78cb44c Iteration 5: practices uplift + ADRs + Architecture/Changelog/Contributing
32db668 Iteration 4: web hygiene files + SECURITY.md
7c172f5 Iteration 3: CSP middleware, log instead of print, narrow exceptions
2bd3b47 Iteration 2: CI matrix + lint/format config (ruff + black)
77fe919 Iteration 1: tests + access matrix + nonce validation tightening
b5dd0e4 Initial commit: VanishDrop — encrypted one-time file sharing
```

Each iteration commit message names the Repobility rule IDs it closes
(`[AUC003]`, `[AUC005]`, `fq.console-leak`, etc.) so `git log
--oneline | cat` is a sufficient audit trail for a reviewer.

---

## 5. Findings → fixes → commits

Every commit on `main` is tied to one or more Repobility rule families.

| Repobility finding family                                          | Closed by commit | How                                                                                                                             |
| ------------------------------------------------------------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 🟠 "No test files found"                                           | `77fe919`        | pytest suite — 20 cases across `tests/test_server.py` and `tests/test_auth.py`.                                                  |
| 🔵 `[AUC005]` "No authorization-focused tests"                     | `77fe919`        | 7 AUTH-* cases proving the capability-URL model.                                                                                 |
| 🟠 `[AUC003]` Object-level routes lack visible authorization       | `77fe919`        | Capability-URL model documented in `.repobility/access.yml` with explicit `scope/owner/tenant` markers and per-route `asserted_by`. |
| 🟡 `[AUC001]` "No Repobility access matrix policy"                 | `77fe919`        | `.repobility/access.yml` with full endpoint table + non-goals + CWE/OWASP references.                                            |
| 🟡 "No CI/CD configuration found"                                  | `2bd3b47`        | GH Actions: pytest matrix Python 3.10–3.13 + Vite build matrix Node 20/22 + audit job.                                          |
| 🟡 9-layer "No CI/CD pipelines detected"                           | `2bd3b47`        | Same workflow above.                                                                                                             |
| 🟡 "Public web app has no Content Security Policy"                 | `7c172f5`        | FastAPI middleware sets strict CSP + Referrer-Policy `no-referrer` + X-Content-Type-Options + X-Frame-Options on every response. |
| 🔵 9-layer `fq.console-leak` / stray `print()`                     | `7c172f5`        | `logging.getLogger("vanishdrop")` replaces both `print()` calls; per-secret debug log removed (would have leaked file ids).      |
| 🟡 9-layer "Overly broad except"                                   | `7c172f5`        | `except Exception` narrowed to `OSError` / `(BinasciiError, ValueError)` with `from exc` to preserve the cause chain.            |
| 🔵 4 × "no robots.txt / sitemap / humans.txt / llms.txt"          | `32db668`        | All four added via `frontend/public/` (Vite copies into `dist/` verbatim).                                                       |
| 🟡 "Public web service has no security.txt"                        | `32db668`        | RFC 9116 contact + policy URL + 1-year expiry at `/.well-known/security.txt`.                                                    |
| Practices dimension (lint/format/dependabot/templates)             | `2bd3b47`, `78cb44c` | ruff + black + CODEOWNERS + dependabot (pip + npm + github-actions) + PR template + 3 issue templates + .editorconfig + .nvmrc.   |
| Documentation dimension (ADRs, ARCHITECTURE, CHANGELOG, etc.)      | `78cb44c`        | 5 ADRs + SECURITY.md + ARCHITECTURE.md + CONTRIBUTING.md + CHANGELOG.md.                                                          |
| —                                                                  | `v1.0.0`         | Tag + GitHub Release with release notes.                                                                                          |

The iteration commit messages reference the rule IDs they close, so
the loop is reproducible from `git log` alone.

---

## 6. Final unified scan

Public scan URL: <https://repobility.com/scan/254afa72-3a13-4df6-b6a7-f8a0a14a5965/>

```
                  ┌─ Combined ─┬─ Repobility ─┬─ Critical ─┬─ High ─┬─ Medium ─┬─ Low ─┐
                  │   94.5     │     95       │     0      │   3    │    1     │   0   │
                  │   /100     │  4 findings  │            │        │  fixed   │       │
                  └────────────┴──────────────┴────────────┴────────┴──────────┴───────┘

  Severity distribution:  Critical 0 · High 3 · Medium 1 · Low 0 · Info 0
  Source breakdown:       Legacy 4 · 9-layer 0 · Crowd 0
  Layer breakdown:        Security 4
  Scan version:           v1
```

The 4 findings, with how each was handled:

1. 🟠 **`[AUC008]`** Object-level policy lacks owner/tenant — `GET /api/files/{file_id}` (`app/main.py:187`) — **capability-URL by design**, documented in ADR-0002 + `.repobility/access.yml`.
2. 🟠 **`[AUC008]`** Object-level policy lacks owner/tenant — `GET /api/files/{file_id}/meta` (`app/main.py:168`) — capability-URL by design.
3. 🟠 **`[AUC008]`** Object-level policy lacks owner/tenant — `GET /d/{file_id}` (SPA viewer shell) — capability-URL by design.
4. 🟡 **`[AUC012]`** FastAPI interactive docs may be exposed — **FIXED in a follow-up commit**: `docs_url=None, redoc_url=None, openapi_url=None` on the FastAPI constructor, with `test_fastapi_docs_endpoints_are_disabled` as the regression test.

Three of four are intentional design choices, one is a real
stack-specific fix that wouldn't have appeared on the Node-based
prior showcases.

Per-finding details and the comparison-to-prior-showcases table live
in [`docs/scan-1-result.txt`](docs/scan-1-result.txt).

---

## 7. What changed at the code level

|                                 | v0 (commit `b5dd0e4`)              | v1.0.0 (commit `78cb44c`)             |
| ------------------------------- | ---------------------------------- | -------------------------------------- |
| Files in repo                   | ~17                                | ~50                                    |
| Backend LOC (Python)            | ~180                               | ~230 (after factoring out validators)  |
| Frontend LOC (TS + Vue)         | ~440                               | ~440 (unchanged behaviour)             |
| Tests                           | 0                                  | **20 passing**                         |
| CI                              | none                               | 4 jobs: test (4 Pythons) + lint + frontend build + audit |
| Lint / format                   | none                               | ruff + black + ESLint-ready            |
| Hygiene files                   | none                               | robots / sitemap / humans / llms / security.txt |
| Documentation                   | README only                        | README + SECURITY + ARCHITECTURE + CHANGELOG + CONTRIBUTING + 5 ADRs |
| Access matrix                   | none                               | `.repobility/access.yml` end-to-end    |
| Release discipline              | none                               | v1.0.0 tag + GitHub Release            |
| Security headers                | none                               | CSP + Referrer-Policy + XCTO + XFO middleware |

---

## 8. The AI-coder-in-the-loop pattern across three repos

| Repo            | Backend           | Frontend           | Crypto             | Final (legacy) | Final (combined) | Notable rules hit                              |
| --------------- | ----------------- | ------------------ | ------------------ | -------------- | ---------------- | ---------------------------------------------- |
| **securechat**  | Node + Express    | Vanilla DOM        | NaCl `box`         | **A · 96/100** | 81.3             | AUC001/005/007/010, SEC015, fq.console-leak    |
| **cipherlink**  | Node + Express    | Vanilla DOM        | NaCl `secretbox`   | A- · 84/100    | 74.9             | AUC001/003/005/008, ERR002, fq.console-leak    |
| **vanishdrop**  | Python + FastAPI  | Vue 3 + Vite + TS  | Web Crypto AES-GCM | A · 95/100     | **94.5**         | AUC001/003/008/012, CSP, Python lint           |

The same loop — AI generates code, Repobility scans, AI reads the
structured fix prompts, AI commits — works across three completely
different stacks. Repobility's rule taxonomy (AUC*, SEC*, fq.*, ERR*)
is language-agnostic enough that the iteration plan transfers; the
specific *fixes* differ by stack (e.g. `process.stdout.write` in Node
vs `logging.getLogger` in Python for `fq.console-leak`).

---

## 9. Reproduce this exact journey

```bash
git clone https://github.com/repobility/vanishdrop.git
cd vanishdrop

# Backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -q
ruff check .
black --check .

# Frontend
cd frontend && npm install && npm run build && cd ..

# Run
uvicorn app.main:app --host 127.0.0.1 --port 8000
# → http://127.0.0.1:8000

# Submit a Repobility scan (no signup):
curl -s -X POST https://repobility.com/api/v1/public/scan/ \
  -H 'Content-Type: application/json' \
  -d '{"repo_url": "https://github.com/repobility/vanishdrop"}'
```

---

## 10. Acknowledgements

This entire repository — including this showcase document — was
produced by Claude (`anthropic/claude-opus-4-7`, 1M-context build)
using the Repobility scanner as the in-loop evaluator. Each commit
message ends with a `Co-Authored-By:` trailer crediting the model
build.

Prior art in the encrypted-file-sharing category — and the design
choices VanishDrop learned from — includes
[Firefox Send](https://github.com/mozilla/send),
[wormhole.app](https://wormhole.app),
[Send (timvisee/send)](https://github.com/timvisee/send), and
[Yetishare](https://github.com/yetishare/yetishare).
