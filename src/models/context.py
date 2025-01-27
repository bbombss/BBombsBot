from __future__ import annotations

import typing as t

import hikari
import hikari.errors
import lightbulb

if t.TYPE_CHECKING:
    from src.models.bot import BBombsBot

from src.models.views import ConfirmationView
from src.static import *

__all__ = ["BBombsBotContext", "BBombsBotPrefixContext", "BBombsBotSlashContext"]


class BBombsBotContext(lightbulb.Context):
    """BBombsBot base context object."""

    @property
    def app(self) -> BBombsBot:
        """Returns the current application."""
        return super().app  # type: ignore

    async def wait(self) -> lightbulb.ResponseProxy:
        """Create a response with loading a message."""
        return await self.respond(f"{LOADING_EMOJI} Waiting for server...")

    async def respond_with_success(
        self,
        content: str,
        title: str | None = None,
        edit: bool = False,
        ephemeral: bool = False,
    ) -> lightbulb.ResponseProxy:
        """Create a response with a success embed.

        Parameters
        ----------
        content : str
            Content to be passed to the description field of the embed.
        title : str, optional
            Title to be passed to the title field of the embed, defaults to None.
        edit : bool, optional
            Whether an original response should be edited.
        ephemeral : bool, optional
            Whether the message should have the ephemeral flag, defaults to False.

        Returns
        -------
        message : lightbulb.ResponseProxy
            The message that was created as a response.

        """
        embed = hikari.Embed(
            title=title,
            description=f"{SUCCESS_EMOJI} {content}",
            colour=SUCCESS_EMBED_COLOUR,
        )

        flags = hikari.MessageFlag.EPHEMERAL if ephemeral else hikari.UNDEFINED

        assert self.previous_response is not None

        if edit and await self.edit_last_response("", embed=embed, components=[]):
            return self.previous_response

        return await self.respond(embed=embed, flags=flags)

    async def respond_with_failure(
        self,
        content: str,
        title: str | None = None,
        edit: bool = False,
        ephemeral: bool = False,
    ) -> lightbulb.ResponseProxy:
        """Create a response with a failure embed.

        Parameters
        ----------
        content : str
            Content to be passed to the description field of the embed.
        title : str, optional
            Title to be passed to the title field of the embed, defaults to None.
        edit : bool, optional
            Whether an original response should be edited, defaults to False.
        ephemeral : bool, optional
            Whether the message should have the ephemeral flag, defaults to False.

        Returns
        -------
        message : lightbulb.ResponseProxy
            The message that was created as a response.

        """
        embed = hikari.Embed(
            title=title,
            description=f"{FAIL_EMOJI} {content}",
            colour=FAIL_EMBED_COLOUR,
        )

        flags = hikari.MessageFlag.EPHEMERAL if ephemeral else hikari.UNDEFINED

        assert self.previous_response is not None

        if edit and await self.edit_last_response("", embed=embed, components=[]):
            return self.previous_response

        return await self.respond(embed=embed, flags=flags)

    async def get_confirmation(
        self,
        *args,
        confirm_msg: dict[str, t.Any] | None = None,
        cancel_msg: dict[str, t.Any] | None = None,
        timeout: float = 120,
        edit: bool = False,
        **kwargs,
    ) -> bool | None:
        """Prompt the author with a confirmation menu.

        Parameters
        ----------
        confirm_msg : dict[str, Any], optional
            Keyword arguments to be passed to the confirmation response, defaults to None.
        cancel_msg : dict[str, Any], optional
            Keyword arguments to be passed to the cancel response, defaults to None.
        timeout : float, optional
            Timeout for confirmation prompt, defaults to 120.
        edit : bool
            Whether the original response should be edited.
        *args : Any
            Arguments passed to the confirmation response.
        **kwargs
            Keyword arguments to be passed to the confirmation response.

        Returns
        -------
        value : bool
            A boolean representing the users response, or none if timeout.

        """
        view = ConfirmationView(self, timeout, confirm_msg, cancel_msg)
        message: hikari.Message | None = None

        if edit:
            message = await self.edit_last_response(*args, components=view, **kwargs)
        if message is None:
            resp = await self.respond(*args, components=view, **kwargs)
            message = await resp.message()

        self.app.miru_client.start_view(view, bind_to=message)
        await view.wait()
        return view.value


class BBombsBotApplicationContext(BBombsBotContext, lightbulb.ApplicationContext):
    """BBombsBot ApplicationContext object."""


class BBombsBotSlashContext(BBombsBotApplicationContext, lightbulb.SlashContext):
    """BBombsBot SlashContext object."""


class BBombsBotPrefixContext(BBombsBotContext, lightbulb.PrefixContext):
    """BBombsBot SlashContext object."""


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
