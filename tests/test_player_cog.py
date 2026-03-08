from unittest.mock import patch, mock_open

import pytest

from client.errors import BackendError
from cogs.player import PlayerCog


class TestDispatch:
    @pytest.mark.asyncio
    async def test_calls_backend_with_correct_args(self, interaction, mock_backend, server_id, category_id):
        cog = PlayerCog(mock_backend)
        await cog.dispatch.callback(cog, interaction, message="Requesting reinforcements at grid 447.")

        mock_backend.send_message.assert_called_once_with(
            server_id, category_id,
            text="Requesting reinforcements at grid 447.",
            sender="TestUser",
        )

    @pytest.mark.asyncio
    async def test_sends_confirmation(self, interaction, mock_backend):
        cog = PlayerCog(mock_backend)
        await cog.dispatch.callback(cog, interaction, message="Hello")

        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_backend_error_propagates(self, interaction, mock_backend):
        mock_backend.send_message.side_effect = BackendError(422, "Message Too Long", "Too long")
        cog = PlayerCog(mock_backend)

        with pytest.raises(BackendError) as exc:
            await cog.dispatch.callback(cog, interaction, message="x" * 3000)

        assert exc.value.error_type == "Message Too Long"


class TestHowto:
    @pytest.mark.asyncio
    async def test_sends_howto_content(self, interaction, mock_backend):
        howto_text = "Use /dispatch to send a message."
        cog = PlayerCog(mock_backend)

        with patch("builtins.open", mock_open(read_data=howto_text)):
            await cog.howto.callback(cog, interaction)

        interaction.response.send_message.assert_called_once()
        sent = interaction.response.send_message.call_args[0][0]
        assert sent == howto_text

    @pytest.mark.asyncio
    async def test_response_is_ephemeral(self, interaction, mock_backend):
        cog = PlayerCog(mock_backend)

        with patch("builtins.open", mock_open(read_data="howto text")):
            await cog.howto.callback(cog, interaction)

        kwargs = interaction.response.send_message.call_args[1]
        assert kwargs.get("ephemeral") is True
