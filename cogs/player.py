import discord
from discord import app_commands
from discord.ext import commands


class PlayerCog(commands.Cog):
    def __init__(self, backend):
        self.backend = backend

    @app_commands.command(name="dispatch", description="Send a dispatch message")
    @app_commands.describe(message="The content of your dispatch")
    async def dispatch(self, interaction: discord.Interaction, message: str):
        await self.backend.send_message(
            interaction.guild_id,
            interaction.channel.category_id,
            text=message,
            sender=interaction.user.display_name,
        )
        await interaction.response.send_message("📨 Dispatch received.")

    @app_commands.command(name="howto", description="How to use the bot as a player")
    async def howto(self, interaction: discord.Interaction):
        text = open("data/howto_player.txt").read()
        await interaction.response.send_message(text, ephemeral=True)
