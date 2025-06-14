from __future__ import annotations

import datetime
import enum
import os
import typing as t
from contextlib import suppress

import hikari
from Levenshtein import distance

if t.TYPE_CHECKING:
    from src.models.bot import BBombsBot

from src.models.database_member import DatabaseMember
from src.models.ratelimiter import MessageRateLimiter
from src.models.safebrowsing import SafebrowsingClient
from src.static.re import *
from src.utils import can_mod, domain_in_list

MESSAGE_SPAM_RATELIMITER = MessageRateLimiter(5, 5)
DUPLICATE_SPAM_RATELIMITER = MessageRateLimiter(10, 4, 4)
INVITE_SPAM_RATELIMITER = MessageRateLimiter(30, 2)
LINK_SPAM_RATELIMITER = MessageRateLimiter(30, 3)
ATTACHMENT_SPAM_RATELIMITER = MessageRateLimiter(30, 2)
MENTION_SPAM_RATELIMITER = MessageRateLimiter(30, 3, 2)

# Placeholder for custom configurations
BLOCK_INVITES = True
BLOCK_FAKE_URL = True
MENTION_FILTER_LIMIT = 9


class AutoModMediaType(enum.Enum):
    """Types of media the automod handles as enums."""

    MENTION = "mentions"
    INVITE = "invites"
    LINK = "links"
    HYPERLINK = "hyperlinks"
    ATTACHMENT = "attachments"
    DUPLICATE = "duplicates"
    MESSAGE = "messages"
    UNDEFINED = "undefined"


class AutoModOffenceType(enum.Enum):
    """Types of offences the automod handles as enums."""

    SPAM = "spam"
    BLOCKED = "blocked"


