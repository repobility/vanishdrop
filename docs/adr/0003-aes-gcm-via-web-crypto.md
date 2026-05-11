# ADR 0003 — AES-GCM via the Web Crypto API as the AEAD

- **Status**: Accepted
- **Date**: 2026-05-12

## Context

VanishDrop needs symmetric authenticated encryption for binary file
blobs of up to 32 MiB. We do not need key agreement; the recipient
learns the key from the URL fragment, not a handshake.

Three families to choose from:

- **Web Crypto API** (`crypto.subtle`) — AES-GCM, hardware-accelerated
  via AES-NI on most platforms. Standardised and ships in every
  evergreen browser.
- **TweetNaCl** (`nacl.secretbox`) — XSalsa20 + Poly1305. Audited but
  pure JS; ~3 KB minified.
- **libsodium / sodium-plus** — full NaCl coverage in WASM.

## Decision

We use **AES-GCM via the Web Crypto API**:

- 256-bit key from `crypto.getRandomValues(new Uint8Array(32))`.
- 96-bit IV from `crypto.getRandomValues(new Uint8Array(12))`.
- `crypto.subtle.encrypt({name:'AES-GCM',iv}, cryptoKey, plaintext)`.

The two prior showcases in this org (SecureChat, Cipherlink) both
used TweetNaCl. Picking Web Crypto here is part of the intentional
contrast: we want VanishDrop to exercise a different cryptographic
toolkit so the "browser-side crypto, server-blind storage" pattern
is visible across primitives.

## Considered alternatives

- **TweetNaCl `secretbox`** — also fine, but identical to Cipherlink's
  choice. The showcase value is in stack diversity.
- **AES-CBC + HMAC** — manual MAC-then-encrypt is a footgun. AES-GCM
  does it correctly in one primitive.
- **ChaCha20-Poly1305** via Web Crypto — not in the Web Crypto API as
  of 2026; only available through libsodium.

## Consequences

- Confidentiality and integrity hold against anyone who doesn't have
  the 32-byte key.
- The browser bundle has zero crypto-related third-party origins.
- AES-GCM is hardware-accelerated on every common platform; 32 MiB
  files encrypt in well under a second on consumer laptops.
- The Web Crypto API requires HTTPS (or `localhost`) — fine for any
  realistic deployment.
