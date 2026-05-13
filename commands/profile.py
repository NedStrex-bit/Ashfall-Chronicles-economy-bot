import discord
from discord import app_commands
from discord.ext import commands

from ranks import BRANCHES, get_branch_rank, get_general_rank
from services.marks_service import get_user_progress


class ProfileCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="profile", description="Show an Ashfall member profile.")
    async def profile(
        self,
        interaction: discord.Interaction,
        user: discord.Member | None = None,
    ) -> None:
        member = user or interaction.user
        progress = get_user_progress(member.id)

        total_marks = progress["total_marks"]
        embed = discord.Embed(
            title=f"{member.display_name}'s Ashfall Profile",
            color=discord.Color.dark_gold(),
        )
        embed.add_field(name="User", value=member.mention, inline=False)
        embed.add_field(name="Total Ash Marks", value=str(total_marks), inline=True)
        embed.add_field(
            name="General Status",
            value=get_general_rank(total_marks),
            inline=True,
        )

        for branch_key, branch_name in BRANCHES.items():
            branch_marks = progress["branches"][branch_key]
            branch_rank = get_branch_rank(branch_key, branch_marks) or "No rank"
            embed.add_field(
                name=branch_name,
                value=f"{branch_marks} marks\n{branch_rank}",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProfileCommands(bot))
