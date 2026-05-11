# Contributing to VanishDrop

VanishDrop is a small, auditable codebase. Changes are weighted toward
simplicity and clarity over feature breadth.

## Ground rules

1. **Don't break the trust model.** The server must remain unable to
   decrypt files. Any change that introduces server-side decryption,
   plaintext logging, persistent key material, or breaks the
   capability-URL property is out of scope.
2. **Trust crypto, not your own.** Use the Web Crypto API or another
   audited primitive. Do not write custom cryptography.
3. **Keep the build surface small.** Python stdlib + FastAPI on the
   backend; Vue 3 + Vite on the frontend. No additional runtime
   dependencies without a strong reason.
4. **Tests must accompany behaviour changes.** Every protocol- or
   auth-relevant change lands with new pytest cases.

## Local development

```bash
git clone https://github.com/repobility/vanishdrop.git
cd vanishdrop

# Backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest httpx ruff black

pytest tests/ -q
ruff check .
black --check .

# Frontend
cd frontend
npm install
npm run build       # production bundle into frontend/dist/
npm run dev         # vite dev server with /api proxied to :8000
```

CI runs the same matrix on every push and PR (Python 3.10–3.13, Node
20/22) plus `pip-audit` and `npm audit --omit=dev`.

## Style

### Python
- 4-space indent, double quotes (Black default).
- Type hints on public functions.
- `ruff` rule set is the default plus `S` (Bandit security rules).
- No `print()` outside of intentional logging.

### TypeScript / Vue
- `<script setup lang="ts">` for components.
- 2-space indent, single quotes, semicolons, trailing commas.
- No `innerHTML` with user content — Vue interpolations are already
  escaped.
- All randomness goes through `crypto.getRandomValues` — never
  `Math.random` in security-adjacent code.

## Pull-request checklist

- [ ] `pytest tests/ -q` passes locally.
- [ ] `ruff check .` and `black --check .` are clean.
- [ ] `npm run build` succeeds.
- [ ] Wire-protocol or threat-model changes update `SECURITY.md` and
      `.repobility/access.yml`.
- [ ] User-visible changes update `README.md` and `CHANGELOG.md`.

## Reporting security issues

See [SECURITY.md](SECURITY.md). Please do not file public issues for
vulnerabilities — email the maintainer first.
