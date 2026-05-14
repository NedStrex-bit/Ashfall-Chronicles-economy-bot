import discord
from discord import app_commands
from discord.ext import commands

from config import REVIEW_QUEUE_CHANNEL_ID
from ranks import BRANCHES
from services.submission_service import (
    create_submission,
    mark_submission_approved,
    mark_submission_rejected,
)


def _has_manage_guild(member: discord.abc.User) -> bool:
    permissions = getattr(member, "guild_permissions", None)
    return permissions is not None and permissions.manage_guild


def _set_embed_status(
    embed: discord.Embed,
    status: str,
    reviewer: discord.abc.User,
) -> discord.Embed:
    updated_embed = embed.copy()
    updated_embed.color = discord.Color.green() if status == "approved" else discord.Color.red()
    updated_embed.set_field_at(
        0,
        name="Status",
        value=f"{status} by {reviewer.mention}",
        inline=False,
    )
    return updated_embed


class SubmissionReviewView(discord.ui.View):
    def __init__(self, submission_id: int) -> None:
        super().__init__(timeout=None)
        self.submission_id = submission_id

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def approve(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        _ = button

        if not _has_manage_guild(interaction.user):
            await interaction.response.send_message(
                "You need the Manage Server permission to review submissions.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        submission = mark_submission_approved(self.submission_id, interaction.user.id)
        if submission is None:
            await interaction.followup.send(
                "Submission not found.",
                ephemeral=True,
            )
            return

        for item in self.children:
            item.disabled = True

        if interaction.message and interaction.message.embeds:
            embed = _set_embed_status(
                interaction.message.embeds[0],
                "approved",
                interaction.user,
            )
            await interaction.message.edit(embed=embed, view=self)

        if interaction.channel and hasattr(interaction.channel, "send"):
            await interaction.channel.send(
                f"Submission #{self.submission_id} approved by {interaction.user.mention}."
            )

        await interaction.followup.send(
            "Submission approved. Now award Ash Marks with /approve after verifying the action_key and bonus_key.",
            ephemeral=True,
        )

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        _ = button

        if not _has_manage_guild(interaction.user):
            await interaction.response.send_message(
                "You need the Manage Server permission to review submissions.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        submission = mark_submission_rejected(self.submission_id, interaction.user.id)
        if submission is None:
            await interaction.followup.send(
                "Submission not found.",
                ephemeral=True,
            )
            return

        for item in self.children:
            item.disabled = True

        if interaction.message and interaction.message.embeds:
            embed = _set_embed_status(
                interaction.message.embeds[0],
                "rejected",
                interaction.user,
            )
            await interaction.message.edit(embed=embed, view=self)

        if interaction.channel and hasattr(interaction.channel, "send"):
            await interaction.channel.send(
                f"Submission #{self.submission_id} rejected by {interaction.user.mention}."
            )

        await interaction.followup.send(
            "Submission rejected.",
            ephemeral=True,
        )


class SubmitCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="submit", description="Submit an Ash Marks report.")
    @app_commands.choices(
        branch=[
            app_commands.Choice(name="voice", value="voice"),
            app_commands.Choice(name="atelier", value="atelier"),
            app_commands.Choice(name="merchant", value="merchant"),
            app_commands.Choice(name="wardens", value="wardens"),
        ]
    )
    async def submit(
        self,
        interaction: discord.Interaction,
        branch: app_commands.Choice[str],
        action_type: str,
        proof_url: str,
        description: str,
        metrics: str = "",
    ) -> None:
        if not REVIEW_QUEUE_CHANNEL_ID:
            await interaction.response.send_message(
                "Review queue channel is not configured.",
                ephemeral=True,
            )
            return

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        channel = interaction.guild.get_channel(REVIEW_QUEUE_CHANNEL_ID)

        if channel is None or not hasattr(channel, "send"):
            await interaction.response.send_message(
                "Review queue channel was not found or is not accessible to the bot.",
                ephemeral=True,
            )
            return

        branch_key = branch.value
        proof_url = proof_url.strip()
        description = description.strip()
        metrics = metrics.strip()
        submission_id = create_submission(
            user_id=interaction.user.id,
            branch=branch_key,
            action_type=action_type,
            proof_url=proof_url,
            description=description,
            metrics=metrics,
        )

        embed = discord.Embed(
            title="New Submission for Review",
            color=discord.Color.purple(),
        )
        embed.add_field(name="Status", value="pending", inline=False)
        embed.add_field(name="Submission ID", value=str(submission_id), inline=True)
        embed.add_field(name="Member", value=interaction.user.mention, inline=True)
        embed.add_field(name="User ID", value=str(interaction.user.id), inline=True)
        embed.add_field(name="Branch", value=BRANCHES[branch_key], inline=False)
        embed.add_field(name="Branch Key", value=branch_key, inline=True)
        embed.add_field(name="Action Type", value=action_type, inline=True)
        embed.add_field(name="Proof URL", value=proof_url, inline=False)
        embed.add_field(name="Description", value=description, inline=False)

        if metrics:
            embed.add_field(name="Metrics", value=metrics, inline=False)

        try:
            await channel.send(embed=embed, view=SubmissionReviewView(submission_id))
        except discord.DiscordException:
            await interaction.response.send_message(
                "Failed to send the submission to the review queue.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "Submission sent for review. Staff will check it and award Ash Marks if everything is valid.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SubmitCommands(bot))
