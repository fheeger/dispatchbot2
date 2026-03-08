import discord
from discord import app_commands
from discord.ext import commands


class AdminCog(commands.Cog):
    def __init__(self, backend):
        self.backend = backend

    @app_commands.command(name="message_all",
                          description="Send a file's contents as a DM to all server members")
    @app_commands.checks.has_role("Admin")
    @app_commands.describe(filename="File in the data/ directory to send")
    async def message_all(self, interaction: discord.Interaction, filename: str):
        try:
            message = open(f"data/{filename}").read()
        except FileNotFoundError:
            await interaction.response.send_message(f"File {filename} not found.")
            return

        await interaction.response.defer()
        total = len(interaction.guild.members)
        success = 0
        for member in interaction.guild.members:
            try:
                await member.send(message)
                success += 1
            except Exception:
                pass
        await interaction.followup.send(
            f"Message was sent to {success} out of {total} members."
        )
