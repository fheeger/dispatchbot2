from unittest.mock import MagicMock, AsyncMock, mock_open, patch

import pytest
from discord import app_commands

from cogs.admin import AdminCog


class TestMessageAll:
    @pytest.mark.asyncio
    async def test_dms_file_content_to_all_members(self, interaction, mock_backend):
        member_a = MagicMock()
        member_a.send = AsyncMock()
        member_b = MagicMock()
        member_b.send = AsyncMock()
        interaction.guild.members = [member_a, member_b]

        cog = AdminCog(mock_backend)
        with patch("builtins.open", mock_open(read_data="Announcement text.")):
            await cog.message_all.callback(cog, interaction, filename="announcement.txt")

        member_a.send.assert_called_once_with("Announcement text.")
        member_b.send.assert_called_once_with("Announcement text.")

    @pytest.mark.asyncio
    async def test_reads_from_data_directory(self, interaction, mock_backend):
        interaction.guild.members = []
        cog = AdminCog(mock_backend)

        with patch("builtins.open", mock_open(read_data="")) as mock_file:
            await cog.message_all.callback(cog, interaction, filename="announcement.txt")

        opened_path = mock_file.call_args[0][0]
        assert "announcement.txt" in opened_path
        assert "data" in opened_path

    @pytest.mark.asyncio
    async def test_sends_summary_with_success_count(self, interaction, mock_backend):
        member_a = MagicMock()
        member_a.send = AsyncMock()
        member_b = MagicMock()
        member_b.send = AsyncMock()
        interaction.guild.members = [member_a, member_b]

        cog = AdminCog(mock_backend)
        with patch("builtins.open", mock_open(read_data="Hello.")):
            await cog.message_all.callback(cog, interaction, filename="announcement.txt")

        interaction.followup.send.assert_called_once()
        summary = interaction.followup.send.call_args[0][0]
        assert "2" in summary

    @pytest.mark.asyncio
    async def test_reports_partial_success_when_some_dms_fail(self, interaction, mock_backend):
        member_ok = MagicMock()
        member_ok.send = AsyncMock()
        member_fail = MagicMock()
        member_fail.send = AsyncMock(side_effect=Exception("DMs closed"))
        interaction.guild.members = [member_ok, member_fail]

        cog = AdminCog(mock_backend)
        with patch("builtins.open", mock_open(read_data="Hello.")):
            await cog.message_all.callback(cog, interaction, filename="announcement.txt")

        summary = interaction.followup.send.call_args[0][0]
        assert "1" in summary
        assert "2" in summary

    def test_requires_admin_role(self, interaction, mock_backend):
        interaction.user.roles = []
        cog = AdminCog(mock_backend)

        with pytest.raises(app_commands.MissingRole):
            for check in cog.message_all.checks:
                check(interaction)

    @pytest.mark.asyncio
    async def test_file_not_found_sends_error(self, interaction, mock_backend):
        interaction.guild.members = []
        cog = AdminCog(mock_backend)

        with patch("builtins.open", side_effect=FileNotFoundError):
            await cog.message_all.callback(cog, interaction, filename="missing.txt")

        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        assert "missing.txt" in msg
