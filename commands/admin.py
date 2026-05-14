import discord
from discord import app_commands
from discord.ext import commands

from actions import (
    BONUS_REWARDS,
    get_action_choices_for_branch,
    get_action_marks,
    get_bonus_marks,
)
from ranks import BRANCHES, get_branch_rank, get_general_rank
from services.log_service import send_rewards_log
from services.marks_service import (
    add_marks,
    adjust_marks,
    get_user_progress,
    validate_limits,
)
from services.roles_service import sync_member_roles


class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _has_manage_guild(self, interaction: discord.Interaction) -> bool:
        permissions = getattr(interaction.user, "guild_permissions", None)

        if permissions is None or not permissions.manage_guild:
            await interaction.response.send_message(
                "You need the Manage Server permission to use this command.",
                ephemeral=True,
            )
            return False

        return True

    @app_commands.command(name="approve", description="Approve Ash Marks for a member.")
    @app_commands.choices(
        branch=[
            app_commands.Choice(name="voice", value="voice"),
            app_commands.Choice(name="atelier", value="atelier"),
            app_commands.Choice(name="merchant", value="merchant"),
            app_commands.Choice(name="wardens", value="wardens"),
        ]
    )
    async def approve(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        branch: app_commands.Choice[str],
        action_key: str,
        bonus_key: str = "",
        proof_url: str = "",
        comment: str = "",
    ) -> None:
        if not await self._has_manage_guild(interaction):
            return

        branch_key = branch.value
        action_key = action_key.strip()
        bonus_key = bonus_key.strip()
        proof_url = proof_url.strip()
        comment = comment.strip()

        base_marks = get_action_marks(branch_key, action_key)
        if base_marks is None:
            available_actions = ", ".join(get_action_choices_for_branch(branch_key))
            await interaction.response.send_message(
                f"Unknown action_key for {branch_key}. Available action_key values: {available_actions}",
                ephemeral=True,
            )
            return

        bonus_marks = 0
        if bonus_key:
            bonus_marks_value = get_bonus_marks(branch_key, bonus_key)

            if bonus_marks_value is None:
                available_bonus_keys = ", ".join(BONUS_REWARDS.get(branch_key, {}))
                if not available_bonus_keys:
                    available_bonus_keys = "no bonus_key values available for this branch"

                await interaction.response.send_message(
                    f"Unknown bonus_key for {branch_key}. Available bonus_key values: {available_bonus_keys}",
                    ephemeral=True,
                )
                return

            bonus_marks = bonus_marks_value

        is_allowed, limit_reason = validate_limits(
            user.id,
            branch_key,
            action_key,
            base_marks,
        )
        if not is_allowed:
            await interaction.response.send_message(limit_reason, ephemeral=True)
            return

        total_added = base_marks + bonus_marks

        progress = add_marks(
            user_id=user.id,
            admin_id=interaction.user.id,
            branch=branch_key,
            action_type=action_key,
            base_marks=base_marks,
            bonus_marks=bonus_marks,
            proof_url=proof_url or None,
            comment=comment or None,
        )

        total_marks = progress["total_marks"]
        branch_marks = progress["branches"][branch_key]
        general_rank = get_general_rank(total_marks)
        branch_rank = get_branch_rank(branch_key, branch_marks) or "No branch rank yet"
        role_changes = await sync_member_roles(user)

        embed = discord.Embed(
            title="Ash Marks Approved",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Member", value=user.mention, inline=True)
        embed.add_field(name="Branch", value=BRANCHES[branch_key], inline=True)
        embed.add_field(name="Action", value=action_key, inline=False)
        if bonus_key:
            embed.add_field(name="Bonus Key", value=bonus_key, inline=False)
        embed.add_field(name="Base", value=str(base_marks), inline=True)
        embed.add_field(name="Bonus", value=str(bonus_marks), inline=True)
        embed.add_field(name="Total Added", value=str(total_added), inline=True)
        embed.add_field(name="Total Balance", value=str(total_marks), inline=True)
        embed.add_field(name="General Status", value=general_rank, inline=True)
        embed.add_field(name="Branch Balance", value=str(branch_marks), inline=True)
        embed.add_field(name="Branch Rank", value=branch_rank, inline=True)
        embed.add_field(
            name="Roles Added",
            value=", ".join(role_changes["added"]) or "None",
            inline=False,
        )
        embed.add_field(
            name="Roles Removed",
            value=", ".join(role_changes["removed"]) or "None",
            inline=False,
        )

        if role_changes["missing_roles"]:
            embed.add_field(
                name="Missing Roles",
                value=", ".join(role_changes["missing_roles"]),
                inline=False,
            )

        if role_changes["role_errors"]:
            embed.add_field(
                name="Role Errors",
                value="\n".join(role_changes["role_errors"]),
                inline=False,
            )

        if proof_url:
            embed.add_field(name="Proof", value=proof_url, inline=False)

        if comment:
            embed.add_field(name="Comment", value=comment, inline=False)

        log_lines = [
            f"Admin: {interaction.user.mention}",
            f"Member: {user.mention}",
            f"Branch: {BRANCHES[branch_key]}",
            f"Action: {action_key}",
            f"Base marks: {base_marks}",
            f"Bonus key: {bonus_key or 'None'}",
            f"Bonus marks: {bonus_marks}",
            f"Total: {total_added}",
            f"Proof: {proof_url or 'None'}",
            f"Comment: {comment or 'None'}",
        ]
        await send_rewards_log(
            self.bot,
            interaction.guild,
            "Ash Marks Approved",
            "\n".join(log_lines),
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="sync_roles",
        description="Synchronize Ash Marks progression roles for a member.",
    )
    async def sync_roles(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
    ) -> None:
        if not await self._has_manage_guild(interaction):
            return

        role_changes = await sync_member_roles(user)

        embed = discord.Embed(
            title="Ashfall Roles Synced",
            color=discord.Color.green(),
        )
        embed.add_field(name="Member", value=user.mention, inline=False)
        embed.add_field(
            name="Roles Added",
            value=", ".join(role_changes["added"]) or "No roles added",
            inline=False,
        )
        embed.add_field(
            name="Roles Removed",
            value=", ".join(role_changes["removed"]) or "No roles removed",
            inline=False,
        )

        if role_changes["missing_roles"]:
            embed.add_field(
                name="Missing Roles",
                value=", ".join(role_changes["missing_roles"]),
                inline=False,
            )

        if role_changes["role_errors"]:
            embed.add_field(
                name="Role Errors",
                value="\n".join(role_changes["role_errors"]),
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="adjust", description="Manually adjust Ash Marks.")
    @app_commands.choices(
        branch=[
            app_commands.Choice(name="voice", value="voice"),
            app_commands.Choice(name="atelier", value="atelier"),
            app_commands.Choice(name="merchant", value="merchant"),
            app_commands.Choice(name="wardens", value="wardens"),
        ]
    )
    async def adjust(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        branch: app_commands.Choice[str],
        amount: int,
        reason: str,
    ) -> None:
        if not await self._has_manage_guild(interaction):
            return

        branch_key = branch.value
        reason = reason.strip()
        previous_progress = get_user_progress(user.id)
        previous_branch_marks = previous_progress["branches"][branch_key]

        progress = adjust_marks(
            user_id=user.id,
            admin_id=interaction.user.id,
            branch=branch_key,
            amount=amount,
            reason=reason,
        )
        role_changes = await sync_member_roles(user)

        new_total_marks = progress["total_marks"]
        new_branch_marks = progress["branches"][branch_key]
        actual_change = new_branch_marks - previous_branch_marks

        embed = discord.Embed(
            title="Ash Marks Adjusted",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Member", value=user.mention, inline=True)
        embed.add_field(name="Branch", value=BRANCHES[branch_key], inline=True)
        embed.add_field(name="Change", value=str(actual_change), inline=True)
        embed.add_field(name="Reason", value=reason or "Not provided", inline=False)
        embed.add_field(
            name="New Total Balance",
            value=str(new_total_marks),
            inline=True,
        )
        embed.add_field(
            name="New Branch Balance",
            value=str(new_branch_marks),
            inline=True,
        )
        embed.add_field(
            name="Roles Added",
            value=", ".join(role_changes["added"]) or "No roles added",
            inline=False,
        )
        embed.add_field(
            name="Roles Removed",
            value=", ".join(role_changes["removed"]) or "No roles removed",
            inline=False,
        )

        if role_changes["missing_roles"]:
            embed.add_field(
                name="Missing Roles",
                value=", ".join(role_changes["missing_roles"]),
                inline=False,
            )

        if role_changes["role_errors"]:
            embed.add_field(
                name="Role Errors",
                value="\n".join(role_changes["role_errors"]),
                inline=False,
            )

        log_lines = [
            f"Admin: {interaction.user.mention}",
            f"Member: {user.mention}",
            f"Branch: {BRANCHES[branch_key]}",
            f"Amount: {amount}",
            f"Reason: {reason or 'None'}",
        ]
        await send_rewards_log(
            self.bot,
            interaction.guild,
            "Ash Marks Adjusted",
            "\n".join(log_lines),
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="remove_marks", description="Remove Ash Marks from a member.")
    @app_commands.choices(
        branch=[
            app_commands.Choice(name="voice", value="voice"),
            app_commands.Choice(name="atelier", value="atelier"),
            app_commands.Choice(name="merchant", value="merchant"),
            app_commands.Choice(name="wardens", value="wardens"),
        ]
    )
    async def remove_marks(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        branch: app_commands.Choice[str],
        amount: int,
        reason: str,
    ) -> None:
        if not await self._has_manage_guild(interaction):
            return

        if amount <= 0:
            await interaction.response.send_message(
                "amount must be a positive number.",
                ephemeral=True,
            )
            return

        branch_key = branch.value
        reason = reason.strip()
        previous_progress = get_user_progress(user.id)
        previous_branch_marks = previous_progress["branches"][branch_key]

        progress = adjust_marks(
            user_id=user.id,
            admin_id=interaction.user.id,
            branch=branch_key,
            amount=-amount,
            reason=reason,
        )
        role_changes = await sync_member_roles(user)

        new_total_marks = progress["total_marks"]
        new_branch_marks = progress["branches"][branch_key]
        actual_removed = previous_branch_marks - new_branch_marks

        embed = discord.Embed(
            title="Ash Marks Removed",
            color=discord.Color.red(),
        )
        embed.add_field(name="Member", value=user.mention, inline=True)
        embed.add_field(name="Branch", value=BRANCHES[branch_key], inline=True)
        embed.add_field(name="Removed", value=str(actual_removed), inline=True)
        embed.add_field(name="Reason", value=reason or "Not provided", inline=False)
        embed.add_field(
            name="New Total Balance",
            value=str(new_total_marks),
            inline=True,
        )
        embed.add_field(
            name="New Branch Balance",
            value=str(new_branch_marks),
            inline=True,
        )
        embed.add_field(
            name="Roles Added",
            value=", ".join(role_changes["added"]) or "No roles added",
            inline=False,
        )
        embed.add_field(
            name="Roles Removed",
            value=", ".join(role_changes["removed"]) or "No roles removed",
            inline=False,
        )

        if role_changes["missing_roles"]:
            embed.add_field(
                name="Missing Roles",
                value=", ".join(role_changes["missing_roles"]),
                inline=False,
            )

        if role_changes["role_errors"]:
            embed.add_field(
                name="Role Errors",
                value="\n".join(role_changes["role_errors"]),
                inline=False,
            )

        log_lines = [
            f"Admin: {interaction.user.mention}",
            f"Member: {user.mention}",
            f"Branch: {BRANCHES[branch_key]}",
            f"Requested remove amount: {amount}",
            f"Actual removed: {actual_removed}",
            f"Reason: {reason or 'None'}",
        ]
        await send_rewards_log(
            self.bot,
            interaction.guild,
            "Ash Marks Removed",
            "\n".join(log_lines),
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCommands(bot))
