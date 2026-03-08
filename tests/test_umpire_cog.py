import hashlib
from unittest.mock import MagicMock, AsyncMock, patch, mock_open

import discord
import pytest

from client.errors import BackendError
from client.models import ChannelResponse, Message, RecipientChannel
from cogs.umpire import UmpireCog
from tests.conftest import make_mock_message, async_iter


def user_hash(user_id: int) -> str:
    return hashlib.sha256(str(user_id).encode()).hexdigest()


# ---------------------------------------------------------------------------
# /create_account
# ---------------------------------------------------------------------------

class TestCreateAccount:
    @pytest.mark.asyncio
    async def test_calls_backend_with_username_and_hash(self, interaction, mock_backend):
        cog = UmpireCog(mock_backend)
        await cog.create_account.callback(cog, interaction, username="john")

        mock_backend.create_user.assert_called_once_with("john", user_hash(interaction.user.id))

    @pytest.mark.asyncio
    async def test_dms_password_to_user(self, interaction, mock_backend):
        mock_backend.create_user.return_value.password = "secret123"
        cog = UmpireCog(mock_backend)
        await cog.create_account.callback(cog, interaction, username="john")

        interaction.user.send.assert_called_once()
        dm_text = interaction.user.send.call_args[0][0]
        assert "secret123" in dm_text

    @pytest.mark.asyncio
    async def test_sends_confirmation(self, interaction, mock_backend):
        cog = UmpireCog(mock_backend)
        await cog.create_account.callback(cog, interaction, username="john")

        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_backend_error_propagates(self, interaction, mock_backend):
        mock_backend.create_user.side_effect = BackendError(400, "User Already Exists", "User exists")
        cog = UmpireCog(mock_backend)

        with pytest.raises(BackendError) as exc:
            await cog.create_account.callback(cog, interaction, username="john")

        assert exc.value.error_type == "User Already Exists"


# ---------------------------------------------------------------------------
# /start_game
# ---------------------------------------------------------------------------

class TestStartGame:
    @pytest.mark.asyncio
    async def test_calls_backend_with_name_and_server(self, interaction, mock_backend, server_id):
        cog = UmpireCog(mock_backend)
        await cog.start_game.callback(cog, interaction, game_name="Test-Game")

        mock_backend.create_game.assert_called_once_with(
            "Test-Game", server_id, user_hash(interaction.user.id)
        )

    @pytest.mark.asyncio
    async def test_sends_confirmation_with_game_name(self, interaction, mock_backend):
        cog = UmpireCog(mock_backend)
        await cog.start_game.callback(cog, interaction, game_name="Test-Game")

        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        assert "Test-Game" in msg

    @pytest.mark.asyncio
    async def test_backend_error_propagates(self, interaction, mock_backend):
        mock_backend.create_game.side_effect = BackendError(422, "Game Already Exists", "Exists")
        cog = UmpireCog(mock_backend)

        with pytest.raises(BackendError):
            await cog.start_game.callback(cog, interaction, game_name="Test-Game")


# ---------------------------------------------------------------------------
# /end_game
# ---------------------------------------------------------------------------

class TestEndGame:
    @pytest.mark.asyncio
    async def test_calls_backend(self, interaction, mock_backend, server_id, category_id):
        cog = UmpireCog(mock_backend)
        await cog.end_game.callback(cog, interaction)

        mock_backend.end_game.assert_called_once_with(server_id, category_id)

    @pytest.mark.asyncio
    async def test_sends_confirmation_with_game_name_and_turn(self, interaction, mock_backend):
        cog = UmpireCog(mock_backend)
        await cog.end_game.callback(cog, interaction)

        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        assert "Test-Game" in msg
        assert "4" in msg

    @pytest.mark.asyncio
    async def test_backend_error_propagates(self, interaction, mock_backend):
        mock_backend.end_game.side_effect = BackendError(404, "Game Not Found", "No game")
        cog = UmpireCog(mock_backend)

        with pytest.raises(BackendError):
            await cog.end_game.callback(cog, interaction)


# ---------------------------------------------------------------------------
# /next_turn
# ---------------------------------------------------------------------------

