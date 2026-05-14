import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import PATH_MESSAGE_ID
from services.log_service import send_rewards_log
from services.reaction_roles_service import (
    add_reaction_role,
    get_role_name_by_emoji,
    remove_reaction_role,
)


logger = logging.getLogger(__name__)


PATH_MESSAGE_TEXT = """Choose your path 🜂

React below to unlock a branch:

📣 — The Voice of Ashfall
For those who help spread the word: posts, stories, reels, shorts, reviews, threads, and other public content.

🎨 — The Atelier of Ash
For creators and painters: painted models, printed scenes, fan art, dioramas, moodboards, showcases, and painting videos.

🪙 — The Merchant Covenant
For backers and supporters: Kickstarter backing, add-ons, late pledges, merchant support, and repeated campaign support.

🛡️ — The Chronicle Wardens
For testers and feedback-givers: printed models, print reports, settings, structured feedback, bug reports, polls, and beta test notes.

You can choose one path or several.
Remove your reaction to leave a branch."""

PATH_REACTIONS = ["📣", "🎨", "🪙", "🛡️"]


class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _log_reaction_role_change(
        self,
        guild: discord.Guild | None,
        title: str,
        description: str,
    ) -> None:
        logger.info(description)
        try:
            await send_rewards_log(self.bot, guild, title, description)
        except discord.HTTPException:
            logger.warning("Failed to send reaction role log to Discord.")

    @app_commands.command(
        name="create_path_message",
        description="Create the choose-your-path reaction roles message.",
    )
    async def create_path_message(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        permissions = getattr(interaction.user, "guild_permissions", None)

        if permissions is None or not permissions.manage_guild:
            await interaction.response.send_message(
                "You need the Manage Server permission to use this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            message = await channel.send(PATH_MESSAGE_TEXT)

            for emoji in PATH_REACTIONS:
                await message.add_reaction(emoji)
        except discord.Forbidden:
            logger.warning("Cannot create path message or add reactions: forbidden.")
            await interaction.followup.send(
                "Discord denied creating the message or adding reactions. Check the bot permissions in the selected channel.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            logger.warning("Cannot create path message or add reactions: HTTP error.")
            await interaction.followup.send(
                "Discord API returned an error while creating the reaction roles message. Try again later.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            (
                "Reaction roles message created.\n"
                f"Message ID: `{message.id}`\n"
                "Add this ID to `.env` as `PATH_MESSAGE_ID` and restart the bot."
            ),
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        if PATH_MESSAGE_ID == 0:
            return

        if payload.message_id != PATH_MESSAGE_ID:
            return

        if payload.guild_id is None:
            return

        if payload.member is None:
            return

        if payload.member.bot:
            return

        emoji = str(payload.emoji)

        try:
            result = await add_reaction_role(payload.member, emoji)
        except discord.Forbidden:
            logger.warning("Reaction role add forbidden for emoji %s.", emoji)
            return
        except discord.HTTPException:
            logger.warning("Reaction role add HTTP error for emoji %s.", emoji)
            return

        if result == "unknown_emoji":
            return

        if result == "role_not_found":
            logger.warning("Reaction role not found for emoji %s.", emoji)
            return

        if result == "role_added":
            role_name = get_role_name_by_emoji(emoji)
            description = (
                f"Reaction role added: {payload.member.mention} -> {role_name} by {emoji}"
            )
            await self._log_reaction_role_change(
                payload.member.guild,
                "Reaction Role Added",
                description,
            )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        if PATH_MESSAGE_ID == 0:
            return

        if payload.message_id != PATH_MESSAGE_ID:
            return

        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)

        if guild is None:
            return

        member = guild.get_member(payload.user_id)

        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.NotFound:
                return
            except discord.Forbidden:
                logger.warning(
                    "Cannot fetch member %s: missing permissions.",
                    payload.user_id,
                )
                return
            except discord.HTTPException:
                logger.warning(
                    "Cannot fetch member %s: Discord API error.",
                    payload.user_id,
                )
                return

        if member.bot:
            return

        emoji = str(payload.emoji)

        try:
            result = await remove_reaction_role(member, emoji)
        except discord.Forbidden:
            logger.warning("Reaction role remove forbidden for emoji %s.", emoji)
            return
        except discord.HTTPException:
            logger.warning("Reaction role remove HTTP error for emoji %s.", emoji)
            return

        if result == "unknown_emoji":
            return

        if result == "role_not_found":
            logger.warning("Reaction role not found for emoji %s.", emoji)
            return

        if result == "role_removed":
            role_name = get_role_name_by_emoji(emoji)
            description = f"Reaction role removed: {member.mention} -> {role_name} by {emoji}"
            await self._log_reaction_role_change(
                member.guild,
                "Reaction Role Removed",
                description,
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
