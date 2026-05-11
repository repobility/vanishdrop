# Changelog

All notable changes to VanishDrop are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-05-12

### Added

- Initial release.
- End-to-end encrypted one-time file sharing using Web Crypto API
  AES-GCM (256-bit key, 96-bit IV).
- FastAPI backend with SQLite + filesystem storage, periodic sweep,
  atomic one-time-download semantics.
- Vue 3 + Vite + TypeScript frontend with separate compose and
  viewer flows.
- Strict CSP middleware and `no-referrer` meta tag.
- pytest suite — 20 tests across server + auth.
- `.repobility/access.yml` documenting the capability-URL model.
- GitHub Actions CI matrix: Python 3.10–3.13 + Node 20/22 + lint +
  dependency audit.
- Web hygiene files (`robots.txt`, `sitemap.xml`, `humans.txt`,
  `llms.txt`, `/.well-known/security.txt`).
- `SECURITY.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, ADRs.

[1.0.0]: https://github.com/repobility/vanishdrop/releases/tag/v1.0.0
