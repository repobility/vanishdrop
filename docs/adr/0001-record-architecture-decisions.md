# ADR 0001 — Record architecture decisions

- **Status**: Accepted
- **Date**: 2026-05-12

## Context

VanishDrop makes several non-obvious choices (capability-URL auth,
Web Crypto over a vendored library, FastAPI over Express, no download
receipts). Future contributors and security reviewers need the *why*
of each.

## Decision

We record significant architectural decisions as
[Architecture Decision Records](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
under [`docs/adr/`](.). Each ADR captures **Context**, **Decision**,
and **Consequences**, is immutable once accepted, and gets a new
number rather than edits if superseded.

## Consequences

- A reviewer reading a PR that touches the wire protocol, the auth
  model, the cryptographic core, or the storage substrate can find
  the relevant ADR and cite it.
- Out-of-date ADRs are explicitly visible (status: `Superseded`)
  rather than silently dropped.
- The act of writing the ADR forces the author to articulate
  trade-offs.
