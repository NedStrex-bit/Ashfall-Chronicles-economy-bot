import discord

from ranks import BRANCH_RANKS, GENERAL_RANKS, get_branch_rank, get_general_rank
from services.marks_service import get_user_progress


def find_role(guild: discord.Guild, role_name: str) -> discord.Role | None:
    return discord.utils.get(guild.roles, name=role_name)


def _add_missing_role(missing_roles: list[str], role_name: str) -> None:
    if role_name not in missing_roles:
        missing_roles.append(role_name)


async def sync_member_roles(member: discord.Member) -> dict[str, list[str]]:
    progress = get_user_progress(member.id)
    total_marks = progress["total_marks"]
    current_general_rank = get_general_rank(total_marks)

    added: list[str] = []
    removed: list[str] = []
    missing_roles: list[str] = []
    role_errors: list[str] = []

    for rank_name in GENERAL_RANKS:
        role = find_role(member.guild, rank_name)

        if role is None:
            _add_missing_role(missing_roles, rank_name)
            continue

        if rank_name != current_general_rank and role in member.roles:
            try:
                await member.remove_roles(role, reason="Ash Marks general rank sync")
                removed.append(role.name)
            except discord.Forbidden:
                role_errors.append(f"Cannot remove {role.name}: missing permissions.")
            except discord.HTTPException:
                role_errors.append(f"Cannot remove {role.name}: Discord API error.")

    current_general_role = find_role(member.guild, current_general_rank)
    if current_general_role is None:
        _add_missing_role(missing_roles, current_general_rank)
    elif current_general_role not in member.roles:
        try:
            await member.add_roles(current_general_role, reason="Ash Marks general rank sync")
            added.append(current_general_role.name)
        except discord.Forbidden:
            role_errors.append(f"Cannot add {current_general_role.name}: missing permissions.")
        except discord.HTTPException:
            role_errors.append(f"Cannot add {current_general_role.name}: Discord API error.")

    for branch, branch_ranks in BRANCH_RANKS.items():
        branch_marks = progress["branches"][branch]
        current_branch_rank = get_branch_rank(branch, branch_marks)

        for rank_name in branch_ranks:
            role = find_role(member.guild, rank_name)

            if role is None:
                _add_missing_role(missing_roles, rank_name)
                continue

            if rank_name != current_branch_rank and role in member.roles:
                try:
                    await member.remove_roles(role, reason="Ash Marks branch rank sync")
                    removed.append(role.name)
                except discord.Forbidden:
                    role_errors.append(f"Cannot remove {role.name}: missing permissions.")
                except discord.HTTPException:
                    role_errors.append(f"Cannot remove {role.name}: Discord API error.")

        if current_branch_rank is None:
            continue

        current_branch_role = find_role(member.guild, current_branch_rank)
        if current_branch_role is None:
            _add_missing_role(missing_roles, current_branch_rank)
        elif current_branch_role not in member.roles:
            try:
                await member.add_roles(current_branch_role, reason="Ash Marks branch rank sync")
                added.append(current_branch_role.name)
            except discord.Forbidden:
                role_errors.append(f"Cannot add {current_branch_role.name}: missing permissions.")
            except discord.HTTPException:
                role_errors.append(f"Cannot add {current_branch_role.name}: Discord API error.")

    return {
        "added": added,
        "removed": removed,
        "missing_roles": missing_roles,
        "role_errors": role_errors,
    }
