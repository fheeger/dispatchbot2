# Dispatch Bot

This is a Discord bot for running turn-based tabletop wargames. Players submit dispatches via Discord; umpires review and route them via a Django web interface; messages are delivered to player channels when a turn is advanced.

This repository is a greenfield reimplementation. The reference implementation is at `C:\Users\Felix\Projects\dispatch_bot` and the Django backend is at `C:\Users\Felix\Projects\dispatch_bot_backend`.

## Docs

- `docs/commands.md` — all available bot commands and their behaviour
- `docs/project_setup.md` — recommended architecture, libraries, and project structure
- `docs/dispatch_bot_api.yaml` — OpenAPI spec for the backend API (verified against the backend source)
- `docs/deployment.md` — hosting on SparkedHost via Pterodactyl

## Architecture

- **Bot** (this repo) — Discord front-end, stateless. Built with discord.py 2.x slash commands.
- **Backend** — Django REST API at a separate URL. All game state lives there.
- **Discord server** — Categories map to games; channels within categories are player channels.

## Key conventions

- All commands are slash commands (`@app_commands.command`), not prefix commands.
- HTTP calls to the backend use `httpx` with `async`/`await`.
- Configuration is loaded via `pydantic-settings` from environment variables / `.env`.
- Backend responses are parsed into Pydantic models in `client/models.py`.
- A single `BackendError` exception (with `error_type` and `message`) covers all backend errors.
- All backend error handling lives in one `on_app_command_error` handler on `bot.tree`, not in individual commands.
- Tests use `pytest-asyncio` and `respx` to mock `httpx` calls.

## Backend API

The backend identifies which game to act on via `server_id` and `category_id` query parameters. Both are optional — the backend uses them to filter and disambiguate. Key error types returned by the backend:

| `error_type` | HTTP status |
|---|---|
| `Game Not Found` | 404 |
| `Game Ambiguous` | 400 |
| `No Account` | 403 |
| `Game Already Exists` | 422 |
| `Message Too Long` | 422 |
| `User Already Exists` | 400 |

See `docs/dispatch_bot_api.yaml` for the full API spec.
