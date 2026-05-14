import discord
from discord import app_commands
from discord.ext import commands

from services.marks_service import get_user_history


class HistoryCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="history", description="Show recent Ash Marks history.")
    async def history(
        self,
        interaction: discord.Interaction,
        user: discord.Member | None = None,
        limit: int = 10,
    ) -> None:
        member = user or interaction.user
        limit = max(1, min(limit, 20))
        transactions = get_user_history(member.id, limit)

        embed = discord.Embed(
            title=f"Ash Marks History — {member.display_name}",
            color=discord.Color.dark_teal(),
        )

        if not transactions:
            embed.description = "No Ash Marks history yet."
            await interaction.response.send_message(embed=embed)
            return

        for transaction in transactions:
            comment = transaction["comment"]
            lines = [
                f"{transaction['total_marks']:+} Ash Marks",
                f"Branch: {transaction['branch']}",
                f"Action: {transaction['action_type']}",
                f"Base: {transaction['base_marks']}",
                f"Bonus: {transaction['bonus_marks']}",
            ]

            if comment:
                lines.append(f"Comment: {comment}")

            lines.append(f"Date: {transaction['created_at']}")

            embed.add_field(
                name=f"Transaction #{transaction['id']}",
                value="\n".join(lines),
                inline=False,
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HistoryCommands(bot))
