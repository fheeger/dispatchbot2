import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from client.backend_client import BackendClient
from client.errors import BackendError
from cogs.admin import AdminCog
from cogs.misc import MiscCog
from cogs.player import PlayerCog
from cogs.umpire import UmpireCog
from config import settings

log = logging.getLogger(__name__)

_BACKEND_ERROR_MESSAGES = {
    "Game Not Found": "No game found for this channel.",
    "Game Ambiguous": "Multiple games found — be more specific.",
    "No Account": "You don't have an umpire account. Use `/create_account` first.",
    "Game Already Exists": "A game with that name already exists.",
    "Message Too Long": "Your message is too long.",
    "User Already Exists": "That username is already taken.",
}


async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(
            f"You need the **{error.missing_role}** role to use this command.",
            ephemeral=True,
        )
        return

    cause = error.__cause__ if error.__cause__ is not None else error
    if isinstance(cause, BackendError):
        text = _BACKEND_ERROR_MESSAGES.get(cause.error_type, f"Backend error: {cause.message}")
        await interaction.response.send_message(text, ephemeral=True)
        return

    log.exception("Unhandled slash command error", exc_info=error)
    await interaction.response.send_message(
        "An unexpected error occurred.", ephemeral=True
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix="!", intents=intents)
    backend = BackendClient(settings.base_url)

    bot.tree.error(on_app_command_error)

    @bot.event
    async def on_ready() -> None:
        log.info("Logged in as %s", bot.user)
        await bot.tree.sync()
        log.info("Commands synced.")

    await bot.add_cog(MiscCog(backend))
    await bot.add_cog(PlayerCog(backend))
    await bot.add_cog(UmpireCog(backend, base_url=settings.base_url))
    await bot.add_cog(AdminCog(backend))

    try:
        await bot.start(settings.token)
    finally:
        await backend.aclose()


if __name__ == "__main__":
    asyncio.run(main())
