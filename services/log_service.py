import discord

from config import REWARDS_LOG_CHANNEL_ID


async def send_rewards_log(
    bot: discord.Client,
    guild: discord.Guild | None,
    title: str,
    description: str,
) -> None:
    _ = bot

    if not REWARDS_LOG_CHANNEL_ID:
        return

    if guild is None:
        return

    channel = guild.get_channel(REWARDS_LOG_CHANNEL_ID)

    if channel is None or not hasattr(channel, "send"):
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.gold(),
    )

    try:
        await channel.send(embed=embed)
    except discord.DiscordException:
        return
