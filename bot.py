import sqlite3

import discord
from discord import app_commands
from discord.ext import commands

from config import DISCORD_TOKEN, GUILD_ID
from database import init_db


class AshfallBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.reactions = True

        super().__init__(command_prefix="!", intents=intents)
        self.guild = discord.Object(id=GUILD_ID)

    async def setup_hook(self) -> None:
        init_db()
        await self.load_extensions()
        self.tree.copy_global_to(guild=self.guild)
        synced_commands = await self.tree.sync(guild=self.guild)
        print(f"Synced {len(synced_commands)} command(s) for guild {GUILD_ID}.")

    async def load_extensions(self) -> None:
        await self.load_extension("commands.admin")
        await self.load_extension("commands.history")
        await self.load_extension("commands.leaderboard")
        await self.load_extension("commands.profile")
        await self.load_extension("commands.reaction_roles")
        await self.load_extension("commands.submit")
        await self.load_extension("commands.welcome")

    async def on_ready(self) -> None:
        print(f"Ashfall bot is running as {self.user}.")


bot = AshfallBot()


async def send_ephemeral_error(
    interaction: discord.Interaction,
    message: str,
) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    original_error = getattr(error, "original", error)

    if isinstance(original_error, app_commands.MissingPermissions):
        message = "You do not have permission to use this command."
    elif isinstance(original_error, app_commands.CheckFailure):
        message = "This command is not available for your role or context."
    elif isinstance(original_error, ValueError):
        message = f"Invalid input: {original_error}"
    elif isinstance(original_error, sqlite3.Error):
        message = "Database error. Try again later or contact the staff."
    elif isinstance(original_error, discord.Forbidden):
        message = "Discord denied this action. Check the bot permissions and role position."
    elif isinstance(original_error, discord.HTTPException):
        message = "Discord API returned an error. Try again later."
    else:
        message = "An unexpected error occurred. Contact the staff."
        print(f"Unhandled app command error: {original_error!r}")

    try:
        await send_ephemeral_error(interaction, message)
    except discord.HTTPException:
        print(f"Failed to send app command error response: {original_error!r}")


bot.tree.on_error = on_app_command_error


@bot.tree.command(name="ping", description="Check whether the bot is running.")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Pong! Bot is working.")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
