# Dispatch Bot — Recommended Project Setup

## Project Structure

```
dispatch_bot/
├── .env                    # local secrets (not committed)
├── .env.example            # committed template with dummy values
├── requirements.txt
├── bot.py                  # entry point
├── config.py               # typed configuration
├── client/
│   ├── __init__.py
│   ├── backend_client.py   # async HTTP client
│   └── models.py           # pydantic response/request models
├── cogs/
│   ├── __init__.py
│   ├── player.py
│   ├── umpire.py
│   └── admin.py
└── tests/
    ├── conftest.py
    ├── test_player.py
    └── test_umpire.py
```

---

## Dependencies

```
# requirements.txt
discord.py>=2.3
httpx>=0.27
pydantic>=2.0
pydantic-settings>=2.0

# dev/test only
pytest>=8.0
pytest-asyncio>=0.23
respx>=0.21
```

---

## Configuration — `config.py`

Use **[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** to load and validate configuration. It reads from environment variables and a `.env` file automatically, with type coercion and validation on startup.

The config object is instantiated once at module level and imported wherever needed.

`.env.example` should be committed to the repository with placeholder values so new contributors know which variables are required.

---

## API Models — `client/models.py`

Define **[Pydantic](https://docs.pydantic.dev/) models** for every request body and response the backend returns. This validates the API contract at the boundary — if the backend changes its response shape, a clear validation error is raised immediately.

Each backend endpoint should have a corresponding response model. Field aliases handle any naming differences between JSON keys (e.g. camelCase from the backend) and Python attribute names.

---

## Backend Client — `client/backend_client.py`

A single class wraps all backend HTTP calls. Key design points:

- Use **[httpx](https://www.python-httpx.org/)** with `async`/`await` for non-blocking HTTP calls.
- A single private `_request` method handles the HTTP call, checks for errors, and returns parsed JSON. All public methods call this internally.
- On HTTP error responses, raise a `BackendError` exception that carries the `error_type` and `message` from the response body.
- Each public method returns a typed Pydantic model so callers work with typed objects throughout.

---

## Bot Entry Point — `bot.py`

The entry point creates the bot, loads each cog via `load_extension`, and starts the bot. It also registers a global slash command error handler (see Error Handling below).

The `command_prefix` parameter is required by `commands.Bot` but unused for slash commands — set it to an unlikely string.

---

## Slash Commands

All commands are implemented as Discord **Application Commands** (slash commands), registered using the `@app_commands.command` decorator.

- **Parameters are declared in the function signature** with types. Discord validates and auto-completes them before the handler is called.
- **Discord object types** (e.g. `discord.TextChannel`) can be used directly as parameter types. Discord resolves names to objects automatically.
- **Optional parameters** use Python default values. When a parameter like `channel` is omitted, the handler falls back to the current channel.
- Commands are visible to users via the `/` menu.

Commands that may take time should call `interaction.response.defer()` immediately to prevent Discord's 3-second timeout, then use `interaction.followup.send()` for subsequent messages.

### Syncing Commands with Discord

Slash commands must be registered with Discord's API before they appear. This is done by calling `bot.tree.sync()`. There are two strategies:

- **Guild sync** (development): syncs instantly to a specific server.
- **Global sync** (production): syncs to all servers but takes up to one hour to propagate. Call this in `on_ready`.

Avoid syncing on every startup in production to stay within Discord's rate limits.

---

## Global Error Handling

Register a single error handler on `bot.tree` using the `on_app_command_error` event. This handler receives all unhandled exceptions from slash commands.

Inside the handler, check if the cause is a `BackendError` and match on its `error_type` to produce a user-friendly message. All other exceptions are caught as a fallback. Error responses should be sent as ephemeral messages (visible only to the triggering user) where appropriate.

---

## Testing

### HTTP Mocking with `respx`

**[respx](https://lundberg.github.io/respx/)** intercepts `httpx` calls in tests, allowing the backend to be mocked without a running server. Each test defines which HTTP requests to expect and what responses to return.

Tests for the backend client should cover:
- Successful responses are parsed into the correct model
- Error responses raise `BackendError` with the correct `error_type`

### Async Tests with `pytest-asyncio`

Mark async test functions with `@pytest.mark.asyncio`. A shared `conftest.py` provides fixtures such as a mock backend client (using `unittest.mock.AsyncMock`) for testing cog logic in isolation from the HTTP layer.

### What to Test

- **`BackendClient`** (using `respx`): correct URL, query params, and request body; response parsing into the right model; `BackendError` raised with the correct `error_type` on error responses.
- **Cogs** (using `AsyncMock` backend): business logic, correct backend methods called with correct arguments, correct messages sent back to Discord.

Run tests with:
```
pytest tests/ -v
```
