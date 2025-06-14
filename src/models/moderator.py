from __future__ import annotations

import datetime
import typing

import hikari

from src.static import WARN_EMBED_COLOUR
from src.models.errors import DirectMessageFailedError

if typing.TYPE_CHECKING:
    from src.models.bot import BBombsBot


class Moderator:
    """Moderator class which carries out moderation actions."""

    def __init__(self, bot: BBombsBot) -> None:
        self.app: BBombsBot = bot

    async def notice(self, member: hikari.Member, guild: hikari.Guild, content: str) -> None:
        """Send a notice to a member regarding moderation.

        Parameters
        ----------
        member : hikari.Member
            The member this notice is for.
        guild : hikari.Guild
            The guild they are a member of.
        content : str
            The message to be delivered with the notice.

        """
        try:
            await member.send(
                embed=hikari.Embed(
                    title=f":warning: Moderation Notice From {guild.name if guild.name else 'Unknown Server'}",
                    description=content,
                    colour=WARN_EMBED_COLOUR,
                )
            )
        except hikari.ForbiddenError:
            raise DirectMessageFailedError

    async def timeout(
        self, member: hikari.Member, guild: hikari.Guild, duration: datetime.datetime, reason: str
    ) -> None:
        """Timeout a member.

        Parameters
        ----------
        member : hikari.Member
            The member this notice is for.
        guild : hikari.Guild
            The guild they are a member of.
        duration : datetime.datetime
            The timestamp at which the timeout should end.
        reason : str
            The reason for the timeout.

        """
        expiration = duration.strftime("%X %x")
        msg = f"""You have received a timeout for violating a moderation policy: **{reason}**
Your timeout expires: {expiration} UTC."""
        await member.edit(
            communication_disabled_until=duration, reason=f"Timed out for {reason} until {expiration} UTC."
        )
        await self.notice(member, guild, msg)


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
