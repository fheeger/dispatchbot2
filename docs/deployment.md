# Dispatch Bot — Deployment

## Hosting

The bot is hosted on [SparkedHost](https://sparkedhost.com/discord-bot-hosting), which uses the [Pterodactyl](https://pterodactyl.io/) panel. Pterodactyl manages the bot process using pre-configured environment templates called "eggs". Use the Python egg, configured to run `bot.py` with dependencies installed from `requirements.txt`.

## Environment Variables

The following environment variables must be set in the Pterodactyl panel:

| Variable   | Description                          |
|------------|--------------------------------------|
| `TOKEN`    | Discord bot token                    |
| `BASE_URL` | URL of the Django backend, including trailing slash |

## Startup

The panel should be configured to:

1. Install dependencies with `pip install -r requirements.txt`
2. Start the bot with `python bot.py`