class TestNextTurn:
    @pytest.mark.asyncio
    async def test_no_warning_when_no_unapproved_messages(self, interaction, mock_backend):
        mock_backend.check_unapproved_messages.return_value = []
        cog = UmpireCog(mock_backend)
        await cog.next_turn.callback(cog, interaction)

        sent_messages = [str(c) for c in interaction.followup.send.call_args_list]
        assert not any("unapproved" in m.lower() for m in sent_messages)

    @pytest.mark.asyncio
    async def test_warns_when_unapproved_messages_exist(self, interaction, mock_backend):
        mock_backend.check_unapproved_messages.return_value = [MagicMock(), MagicMock()]
        cog = UmpireCog(mock_backend)
        await cog.next_turn.callback(cog, interaction)

        all_sent = " ".join(str(c) for c in interaction.followup.send.call_args_list)
        assert "2" in all_sent
        assert "unapproved" in all_sent.lower()

    @pytest.mark.asyncio
    async def test_advances_turn(self, interaction, mock_backend, server_id, category_id):
        cog = UmpireCog(mock_backend)
        await cog.next_turn.callback(cog, interaction)

        mock_backend.next_turn.assert_called_once_with(server_id, category_id)

    @pytest.mark.asyncio
    async def test_sends_turn_confirmation(self, interaction, mock_backend):
        cog = UmpireCog(mock_backend)
        await cog.next_turn.callback(cog, interaction)

        all_sent = " ".join(str(c) for c in interaction.followup.send.call_args_list)
        assert "4" in all_sent  # turn number

    @pytest.mark.asyncio
    async def test_delivers_messages_to_recipient_channels(self, interaction, mock_backend):
        recipient_channel = MagicMock()
        recipient_channel.send = AsyncMock()
        interaction.guild.get_channel.return_value = recipient_channel

        mock_backend.get_messages.return_value = [
            Message(
                text="Attack at dawn.", sender="Alpha", showSender=True,
                channels_list=[RecipientChannel(channelId=444, channelName="bravo")],
                turn_when_sent=3, turn_when_received=4, game=1,
            )
        ]
        cog = UmpireCog(mock_backend)
        await cog.next_turn.callback(cog, interaction)

        recipient_channel.send.assert_called_once()
        sent_text = recipient_channel.send.call_args[0][0]
        assert "Attack at dawn." in sent_text

    @pytest.mark.asyncio
    async def test_includes_sender_when_show_sender_true(self, interaction, mock_backend):
        recipient_channel = MagicMock()
        recipient_channel.send = AsyncMock()
        interaction.guild.get_channel.return_value = recipient_channel

        mock_backend.get_messages.return_value = [
            Message(
                text="Move to grid 5.", sender="Alpha", showSender=True,
                channels_list=[RecipientChannel(channelId=444, channelName="bravo")],
                turn_when_sent=3, turn_when_received=4, game=1,
            )
        ]
        cog = UmpireCog(mock_backend)
        await cog.next_turn.callback(cog, interaction)

        sent_text = recipient_channel.send.call_args[0][0]
        assert "Alpha" in sent_text

    @pytest.mark.asyncio
    async def test_hides_sender_when_show_sender_false(self, interaction, mock_backend):
        recipient_channel = MagicMock()
        recipient_channel.send = AsyncMock()
        interaction.guild.get_channel.return_value = recipient_channel

        mock_backend.get_messages.return_value = [
            Message(
                text="Move to grid 5.", sender="Alpha", showSender=False,
                channels_list=[RecipientChannel(channelId=444, channelName="bravo")],
                turn_when_sent=3, turn_when_received=4, game=1,
            )
        ]
        cog = UmpireCog(mock_backend)
        await cog.next_turn.callback(cog, interaction)

        sent_text = recipient_channel.send.call_args[0][0]
        assert "Alpha" not in sent_text

    @pytest.mark.asyncio
    async def test_reports_delivery_count(self, interaction, mock_backend):
        recipient_channel = MagicMock()
        recipient_channel.send = AsyncMock()
        interaction.guild.get_channel.return_value = recipient_channel

        mock_backend.get_messages.return_value = [
            Message(
                text="Msg 1.", sender="Alpha", showSender=True,
                channels_list=[RecipientChannel(channelId=444, channelName="bravo")],
                turn_when_sent=3, turn_when_received=4, game=1,
            ),
            Message(
                text="Msg 2.", sender="Bravo", showSender=True,
                channels_list=[RecipientChannel(channelId=444, channelName="bravo")],
                turn_when_sent=3, turn_when_received=4, game=1,
            ),
        ]
        cog = UmpireCog(mock_backend)
        await cog.next_turn.callback(cog, interaction)

        all_sent = " ".join(str(c) for c in interaction.followup.send.call_args_list)
        assert "2" in all_sent


