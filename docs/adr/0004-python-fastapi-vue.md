# ADR 0004 — Python FastAPI + Vue 3 stack

- **Status**: Accepted
- **Date**: 2026-05-12

## Context

VanishDrop is the third Repobility-in-the-loop showcase. The first
two ([repobility/securechat](https://github.com/repobility/securechat)
and [repobility/cipherlink](https://github.com/repobility/cipherlink))
both used Node.js + Express + vanilla DOM. The user explicitly asked
for a different stack on both ends so the showcase exercises a
different surface of the scanner.

## Decision

- **Backend**: Python 3.10+ with FastAPI and uvicorn. SQLite (stdlib)
  for metadata; filesystem for blobs.
- **Frontend**: Vue 3 (Composition API) with Vite + TypeScript.
  Single-file components.
- **Crypto**: Web Crypto API (AES-GCM).

## Rationale

- **FastAPI** is the current default for modern Python web APIs;
  built-in OpenAPI schema, async-friendly, type-hint-driven
  validation via Pydantic.
- **Vue 3** has a meaningfully different mental model from vanilla
  DOM: declarative templates, reactive refs, single-file components.
  Different from the two prior repos.
- **SQLite + filesystem** is the right substrate for the data shape:
  metadata is structured (queryable by id, expiry), blobs are
  opaque bytes. Putting blobs in SQLite would be a fight.
- **Vite** gives us a real bundler with hot reload, TypeScript
  type-checking via `vue-tsc`, and a `frontend/dist/` output that
  FastAPI can `mount` as static files.

## Considered alternatives

- **Go + chi + Svelte** — Svelte is great but the showcase value is
  similar; the Python ecosystem differs from Node more dramatically.
- **Django + DRF + React** — heavier than needed for ~150 LOC of
  server code.
- **HTMX + FastAPI** — would have removed the JS frontend almost
  entirely. Defeats the "Vue 3" leg of the contrast.

## Consequences

- Repobility's scanner exercises Python rules (Bandit-style, ruff,
  pip-audit) it didn't on the prior repos.
- CI is dual-pipeline (Python matrix + Node matrix). Both are wired
  into the same workflow.
- Deployment story is "build the frontend once, then run uvicorn".
  The frontend dist is excluded from version control (gitignore'd)
  to keep diffs reviewable.
