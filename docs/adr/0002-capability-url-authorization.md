# ADR 0002 — Capability URL as the authorization model

- **Status**: Accepted
- **Date**: 2026-05-12

## Context

A one-time file-sharing service needs *some* way to scope who can
download a file. Conventional options:

- **Accounts + ACL** — heavy: needs a user database, password reset,
  session tokens, email verification.
- **Pre-shared passphrase** — pushes the coordination problem we're
  trying to solve onto the user.
- **Capability URL** — the URL itself is the credential. Anyone with
  the URL can download; anyone without it can't.

## Decision

VanishDrop uses a capability URL of the form:

```
https://host/d/<id>#k=<urlsafe-base64-key>
```

- `id`: 16 random bytes from `secrets.token_bytes(16)` → 22-char
  urlsafe base64 → ~128-bit search space. Path-visible DB key.
- `k`: 32 random bytes from `crypto.getRandomValues` (the browser's
  CSPRNG). In the URL fragment.

The browser **never** sends fragments in HTTP. The server cannot
learn the key, even from logs, even if compromised. Possession of
the *full* URL is the credential. No user table, no session, no
role.

## Rationale

- No accounts means no onboarding friction for one-shot recipients.
- Aligns with widely-deployed prior art: Firefox Send, wormhole.app,
  Yopass, PrivateBin, OneTimeSecret.
- The threat surface shrinks: there's no auth code that can have a
  bug. The server treats every fetcher equally; only the URL
  distinguishes who can decrypt.

## Consequences

- A leaked URL is a leaked file. Browser history, channel of
  distribution, screen-share — all become exfiltration vectors. We
  mitigate the dominant case (re-read from history) by making
  one-time-download the default.
- The creator cannot retract a file after sending. To mitigate, TTL
  is enforced server-side and defaults to 24 h.
- Static analyzers (Repobility's `[AUC003]` / `[AUC008]` rules) flag
  every object-level endpoint as "lacks owner/tenant check". We
  document the model explicitly in `.repobility/access.yml` so the
  finding ties to a deliberate design choice rather than a bug.