# ---------------------------------------------------------------------------
# /add_category
# ---------------------------------------------------------------------------

class TestAddCategory:
    @pytest.mark.asyncio
    async def test_calls_backend_with_provided_category(self, interaction, mock_backend, server_id):
        category = MagicMock(spec=discord.CategoryChannel)
        category.id = 555555555555555555
        cog = UmpireCog(mock_backend)
        await cog.add_category.callback(cog, interaction, game_name="Test-Game", category=category)

        mock_backend.add_categories.assert_called_once_with("Test-Game", server_id, [555555555555555555])

    @pytest.mark.asyncio
    async def test_defaults_to_current_channel_category(self, interaction, mock_backend, server_id, category_id):
        cog = UmpireCog(mock_backend)
        await cog.add_category.callback(cog, interaction, game_name="Test-Game", category=None)

        mock_backend.add_categories.assert_called_once_with("Test-Game", server_id, [category_id])

    @pytest.mark.asyncio
    async def test_sends_confirmation(self, interaction, mock_backend):
        cog = UmpireCog(mock_backend)
        await cog.add_category.callback(cog, interaction, game_name="Test-Game", category=None)

        interaction.response.send_message.assert_called_once()


# ---------------------------------------------------------------------------
# /remove_category
# ---------------------------------------------------------------------------

class TestRemoveCategory:
    @pytest.mark.asyncio
    async def test_calls_backend_with_provided_category(self, interaction, mock_backend, server_id):
        category = MagicMock(spec=discord.CategoryChannel)
        category.id = 555555555555555555
        cog = UmpireCog(mock_backend)
        await cog.remove_category.callback(cog, interaction, game_name="Test-Game", category=category)

        mock_backend.remove_categories.assert_called_once_with("Test-Game", server_id, [555555555555555555])

    @pytest.mark.asyncio
    async def test_defaults_to_current_channel_category(self, interaction, mock_backend, server_id, category_id):
        cog = UmpireCog(mock_backend)
        await cog.remove_category.callback(cog, interaction, game_name="Test-Game", category=None)

        mock_backend.remove_categories.assert_called_once_with("Test-Game", server_id, [category_id])

    @pytest.mark.asyncio
    async def test_sends_confirmation(self, interaction, mock_backend):
        cog = UmpireCog(mock_backend)
        await cog.remove_category.callback(cog, interaction, game_name="Test-Game", category=None)

        interaction.response.send_message.assert_called_once()


# ---------------------------------------------------------------------------
# /list_categories
# ---------------------------------------------------------------------------

class TestListCategories:
    @pytest.mark.asyncio
    async def test_calls_backend(self, interaction, mock_backend, server_id):
        cog = UmpireCog(mock_backend)
        await cog.list_categories.callback(cog, interaction, game_name="Test-Game")

        mock_backend.list_categories.assert_called_once_with("Test-Game", server_id)

    @pytest.mark.asyncio
    async def test_sends_category_names(self, interaction, mock_backend):
        category_channel = MagicMock(spec=discord.CategoryChannel)
        category_channel.name = "Blue"
        interaction.guild.get_channel.return_value = category_channel

        cog = UmpireCog(mock_backend)
        await cog.list_categories.callback(cog, interaction, game_name="Test-Game")

        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        assert "Blue" in msg


# ---------------------------------------------------------------------------
# /add_channel
# ---------------------------------------------------------------------------

