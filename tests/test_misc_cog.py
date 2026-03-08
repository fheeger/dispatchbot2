import pytest

from cogs.misc import MiscCog


class TestHello:
    @pytest.mark.asyncio
    async def test_sends_greeting(self, interaction, mock_backend):
        cog = MiscCog(mock_backend)
        await cog.hello.callback(cog, interaction)

        interaction.response.send_message.assert_called_once()
        message = interaction.response.send_message.call_args[0][0]
        assert "dispatch" in message.lower() or "hello" in message.lower()
