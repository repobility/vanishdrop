# ADR 0005 — No download receipts or analytics

- **Status**: Accepted
- **Date**: 2026-05-12

## Context

Most file-sharing services offer some form of read notification: an
email, a webhook, a "the recipient opened it at HH:MM" indicator for
the sender. It is a frequently-requested feature.

## Decision

VanishDrop does not offer download receipts. The creator cannot learn
— from the service — whether or when their file was downloaded.

## Rationale

- The recipient's privacy outweighs the sender's curiosity. Many
  legitimate recipients fetch sensitive files in moments where being
  identified is harmful (incident response, journalism, abuse-victim
  support).
- The sender can already infer the outcome out-of-band: the recipient
  acknowledges via the channel they got the URL on.
- Adding read receipts would require either (a) an account for the
  sender (kills ADR-0002) or (b) a long-lived sender token attached
  to each upload, which becomes a new credential to protect.

## Consequences

- `/healthz` reports only a count of stored records, no per-record
  state.
- The compose UI shows the URL, expiry, and max-downloads, never an
  "opened at" stamp.
- Operators are encouraged to keep server logs minimal — even
  per-fetch IP logs would effectively become a download receipt for
  anyone who can read them. The default uvicorn access log is
  enabled in development but should be disabled or scrubbed in
  production.