class TestAddChannel:
    @pytest.mark.asyncio
    async def test_calls_backend_with_provided_channel(self, interaction, mock_backend, server_id, category_id):
        channel = MagicMock(spec=discord.TextChannel)
        channel.id = 444444444444444444
        channel.name = "bravo-company"
        cog = UmpireCog(mock_backend)
        await cog.add_channel.callback(cog, interaction, channel=channel)

        mock_backend.update_channels.assert_called_once_with(
            server_id, category_id, {444444444444444444: "bravo-company"}
        )

    @pytest.mark.asyncio
    async def test_defaults_to_current_channel(self, interaction, mock_backend, server_id, category_id):
        cog = UmpireCog(mock_backend)
        await cog.add_channel.callback(cog, interaction, channel=None)

        mock_backend.update_channels.assert_called_once_with(
            server_id, category_id, {interaction.channel.id: interaction.channel.name}
        )

    @pytest.mark.asyncio
    async def test_sends_confirmation(self, interaction, mock_backend):
        cog = UmpireCog(mock_backend)
        await cog.add_channel.callback(cog, interaction, channel=None)

        interaction.response.send_message.assert_called_once()


# ---------------------------------------------------------------------------
# /remove_channel
# ---------------------------------------------------------------------------

class TestRemoveChannel:
    @pytest.mark.asyncio
    async def test_calls_backend_with_provided_channel(self, interaction, mock_backend, server_id, category_id):
        channel = MagicMock(spec=discord.TextChannel)
        channel.id = 444444444444444444
        channel.name = "bravo-company"
        cog = UmpireCog(mock_backend)
        await cog.remove_channel.callback(cog, interaction, channel=channel)

        mock_backend.remove_channels.assert_called_once_with(
            server_id, category_id, {444444444444444444: "bravo-company"}
        )

    @pytest.mark.asyncio
    async def test_defaults_to_current_channel(self, interaction, mock_backend, server_id, category_id):
        cog = UmpireCog(mock_backend)
        await cog.remove_channel.callback(cog, interaction, channel=None)

        mock_backend.remove_channels.assert_called_once_with(
            server_id, category_id, {interaction.channel.id: interaction.channel.name}
        )

    @pytest.mark.asyncio
    async def test_sends_confirmation(self, interaction, mock_backend):
        cog = UmpireCog(mock_backend)
        await cog.remove_channel.callback(cog, interaction, channel=None)

        interaction.response.send_message.assert_called_once()


# ---------------------------------------------------------------------------
# /list_channels
# ---------------------------------------------------------------------------

class TestListChannels:
    @pytest.mark.asyncio
    async def test_calls_backend(self, interaction, mock_backend, server_id, category_id):
        cog = UmpireCog(mock_backend)
        await cog.list_channels.callback(cog, interaction)

        mock_backend.list_channels.assert_called_once_with(server_id, category_id)

    @pytest.mark.asyncio
    async def test_sends_channel_names(self, interaction, mock_backend):
        cog = UmpireCog(mock_backend)
        await cog.list_channels.callback(cog, interaction)

        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        assert "alpha-company" in msg


# ---------------------------------------------------------------------------
# /broadcast
# ---------------------------------------------------------------------------

class TestBroadcast:
    @pytest.mark.asyncio
    async def test_sends_message_to_all_channels(self, interaction, mock_backend):
        channel_a = MagicMock()
        channel_a.send = AsyncMock()
        channel_b = MagicMock()
        channel_b.send = AsyncMock()
        mock_backend.list_channels.return_value = [
            ChannelResponse(channel_id=111, name="alpha", game=1),
            ChannelResponse(channel_id=222, name="bravo", game=1),
        ]
        interaction.guild.get_channel.side_effect = lambda cid: {111: channel_a, 222: channel_b}[cid]

        cog = UmpireCog(mock_backend)
        await cog.broadcast.callback(cog, interaction, message="Umpire time has begun.")

        channel_a.send.assert_called_once_with("Umpire time has begun.")
        channel_b.send.assert_called_once_with("Umpire time has begun.")

    @pytest.mark.asyncio
    async def test_sends_delivery_summary(self, interaction, mock_backend):
        channel = MagicMock()
        channel.send = AsyncMock()
        interaction.guild.get_channel.return_value = channel

        cog = UmpireCog(mock_backend)
        await cog.broadcast.callback(cog, interaction, message="Hello all.")

        interaction.followup.send.assert_called_once()
        summary = interaction.followup.send.call_args[0][0]
        assert "1" in summary  # 1/1 channels


