import os

from dotenv import load_dotenv


load_dotenv()


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID_RAW = os.getenv("GUILD_ID")
REWARDS_LOG_CHANNEL_ID_RAW = os.getenv("REWARDS_LOG_CHANNEL_ID", "0")
REVIEW_QUEUE_CHANNEL_ID_RAW = os.getenv("REVIEW_QUEUE_CHANNEL_ID", "0")
PATH_MESSAGE_ID_RAW = os.getenv("PATH_MESSAGE_ID", "0")


if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set. Add it to your .env file.")

if not GUILD_ID_RAW:
    raise RuntimeError("GUILD_ID is not set. Add it to your .env file.")

try:
    GUILD_ID = int(GUILD_ID_RAW)
except ValueError as exc:
    raise RuntimeError("GUILD_ID must be a Discord server ID number.") from exc

try:
    REWARDS_LOG_CHANNEL_ID = int(REWARDS_LOG_CHANNEL_ID_RAW or "0")
except ValueError:
    REWARDS_LOG_CHANNEL_ID = 0

try:
    REVIEW_QUEUE_CHANNEL_ID = int(REVIEW_QUEUE_CHANNEL_ID_RAW or "0")
except ValueError:
    REVIEW_QUEUE_CHANNEL_ID = 0

try:
    PATH_MESSAGE_ID = int(PATH_MESSAGE_ID_RAW or "0")
except ValueError:
    PATH_MESSAGE_ID = 0
