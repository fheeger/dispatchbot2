import datetime
import hashlib

import discord
from discord import app_commands
from discord.ext import commands

SEND_EMOJI = "📨"
MISSED_MESSAGE_MAX_AGE = datetime.timedelta(days=3)


def _user_hash(user_id: int) -> str:
    return hashlib.sha256(str(user_id).encode()).hexdigest()


class UmpireCog(commands.Cog):
    def __init__(self, backend, base_url: str = ""):
        self.backend = backend
        self.base_url = base_url

    @app_commands.command(name="create_account",
                          description="Create an umpire account for the web interface")
    @app_commands.describe(username="Your desired login username")
    async def create_account(self, interaction: discord.Interaction, username: str):
        result = await self.backend.create_user(username, _user_hash(interaction.user.id))
        await interaction.response.send_message(
            "Account created. Your password has been sent to you by DM."
        )
        await interaction.user.send(
            f"Your umpire account has been created.\n"
            f"Username: {username}\n"
            f"Password: ||{result.password}||"
        )

    @app_commands.command(name="start_game", description="Start a new game")
    @app_commands.describe(game_name="Name of the game (letters, digits, dashes, underscores only)")
    async def start_game(self, interaction: discord.Interaction, game_name: str):
        result = await self.backend.create_game(
            game_name, interaction.guild_id, _user_hash(interaction.user.id)
        )
        await interaction.response.send_message(
            f"Game created: {result.name}, turn {result.turn}, time {result.start_time}."
        )

    @app_commands.command(name="end_game", description="End the current game")
    async def end_game(self, interaction: discord.Interaction):
        result = await self.backend.end_game(
            interaction.guild_id, interaction.channel.category_id
        )
        await interaction.response.send_message(
            f"Game {result.name} has ended at turn {result.turn}."
        )

    @app_commands.command(name="next_turn",
                          description="Advance to the next turn and deliver messages")
    async def next_turn(self, interaction: discord.Interaction):
        await interaction.response.defer()

        unapproved = await self.backend.check_unapproved_messages(
            interaction.guild_id, interaction.channel.category_id
        )
        if unapproved:
            await interaction.followup.send(
                f"⚠️ {len(unapproved)} unapproved messages still pending."
            )

        turn = await self.backend.next_turn(
            interaction.guild_id, interaction.channel.category_id
        )
        await interaction.followup.send(
            f"Turn {turn.turn} started. Time is now {turn.current_time}."
        )

        messages = await self.backend.get_messages(
            interaction.guild_id, interaction.channel.category_id
        )
        delivered = 0
        for msg in messages:
            text = (
                f"Dispatch from {msg.sender}:\n>>> {msg.text}"
                if msg.show_sender
                else f"Dispatch:\n>>> {msg.text}"
            )
            for recipient in msg.channels_list:
                channel = interaction.guild.get_channel(recipient.channel_id)
                if channel:
                    await channel.send(text)
            delivered += 1

        await interaction.followup.send(f"{delivered}/{len(messages)} messages delivered.")

    @app_commands.command(name="add_category",
                          description="Register a category with a game")
    @app_commands.describe(game_name="Name of the game",
                           category="Category to add (defaults to current channel's category)")
    async def add_category(self, interaction: discord.Interaction, game_name: str,
                           category: discord.CategoryChannel = None):
        cat_id = category.id if category else interaction.channel.category_id
        result = await self.backend.add_categories(game_name, interaction.guild_id, [cat_id])
        await interaction.response.send_message(
            f"Category added to game {result.game}."
        )

    @app_commands.command(name="remove_category",
                          description="Remove a category from a game")
    @app_commands.describe(game_name="Name of the game",
                           category="Category to remove (defaults to current channel's category)")
    async def remove_category(self, interaction: discord.Interaction, game_name: str,
                              category: discord.CategoryChannel = None):
        cat_id = category.id if category else interaction.channel.category_id
        result = await self.backend.remove_categories(game_name, interaction.guild_id, [cat_id])
        await interaction.response.send_message(
            f"Category removed from game {result.game}."
        )

    @app_commands.command(name="list_categories",
                          description="List all categories registered to a game")
    @app_commands.describe(game_name="Name of the game")
    async def list_categories(self, interaction: discord.Interaction, game_name: str):
        categories = await self.backend.list_categories(game_name, interaction.guild_id)
        names = []
        for cat in categories:
            ch = interaction.guild.get_channel(cat.number)
            if ch:
                names.append(str(ch.name))
        await interaction.response.send_message(
            f"Categories for {game_name}:\n" + "\n".join(names)
        )

    @app_commands.command(name="add_channel",
                          description="Register a channel as a player channel")
    @app_commands.describe(channel="Channel to add (defaults to current channel)")
    async def add_channel(self, interaction: discord.Interaction,
                          channel: discord.TextChannel = None):
        target = channel or interaction.channel
        result = await self.backend.update_channels(
            interaction.guild_id, interaction.channel.category_id,
            {target.id: target.name},
        )
        await interaction.response.send_message(
            f"Added {target.name} to game {result.game}."
        )

    @app_commands.command(name="remove_channel",
                          description="Remove a channel from a game")
    @app_commands.describe(channel="Channel to remove (defaults to current channel)")
    async def remove_channel(self, interaction: discord.Interaction,
                             channel: discord.TextChannel = None):
        target = channel or interaction.channel
        result = await self.backend.remove_channels(
            interaction.guild_id, interaction.channel.category_id,
            {target.id: target.name},
        )
        await interaction.response.send_message(
            f"Removed {target.name} from game {result.game}."
        )

    @app_commands.command(name="list_channels",
                          description="List all player channels in the current game")
    async def list_channels(self, interaction: discord.Interaction):
        channels = await self.backend.list_channels(
            interaction.guild_id, interaction.channel.category_id
        )
        names = [ch.name for ch in channels]
        await interaction.response.send_message(
            "Player channels:\n" + "\n".join(names)
        )

    @app_commands.command(name="broadcast",
                          description="Send a message to all player channels")
    @app_commands.describe(message="The message to broadcast")
    async def broadcast(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        channels = await self.backend.list_channels(
            interaction.guild_id, interaction.channel.category_id
        )
        sent = 0
        for ch in channels:
            channel = interaction.guild.get_channel(ch.channel_id)
            if channel:
                await channel.send(message)
                sent += 1
        await interaction.followup.send(
            f"Broadcast sent to {sent}/{len(channels)} channels."
        )

    @app_commands.command(name="check_for_missed_messages",
                          description="Resubmit any unprocessed dispatches from channel history")
    async def check_for_missed_messages(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channels = await self.backend.list_channels(
            interaction.guild_id, interaction.channel.category_id
        )
        for ch_data in channels:
            channel = interaction.guild.get_channel(ch_data.channel_id)
            if not channel:
                continue
            async for msg in channel.history(limit=20):
                if not msg.content.startswith("/dispatch"):
                    continue
                if any(r.emoji == SEND_EMOJI for r in msg.reactions):
                    continue
                age = datetime.datetime.now(datetime.timezone.utc) - msg.created_at
                if age > MISSED_MESSAGE_MAX_AGE:
                    continue
                try:
                    text = msg.content.split(" ", 1)[1]
                except IndexError:
                    continue
                await self.backend.send_message(
                    interaction.guild_id, channel.category_id,
                    text=text, sender=msg.author.display_name,
                )
                await msg.add_reaction(SEND_EMOJI)
        await interaction.followup.send("Finished checking for missed messages.")

    @app_commands.command(name="url", description="Show the backend admin URL")
    async def url(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Backend admin interface: {self.base_url}admin"
        )
