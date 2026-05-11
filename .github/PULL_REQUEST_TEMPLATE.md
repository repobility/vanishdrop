<!-- Thanks for contributing! Keep the trust model intact. -->

## Summary

<!-- One paragraph: what changed and why. Link the issue if there is one. -->

## Trust-model impact

- [ ] No change. (Pure refactor, docs, or UI tweak.)
- [ ] Touches the wire protocol — `SECURITY.md` and `.repobility/access.yml` are updated.
- [ ] Touches the server validation rules — added/updated tests in `tests/test_server.py`.
- [ ] Touches the cryptographic core — added/updated tests in `tests/test_auth.py` and the frontend crypto module.
- [ ] Changes the capability-URL contract — `.repobility/access.yml` is updated and `tests/test_auth.py` covers the new behavior.

## Checklist

- [ ] `pytest tests/ -q` passes locally.
- [ ] `ruff check .` and `black --check .` clean.
- [ ] `cd frontend && npm run build` succeeds.
- [ ] No new third-party origins in CSP allowlist.
- [ ] Browser code uses `crypto.getRandomValues` / `crypto.subtle` — no `Math.random` in security-adjacent code.
- [ ] User-visible changes noted in `CHANGELOG.md` under `[Unreleased]`.

## Test plan

<!-- How did you verify this? Two-window manual check, curl against the API,
     pytest, etc. -->