# ---------------------------------------------------------------------------
# /check_for_missed_messages
# ---------------------------------------------------------------------------

class TestCheckForMissedMessages:
    @pytest.mark.asyncio
    async def test_resubmits_unprocessed_dispatch(self, interaction, mock_backend, server_id, category_id):
        channel = MagicMock()
        channel.id = 333333333333333333
        channel.category_id = category_id
        unprocessed = make_mock_message("/dispatch Requesting help.", has_send_emoji=False, age_days=0)
        channel.history = MagicMock(return_value=async_iter([unprocessed]))
        interaction.guild.get_channel.return_value = channel

        cog = UmpireCog(mock_backend)
        await cog.check_for_missed_messages.callback(cog, interaction)

        mock_backend.send_message.assert_called_once_with(
            server_id, category_id,
            text="Requesting help.",
            sender=unprocessed.author.display_name,
        )

    @pytest.mark.asyncio
    async def test_skips_already_processed_dispatch(self, interaction, mock_backend):
        channel = MagicMock()
        channel.id = 333333333333333333
        processed = make_mock_message("/dispatch Already sent.", has_send_emoji=True, age_days=0)
        channel.history = MagicMock(return_value=async_iter([processed]))
        interaction.guild.get_channel.return_value = channel

        cog = UmpireCog(mock_backend)
        await cog.check_for_missed_messages.callback(cog, interaction)

        mock_backend.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_messages_older_than_3_days(self, interaction, mock_backend):
        channel = MagicMock()
        channel.id = 333333333333333333
        old_msg = make_mock_message("/dispatch Old message.", has_send_emoji=False, age_days=4)
        channel.history = MagicMock(return_value=async_iter([old_msg]))
        interaction.guild.get_channel.return_value = channel

        cog = UmpireCog(mock_backend)
        await cog.check_for_missed_messages.callback(cog, interaction)

        mock_backend.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_non_dispatch_messages(self, interaction, mock_backend):
        channel = MagicMock()
        channel.id = 333333333333333333
        regular = make_mock_message("Just a regular message.", has_send_emoji=False, age_days=0)
        channel.history = MagicMock(return_value=async_iter([regular]))
        interaction.guild.get_channel.return_value = channel

        cog = UmpireCog(mock_backend)
        await cog.check_for_missed_messages.callback(cog, interaction)

        mock_backend.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_adds_send_emoji_after_resubmit(self, interaction, mock_backend):
        channel = MagicMock()
        channel.id = 333333333333333333
        channel.category_id = interaction.channel.category_id
        unprocessed = make_mock_message("/dispatch Missed this.", has_send_emoji=False, age_days=0)
        channel.history = MagicMock(return_value=async_iter([unprocessed]))
        interaction.guild.get_channel.return_value = channel

        cog = UmpireCog(mock_backend)
        await cog.check_for_missed_messages.callback(cog, interaction)

        unprocessed.add_reaction.assert_called_once_with("📨")

    @pytest.mark.asyncio
    async def test_sends_completion_message(self, interaction, mock_backend):
        channel = MagicMock()
        channel.id = 333333333333333333
        channel.history = MagicMock(return_value=async_iter([]))
        interaction.guild.get_channel.return_value = channel

        cog = UmpireCog(mock_backend)
        await cog.check_for_missed_messages.callback(cog, interaction)

        assert interaction.followup.send.called


# ---------------------------------------------------------------------------
# /url
# ---------------------------------------------------------------------------

class TestUrl:
    @pytest.mark.asyncio
    async def test_sends_backend_url(self, interaction, mock_backend):
        cog = UmpireCog(mock_backend, base_url="http://example.com/")
        await cog.url.callback(cog, interaction)

        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        assert "http://example.com/" in msg