class AutoMod:
    """AutoMod class for automatically moderating members."""

    def __init__(self, app: BBombsBot) -> None:
        self._app: BBombsBot = app
        self._lists_dir: str = os.path.join(app.base_dir, "src", "static", "lists")
        self._safebrowsing_client = SafebrowsingClient(app.config.SAFEBROWSING_TOKEN, "bbombsbot", "0.1.1")

    @property
    def app(self) -> BBombsBot:
        """Returns the linked application."""
        return self._app

    @property
    def lists_dir(self) -> str:
        """Returns the path to the lists' directory."""
        return self._lists_dir

    @property
    def safebrowsing_client(self) -> SafebrowsingClient:
        """Returns the safebrowsing API client."""
        return self._safebrowsing_client

    def can_automod(self, member: hikari.Member, bot: hikari.Member) -> bool:
        """Determine if a member should be moderated by automoderator.

        Parameters
        ----------
        member : hikari.Member
            The member to check.
        bot : hikari.Member
            The bot member for the relevant server.

        """
        if not isinstance(member, hikari.Member):
            return False

        if member.is_bot:
            return False

        if member.id in self.app.owner_ids:
            return False

        return can_mod(member, bot)

    async def moderate(
        self,
        message: hikari.PartialMessage,
        offence: AutoModOffenceType,
        media: AutoModMediaType,
        reason: str,
        message_queue: list[hikari.Snowflake] | None = None,
    ) -> None:
        """Carry out the suitable moderation action for the offending message.

        Parameters
        ----------
        message : hikari.PartialMessage
            The offending message.
        offence : AutoModOffenceType
            The type of offence.
        media : AutoModMediaType
            The type of media that caused this offence.
        reason : str
            The reason this message is being moderated.
        message_queue : list[hikari.Snowflake] | None
            Message queue to be deleted for spam offences, optional.

        """
        offender = self.app.cache.get_member(message.guild_id, message.author.id)
        guild = offender.get_guild()
        db_member = await DatabaseMember.fetch(offender.id, offender.guild_id)

        with suppress(hikari.NotFoundError):
            await message.delete()
            if message_queue:
                await self.app.rest.delete_messages(message.channel_id, message_queue)

        if db_member.strikes < 4 and offence == AutoModOffenceType.BLOCKED:
            db_member.strikes += 1
            await db_member.update()
            await self.app.mod.notice(
                offender,
                guild,
                f"""Message removed because it violates a moderation policy: **{reason}**
Continued violation may result in further action.""",
            )
            return

        if db_member.strikes < 4 and offence == AutoModOffenceType.SPAM:
            db_member.strikes += 1
            await db_member.update()

            timeout = 10**db_member.strikes
            duration = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=timeout)

            await self.app.mod.timeout(offender, guild, duration, reason)

            return

    async def find_message_spam(self, message: hikari.PartialMessage) -> bool:
        """Check for common types of spam.

        Returns False if the message is offending otherwise True
        """
        MESSAGE_SPAM_RATELIMITER.add_message(message)
        if MESSAGE_SPAM_RATELIMITER.is_rate_limited(message):
            reason = "sending messages too frequently."
            queue = MESSAGE_SPAM_RATELIMITER.get_messages(message)
            await self.moderate(message, AutoModOffenceType.SPAM, AutoModMediaType.MESSAGE, reason, message_queue=queue)
            return False

        return True

    async def find_duplicate_spam(self, message: hikari.PartialMessage) -> bool:
        """Check for duplicate message spamming.

        Returns False if the message is offending otherwise True
        """
        if not message.content:
            return True

        queue = DUPLICATE_SPAM_RATELIMITER.get_messages(message)

        if queue is None:
            DUPLICATE_SPAM_RATELIMITER.add_message(message)
            return True

        prev_msg = self.app.cache.get_message(queue[-1])

        if prev_msg and distance(prev_msg.content.strip(), message.content.strip()) < 5:  # type: ignore
            DUPLICATE_SPAM_RATELIMITER.add_message(message)

            if DUPLICATE_SPAM_RATELIMITER.is_rate_limited(message):
                queue = DUPLICATE_SPAM_RATELIMITER.get_messages(message)
                reason = "sending consecutive copied and pasted messages."
                await self.moderate(
                    message, AutoModOffenceType.SPAM, AutoModMediaType.DUPLICATE, reason, message_queue=queue
                )
                return False

        return True

    async def find_invite_spam(self, message: hikari.PartialMessage) -> bool:
        """Check for messages with invites being spammed.

        Returns False if the message is offending otherwise True
        """
        if message.content and INVITE_REGEX.findall(message.content.lower()):
            INVITE_SPAM_RATELIMITER.add_message(message)

        if INVITE_SPAM_RATELIMITER.is_rate_limited(message):
            reason = "sending discord invites too frequently."
            queue = INVITE_SPAM_RATELIMITER.get_messages(message)
            await self.moderate(message, AutoModOffenceType.SPAM, AutoModMediaType.INVITE, reason, message_queue=queue)
            return False

        return True

    async def find_link_spam(self, message: hikari.PartialMessage) -> bool:
        """Check for messages with links being spammed.

        Returns False if the message is offending otherwise True
        """
        if message.content and URL_REGEX.findall(message.content.lower()):
            LINK_SPAM_RATELIMITER.add_message(message)

        if LINK_SPAM_RATELIMITER.is_rate_limited(message):
            reason = "sending links too frequently."
            queue = LINK_SPAM_RATELIMITER.get_messages(message)
            await self.moderate(message, AutoModOffenceType.SPAM, AutoModMediaType.LINK, reason, message_queue=queue)
            return False

        return True

    async def find_attach_spam(self, message: hikari.PartialMessage) -> bool:
        """Check for messages with attachments being spammed.

        Returns False if the message is offending otherwise True
        """
        if message.attachments:
            ATTACHMENT_SPAM_RATELIMITER.add_message(message)

        if ATTACHMENT_SPAM_RATELIMITER.is_rate_limited(message):
            reason = "sending attachments too frequently."
            queue = ATTACHMENT_SPAM_RATELIMITER.get_messages(message)
            await self.moderate(
                message, AutoModOffenceType.SPAM, AutoModMediaType.ATTACHMENT, reason, message_queue=queue
            )
            return False

        return True

    async def find_mention_spam(self, message: hikari.PartialMessage) -> bool:
        """Check for messages with mentions being spammed.

        Returns False if the message is offending otherwise True
        """
        assert message.author

        if message.user_mentions:
            for mention in message.user_mentions.values():
                if mention.is_bot or mention.id == message.author.id:
                    return True

            MENTION_SPAM_RATELIMITER.add_message(message)

        if MENTION_SPAM_RATELIMITER.is_rate_limited(message):
            queue = MENTION_SPAM_RATELIMITER.get_messages(message)
            reason = "mentioning users too frequently."
            await self.moderate(message, AutoModOffenceType.SPAM, AutoModMediaType.MENTION, reason, message_queue=queue)
            return False

        return True

    async def block_invites(self, message: hikari.PartialMessage) -> bool:
        """Check for messages with invite links.

        Returns False if the message is offending otherwise True
        """
        if BLOCK_INVITES and message.content and INVITE_REGEX.findall(message.content):
            reason = "invite links are not allowed."
            await self.moderate(message, AutoModOffenceType.BLOCKED, AutoModMediaType.INVITE, reason)
            return False

        return True

    async def block_malicious_links(self, message: hikari.PartialMessage) -> bool:
        """Check to see if a message contains malicious links.

        Returns False if the message is offending otherwise True
        """
        if not message.content or not URL_REGEX.findall(message.content.lower()):
            return True

        reason = "this web resource is not allowed."

        matches = URL_REGEX.findall(message.content.lower())
        refined_matches = []

        whitelist = os.path.join(self.lists_dir, "domain_whitelist.txt")
        blacklist = os.path.join(self.lists_dir, "domain_blacklist.txt")

        for match in matches:
            if not await domain_in_list("".join(match), whitelist):
                refined_matches.append(match)

        if not refined_matches:
            return True

        # Resolve url ...

        for match in refined_matches:
            if await domain_in_list("".join(match), blacklist):
                await self.moderate(message, AutoModOffenceType.BLOCKED, AutoModMediaType.LINK, reason)
                return False

        urls = ["".join(match) for match in refined_matches]

        results = await self.safebrowsing_client.check(urls)

        if any(result.status == "unsafe" for result in results):
            await self.moderate(message, AutoModOffenceType.BLOCKED, AutoModMediaType.LINK, reason)
            return False

        return True

    async def block_fake_links(self, message: hikari.PartialMessage) -> bool:
        """Check for messages with hyperlinks where the hyperlink text is also an url.

        Returns False if the message is offending otherwise True
        """
        if BLOCK_FAKE_URL and message.content and FAKE_URL_REGEX.findall(message.content):
            reason = "hyperlink contains link as text string."
            await self.moderate(message, AutoModOffenceType.BLOCKED, AutoModMediaType.HYPERLINK, reason)
            return False

        return True

    async def limit_mentions(self, message: hikari.PartialMessage) -> bool:
        """Check for messages with lots of mentions of different users.

        Returns False if the message is offending otherwise True
        """
        assert message.author

        if mentions := message.user_mentions:
            count = sum(mention.id != message.author.id and not mention.is_bot for mention in mentions.values())

            if count > MENTION_FILTER_LIMIT:
                reason = "message contains too many consecutive mentions."
                await self.moderate(message, AutoModOffenceType.BLOCKED, AutoModMediaType.MENTION, reason)
                return False

        return True

    async def check(self, event: hikari.GuildMessageUpdateEvent | hikari.GuildMessageCreateEvent) -> None:
        """Run automod checks on created or updated messages.

        Parameters
        ----------
        event : hikari.GuildMessageUpdateEvent | hikari.GuildMessageCreateEvent
            The message event to check for offences.

        """
        message = event.message

        if not message.author:
            return
        if message.guild_id is None:
            return

        member = self.app.cache.get_member(message.guild_id, message.author.id)
        bot = self.app.cache.get_member(message.guild_id, self.app.user_id)

        if bot is None:
            return
        if not member or member.is_bot:
            return

        # if not self.can_automod(member, bot):
        #     return

        if isinstance(event, hikari.GuildMessageCreateEvent):
            all(
                (
                    await self.find_message_spam(message),
                    await self.find_duplicate_spam(message),
                    await self.find_invite_spam(message),
                    await self.find_link_spam(message),
                    await self.find_attach_spam(message),
                    await self.find_mention_spam(message),
                    await self.block_malicious_links(message),
                    await self.block_invites(message),
                    await self.block_fake_links(message),
                    await self.limit_mentions(message),
                )
            )
        elif isinstance(event, hikari.GuildMessageUpdateEvent):
            all(
                (
                    await self.block_malicious_links(message),
                    await self.block_invites(message),
                    await self.block_fake_links(message),
                    await self.limit_mentions(message),
                )
            )


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
