# cumplo-herald

## Overview
Multi-channel notification service that delivers real-time alerts to Cumplo investors via WhatsApp
(Twilio) and other channels. Runs as a Cloud Run FastAPI service, triggered by Pub/Sub messages from
the orchestrator via `cumplo-common`'s `PubSubMiddleware`.

## Build & Run
- Install deps: `poetry install`
- Start server locally: `uvicorn cumplo_herald.main:app --reload`
- Auto-fix lint + format: `make format`
- Verify code quality (CI gate): `make lint`

Python 3.13, Poetry 2.4.x.

## Code Quality
Three tools enforced at 120 cols — all three must agree before merging.

| Tool | Role | Command |
|---|---|---|
| Ruff | Lint + format | `make lint` / `make format` |
| basedpyright | Type checking | included in `make lint` |
| docformatter | Docstring style | included in `make lint` |

`make format` auto-fixes; `make lint` verifies (same as CI, no fixes).

## Git Workflow
- Branch prefixes: `feat/`, `fix/`, `chore/`, `ci/`. Conventional-commit subjects.
- `master` is protected: every change requires a PR + code-owner review (`@cnsfeir-reviewer`).
  Never push to `master` directly.

## Architecture
- `cumplo_herald/main.py` — FastAPI app entry point, middleware wiring, router registration.
- `cumplo_herald/routers/` — HTTP route handlers (common + WhatsApp public/private).
- `cumplo_herald/adapters/` — Outbound channel adapters (Twilio, etc.).
- `cumplo_herald/ports/` — Inbound port interfaces.
- `cumplo_herald/utils/` — Constants and helpers.

## Gotchas
- **FastAPI relaxations active:** `FAST002` (Annotated dependency) and `B008` (Depends in defaults)
  are suppressed globally — this is intentional for a FastAPI service.
- **cumplo-common blast radius:** This service depends on the shared `cumplo-common` library. Any
  change there affects all services — bump consumers with `make update-common` after a common
  version release.
- **Twilio credentials** are injected at runtime via environment variables; never hardcode them.

## Before Committing
- [ ] Run `make format`, then `make lint` and ensure it passes.
- [ ] No secrets or credential files committed.
