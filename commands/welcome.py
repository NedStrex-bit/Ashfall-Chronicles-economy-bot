import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import WELCOME_CHANNEL_ID
from services.welcome_service import build_welcome_message


logger = logging.getLogger(__name__)


class WelcomeCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _get_welcome_channel(
        self,
        guild: discord.Guild,
    ) -> discord.abc.Messageable | None:
        if WELCOME_CHANNEL_ID == 0:
            return None

        channel = guild.get_channel(WELCOME_CHANNEL_ID)

        if channel is None or not hasattr(channel, "send"):
            return None

        return channel

    @app_commands.command(
        name="test_welcome",
        description="Send a test welcome message.",
    )
    async def test_welcome(
        self,
        interaction: discord.Interaction,
        user: discord.Member | None = None,
    ) -> None:
        permissions = getattr(interaction.user, "guild_permissions", None)

        if permissions is None or not permissions.manage_guild:
            await interaction.response.send_message(
                "You need the Manage Server permission to use this command.",
                ephemeral=True,
            )
            return

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        target_member = user or interaction.user
        channel = self._get_welcome_channel(interaction.guild) or interaction.channel

        if channel is None or not hasattr(channel, "send"):
            await interaction.response.send_message(
                "No available channel found for the test welcome message.",
                ephemeral=True,
            )
            return

        message = build_welcome_message(target_member)

        try:
            await channel.send(message)
        except discord.Forbidden:
            await interaction.response.send_message(
                "Discord denied sending the test welcome message. Check the bot permissions.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            await interaction.response.send_message(
                "Discord API returned an error while sending the test welcome message.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "Test welcome message sent.",
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return

        if WELCOME_CHANNEL_ID == 0:
            logger.warning("WELCOME_CHANNEL_ID is not configured.")
            return

        channel = self._get_welcome_channel(member.guild)

        if channel is None:
            logger.warning("Welcome channel %s was not found.", WELCOME_CHANNEL_ID)
            return

        message = build_welcome_message(member)

        try:
            await channel.send(message)
        except discord.Forbidden:
            logger.warning("Cannot send welcome message: missing permissions.")
        except discord.HTTPException:
            logger.warning("Cannot send welcome message: Discord API error.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCommands(bot))
