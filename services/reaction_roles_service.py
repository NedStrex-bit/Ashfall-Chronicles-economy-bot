import discord


REACTION_ROLE_MAP = {
    "📣": "Voice of Ashfall",
    "🎨": "Atelier of Ash",
    "🪙": "Merchant Covenant",
    "🛡️": "Chronicle Wardens",
}


def get_role_name_by_emoji(emoji: str) -> str | None:
    return REACTION_ROLE_MAP.get(emoji)


def find_role(guild: discord.Guild, role_name: str) -> discord.Role | None:
    return discord.utils.get(guild.roles, name=role_name)


async def add_reaction_role(member: discord.Member, emoji: str) -> str:
    role_name = get_role_name_by_emoji(emoji)

    if role_name is None:
        return "unknown_emoji"

    role = find_role(member.guild, role_name)

    if role is None:
        return "role_not_found"

    if role in member.roles:
        return "already_has_role"

    await member.add_roles(role, reason="Reaction role added")
    return "role_added"


async def remove_reaction_role(member: discord.Member, emoji: str) -> str:
    role_name = get_role_name_by_emoji(emoji)

    if role_name is None:
        return "unknown_emoji"

    role = find_role(member.guild, role_name)

    if role is None:
        return "role_not_found"

    if role not in member.roles:
        return "does_not_have_role"

    await member.remove_roles(role, reason="Reaction role removed")
    return "role_removed"
