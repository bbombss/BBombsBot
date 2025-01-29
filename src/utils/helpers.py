from __future__ import annotations

import os
import typing as t

import aiofiles
import hikari
import hikari.guilds
import lightbulb

if t.TYPE_CHECKING:
    from src.models.bot import BBombsBot

from src.static.re import *


def has_permissions(
    member: hikari.Member, perms: hikari.Permissions, strict: bool = True
) -> bool:
    """Will return true if a member has specified permissions.

    Parameters
    ----------
    member : hikari.Member
        The member to check.
    perms : hikari.Permissions
        The permissions to check for.
    strict : bool
        Whether the member must poses all or at least one of the permissions.
        Defaults to True.

    """
    member_perms: hikari.Permissions = lightbulb.utils.permissions_for(member)

    if member_perms == hikari.Permissions.NONE:
        return False

    if strict and (member_perms & perms) == perms:
        return True

    elif not strict:
        for perm in perms:
            if perm in member_perms:
                return True

    return False


def higher_role(member: hikari.Member, bot: hikari.Member) -> bool:
    """Will return true if the members highest role is higher than the bots.

    Parameters
    ----------
    member : hikari.Member
        The member to check.
    bot : hikari.Member
        The bot member for the relevant server.

    """
    member_role = member.get_top_role()
    bot_role = bot.get_top_role()
    assert member_role is not None
    assert bot_role is not None

    return member_role.position > bot_role.position


def can_mod(member: hikari.Member, bot: hikari.Member) -> bool:
    """Will return true if the bot can moderate the member.

    Parameters
    ----------
    member : hikari.Member
        The member to check.
    bot : hikari.Member
        The bot member for the relevant server.

    """
    guild = member.get_guild()

    if guild is None:
        return False

    if guild.owner_id == member.id:
        return False

    if higher_role(member, bot):
        return False

    perms: hikari.Permissions = (
        hikari.Permissions.ADMINISTRATOR | hikari.Permissions.MANAGE_GUILD
    )

    return not has_permissions(member, perms, strict=False)


async def domain_in_list(url: str, path: str) -> bool:
    """Will return true if the provided url is in the provided domains list.

    Parameters
    ----------
    url : str
        A valid url to check.
        Returns False if a valid url is not given.
    path : str
        Path to the list file.

    """
    if match := URL_REGEX.fullmatch(url.lower()):
        if match.group(3)[0] != "/":
            domain = match.group(2) + match.group(3)
        else:
            domain = match.group(2)

        async with aiofiles.open(path, "r", encoding="utf-8") as list:
            async for url in list:
                if url.strip() == domain:
                    return True

    return False


async def get_app_version(app: BBombsBot) -> str:
    """Will return the version of BBombsBot included in project file."""
    path = os.path.join(app.base_dir, "pyproject.toml")
    version: str = "2.0.0"

    async with aiofiles.open(path, "r", encoding="utf-8") as file:
        async for line in file:
            if line.startswith("version"):
                version = line[11:-2]
                break

    return version


# Copyright (C) 2025 BBombs

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
