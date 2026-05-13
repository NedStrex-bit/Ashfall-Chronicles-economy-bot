import discord
from discord import app_commands
from discord.ext import commands

from ranks import BRANCHES
from services.marks_service import get_leaderboard


class LeaderboardCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="leaderboard", description="Show Ash Marks leaderboard.")
    @app_commands.choices(
        branch=[
            app_commands.Choice(name="total", value="total"),
            app_commands.Choice(name="voice", value="voice"),
            app_commands.Choice(name="atelier", value="atelier"),
            app_commands.Choice(name="merchant", value="merchant"),
            app_commands.Choice(name="wardens", value="wardens"),
        ]
    )
    async def leaderboard(
        self,
        interaction: discord.Interaction,
        branch: app_commands.Choice[str] | None = None,
        limit: int = 10,
    ) -> None:
        branch_key = branch.value if branch else "total"
        limit = max(1, min(limit, 20))
        rows = get_leaderboard(branch_key, limit)

        title = "Ash Marks Leaderboard"
        if branch_key != "total":
            title = f"{BRANCHES[branch_key]} Leaderboard"

        embed = discord.Embed(
            title=title,
            color=discord.Color.dark_gold(),
        )

        if not rows:
            embed.description = "No users with Ash Marks yet."
            await interaction.response.send_message(embed=embed)
            return

        lines = []
        guild = interaction.guild

        for index, row in enumerate(rows, start=1):
            user_id = row["user_id"]
            member = guild.get_member(user_id) if guild else None
            user_display = member.mention if member else str(user_id)
            lines.append(f"{index}. {user_display} — {row['marks']} Ash Marks")

        embed.description = "\n".join(lines)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LeaderboardCommands(bot))
