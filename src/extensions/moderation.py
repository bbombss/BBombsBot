import hikari

from src.models import BBombsBot, BBombsBotPlugin

moderation = BBombsBotPlugin("moderation")


@moderation.listener(hikari.GuildMessageCreateEvent)
@moderation.listener(hikari.GuildMessageUpdateEvent)
async def run_automod(
    event: hikari.GuildMessageUpdateEvent | hikari.GuildMessageCreateEvent,
):
    await moderation.app.auto_mod.check(event)


def load(bot: BBombsBot) -> None:
    bot.add_plugin(moderation)


def unload(bot: BBombsBot) -> None:
    bot.remove_plugin(moderation)


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
