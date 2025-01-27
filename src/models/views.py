import typing as t

import hikari
import lightbulb
import miru

from src.static import *


class AuthorOnlyView(miru.View):
    """A view that can only be interacted with by the interaction author."""

    def __init__(
        self,
        lightbulb_ctx: lightbulb.Context,
        *,
        timeout: float | None = 120,
        autodefer: bool = True,
    ) -> None:
        super().__init__(timeout=timeout, autodefer=autodefer)
        self.lightbulb_ctx = lightbulb_ctx

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        if ctx.user.id != self.lightbulb_ctx.author.id:
            await ctx.respond(
                embed=hikari.Embed(
                    title=None,
                    description=f"{FAIL_EMOJI} You cannot interact with this menu.",
                    colour=FAIL_EMBED_COLOUR,
                ),
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            return False

        return True


class ConfirmationView(AuthorOnlyView):
    """A view for prompting a user for confirmation."""

    def __init__(
        self,
        lightbulb_ctx: lightbulb.Context,
        timeout: float,
        confirm_msg: dict[str, t.Any] | None = None,
        cancel_msg: dict[str, t.Any] | None = None,
    ) -> None:
        super().__init__(lightbulb_ctx, timeout=timeout)
        self.confirm_msg = confirm_msg
        self.cancel_msg = cancel_msg
        self.value: bool

    @miru.button(emoji="✔️", style=hikari.ButtonStyle.SUCCESS)
    async def confirm_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.value = True
        for item in self.children:
            item.disabled = True
        await ctx.edit_response(components=self)

        if self.confirm_msg:
            await ctx.respond(**self.confirm_msg)
        self.stop()

    @miru.button(emoji="❌", style=hikari.ButtonStyle.SECONDARY)
    async def cancel_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.value = False
        for item in self.children:
            item.disabled = True
        await ctx.edit_response(components=self)

        if self.cancel_msg:
            await ctx.respond(**self.cancel_msg)
        self.stop()


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
