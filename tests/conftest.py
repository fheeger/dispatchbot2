import datetime
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from client.backend_client import BackendClient
from client.models import (
    AccountCreatedResponse,
    AddCategoryResponse,
    CategoryResponse,
    ChannelResponse,
    ChannelsRemovedResponse,
    ChannelsUpdatedResponse,
    GameCreatedResponse,
    GameEndedResponse,
    Message,
    RecipientChannel,
    RemoveCategoryResponse,
    RoundResponse,
    TurnAdvancedResponse,
)

BASE_URL = "http://testserver/"

# ---------------------------------------------------------------------------
# Backend client fixture (for backend_client tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return BackendClient(BASE_URL)


# ---------------------------------------------------------------------------
# Common values
# ---------------------------------------------------------------------------

@pytest.fixture
def server_id():
    return 111111111111111111


@pytest.fixture
def category_id():
    return 222222222222222222


@pytest.fixture
def game_name():
    return "Test-Game"


@pytest.fixture
def discord_id_hash():
    return "abc123def456abc123def456abc123def456abc123def456abc123def456abc1"


# ---------------------------------------------------------------------------
# Shared backend response payloads (for backend_client tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def message_payload():
    return {
        "text": "Requesting reinforcements at grid 447.",
        "sender": "Alpha Company",
        "showSender": True,
        "channels_list": [
            {"channelId": 333333333333333333, "channelName": "alpha-company"}
        ],
        "turn_when_sent": 3,
        "turn_when_received": 4,
        "game": 1,
    }


# ---------------------------------------------------------------------------
# Mock backend client (for cog tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_backend():
    backend = AsyncMock(spec=BackendClient)

    backend.create_user.return_value = AccountCreatedResponse(
        username="john", is_staff=False, password="secret123"
    )
    backend.create_game.return_value = GameCreatedResponse(
        name="Test-Game", turn=1, start_time="08:00:00",
        server_id=111111111111111111, user_id=None,
    )
    backend.get_round.return_value = RoundResponse(
        turn=3, name="Test-Game", start_time="08:00:00",
        server_id=111111111111111111, user_id=None,
    )
    backend.next_turn.return_value = TurnAdvancedResponse(
        name="Test-Game", turn=4, current_time="09:00:00"
    )
    backend.end_game.return_value = GameEndedResponse(
        name="Test-Game", turn=4, current_time="09:00:00"
    )
    backend.get_messages.return_value = []
    backend.check_unapproved_messages.return_value = []
    backend.send_message.return_value = Message(
        text="Hello", sender="Alpha", showSender=True,
        channels_list=[], turn_when_sent=1, turn_when_received=2, game=1,
    )
    backend.add_categories.return_value = AddCategoryResponse(
        game="Test-Game", categories=[222222222222222222]
    )
    backend.remove_categories.return_value = RemoveCategoryResponse(
        game="Test-Game", category=[]
    )
    backend.list_categories.return_value = [
        CategoryResponse(number=222222222222222222, game=1)
    ]
    backend.update_channels.return_value = ChannelsUpdatedResponse(
        game="Test-Game", channels={"333333333333333333": "alpha-company"}
    )
    backend.remove_channels.return_value = ChannelsRemovedResponse(
        game="Test-Game", channels=["333333333333333333"]
    )
    backend.list_channels.return_value = [
        ChannelResponse(channel_id=333333333333333333, name="alpha-company", game=1)
    ]

    return backend


# ---------------------------------------------------------------------------
# Mock Discord interaction (for cog tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def interaction(server_id, category_id):
    inter = MagicMock(spec=discord.Interaction)
    inter.guild_id = server_id
    inter.channel = MagicMock()
    inter.channel.category_id = category_id
    inter.channel.id = 333333333333333333
    inter.channel.name = "alpha-company"
    inter.user = MagicMock()
    inter.user.id = 987654321
    inter.user.display_name = "TestUser"
    inter.user.send = AsyncMock()
    inter.response = AsyncMock()
    inter.response.is_done.return_value = False
    inter.followup = AsyncMock()
    inter.guild = MagicMock()
    inter.guild.id = server_id
    return inter


# ---------------------------------------------------------------------------
# Helpers for async iteration (channel history mocking)
# ---------------------------------------------------------------------------

def make_mock_message(content: str, has_send_emoji: bool = False,
                      age_days: int = 0) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    msg.created_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=age_days)
    msg.author = MagicMock()
    msg.author.display_name = "TestPlayer"
    msg.add_reaction = AsyncMock()

    send_emoji = "📨"
    if has_send_emoji:
        reaction = MagicMock()
        reaction.emoji = send_emoji
        msg.reactions = [reaction]
    else:
        msg.reactions = []

    return msg


def async_iter(items):
    """Return an async iterator over items, for mocking channel.history()."""
    async def _inner():
        for item in items:
            yield item
    return _inner()
