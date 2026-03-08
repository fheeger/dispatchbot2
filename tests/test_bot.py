from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord import app_commands

from bot import on_app_command_error
from client.errors import BackendError


@pytest.fixture
def interaction():
    inter = MagicMock(spec=discord.Interaction)
    inter.response = AsyncMock()
    return inter


# ---------------------------------------------------------------------------
# MissingRole
# ---------------------------------------------------------------------------

class TestMissingRole:
    @pytest.mark.asyncio
    async def test_sends_ephemeral_message(self, interaction):
        error = app_commands.MissingRole("Admin")
        await on_app_command_error(interaction, error)

        interaction.response.send_message.assert_called_once()
        _, kwargs = interaction.response.send_message.call_args
        assert kwargs["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_message_contains_role_name(self, interaction):
        error = app_commands.MissingRole("Admin")
        await on_app_command_error(interaction, error)

        msg = interaction.response.send_message.call_args[0][0]
        assert "Admin" in msg


# ---------------------------------------------------------------------------
# BackendError — direct (error itself is a BackendError)
# ---------------------------------------------------------------------------

class TestBackendErrorDirect:
    @pytest.mark.asyncio
    async def test_sends_ephemeral_message(self, interaction):
        error = BackendError(404, "Game Not Found", "no game")
        await on_app_command_error(interaction, error)

        _, kwargs = interaction.response.send_message.call_args
        assert kwargs["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_known_error_type_sends_friendly_message(self, interaction):
        error = BackendError(404, "Game Not Found", "no game")
        await on_app_command_error(interaction, error)

        msg = interaction.response.send_message.call_args[0][0]
        assert "game" in msg.lower()
        assert "404" not in msg

    @pytest.mark.asyncio
    async def test_unknown_error_type_falls_back_to_raw_message(self, interaction):
        error = BackendError(500, "Some Unknown Error", "something went wrong")
        await on_app_command_error(interaction, error)

        msg = interaction.response.send_message.call_args[0][0]
        assert "something went wrong" in msg


# ---------------------------------------------------------------------------
# BackendError — wrapped (error.__cause__ is a BackendError)
# ---------------------------------------------------------------------------

class TestBackendErrorWrapped:
    @pytest.mark.asyncio
    async def test_unwraps_cause_and_sends_friendly_message(self, interaction):
        backend_err = BackendError(422, "Message Too Long", "max 500 chars")
        wrapper = app_commands.AppCommandError("command failed")
        wrapper.__cause__ = backend_err

        await on_app_command_error(interaction, wrapper)

        msg = interaction.response.send_message.call_args[0][0]
        assert "long" in msg.lower()

    @pytest.mark.asyncio
    async def test_sends_ephemeral_message(self, interaction):
        backend_err = BackendError(422, "Message Too Long", "max 500 chars")
        wrapper = app_commands.AppCommandError("command failed")
        wrapper.__cause__ = backend_err

        await on_app_command_error(interaction, wrapper)

        _, kwargs = interaction.response.send_message.call_args
        assert kwargs["ephemeral"] is True


# ---------------------------------------------------------------------------
# Generic unhandled errors
# ---------------------------------------------------------------------------

class TestGenericError:
    @pytest.mark.asyncio
    async def test_sends_ephemeral_message(self, interaction):
        error = app_commands.AppCommandError("something broke")
        await on_app_command_error(interaction, error)

        _, kwargs = interaction.response.send_message.call_args
        assert kwargs["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_message_does_not_leak_internal_details(self, interaction):
        error = app_commands.AppCommandError("secret internal error")
        await on_app_command_error(interaction, error)

        msg = interaction.response.send_message.call_args[0][0]
        assert "secret internal error" not in msg
