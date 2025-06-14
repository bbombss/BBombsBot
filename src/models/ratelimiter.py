from __future__ import annotations

import abc
import asyncio
import time
import typing as t
from collections import deque

import attr
import hikari

__all__ = ["MessageRateLimiter"]


class RateLimiterContext(t.Protocol):
    """Some form of context object, for typing purposes."""

    @property
    def author(self) -> hikari.UndefinedOr[hikari.User]: ...

    @property
    def guild_id(self) -> hikari.Snowflake | None: ...


class Request(object):
    """Request object."""

    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self


@attr.define()
class RateLimiter:
    """RateLimiter for a specific requesting entity, i.e. messages from a user."""

    bucket: RateLimiterBucket
    reset_at: float
    remaining_requests: int

    request_queue: t.Deque[Request] = attr.field(factory=deque)
    """List of requests to iterate through until remaining_requests is 0."""
    queue_task: asyncio.Task[t.Any] | None = attr.field(default=None)
    """The Async task that is currently handling the queue."""

    @classmethod
    def get_instance(cls, bucket: RateLimiterBucket) -> RateLimiter:
        """Get a RateLimiter for a Bucket."""
        return cls(
            bucket=bucket,
            reset_at=time.monotonic() + bucket.timespan,
            remaining_requests=bucket.count + 1,
        )

    async def _run_queue(self) -> None:
        """Iterate through and resolve request queue."""
        if self.remaining_requests <= 0 and self.reset_at > time.monotonic():
            await asyncio.sleep(self.reset_at - time.monotonic())
            self.reset()

        elif self.reset_at <= time.monotonic():
            self.reset()

        while self.remaining_requests > 0 and self.request_queue:
            self.remaining_requests -= 1
            self.request_queue.popleft()

        self.queue_task = None

    def start(self) -> None:
        """Start the ratelimiter."""
        if self.queue_task is None:
            self.queue_task = asyncio.create_task(self._run_queue())

    def reset(self) -> None:
        """Reset the ratelimiter."""
        self.reset_at = time.monotonic() + self.bucket.timespan
        self.remaining_requests = self.bucket.count


class RateLimiterBucket(abc.ABC):
    """Abstract class for buckets containing RateLimiters."""

    def __init__(self, timespan: float, count: int):
        """Abstract class for buckets containing RateLimiters.

        Parameters
        ----------
        timespan : float
            The timespan in seconds after which the amount of requests resets.
        count : int
            The number of requests allowed for a timespan before ratelimiting occurs.

        """
        self.timespan: float = timespan
        self.count: int = count

        self._rate_limiters: t.Dict[str, RateLimiter] = {}
        """Dictionary of keys representing a requesting entity and its ratelimiter."""

    @abc.abstractmethod
    def _get_key(self, ctx: RateLimiterContext) -> str:
        """Get key for RateLimiter."""

    def _get_ratelimiter(self, ctx: RateLimiterContext) -> RateLimiter:
        """Get the RateLimiter for this context or create one if there is not one."""
        return self._rate_limiters.setdefault(self._get_key(ctx), RateLimiter.get_instance(self))

    def add(self, ctx: RateLimiterContext) -> None:
        """Add a request to the queue for this context and start the ratelimiter."""
        ratelimiter = self._get_ratelimiter(ctx)
        request = Request()

        ratelimiter.request_queue.append(request)

        ratelimiter.start()

    def reset(self, ctx: RateLimiterContext) -> None:
        """Reset the RateLimiter for this context."""
        rate_limiter = self._get_ratelimiter(ctx)

        if rate_limiter:
            rate_limiter.reset()

    def is_rate_limited(self, ctx: RateLimiterContext) -> bool:
        """Will return True if the provided context is being ratelimited."""
        rate_limiter = self._get_ratelimiter(ctx)

        if rate_limiter and rate_limiter.reset_at <= time.monotonic():
            return False
        elif rate_limiter and rate_limiter.remaining_requests <= 0:
            return True
        return False


class MessageRateLimiter(RateLimiterBucket):
    """Ratelimiter for messages per member."""

    def __init__(self, timespan: float, count: int, message_queue_size: int = 0) -> None:
        """Ratelimiter for messages per member.

        Parameters
        ----------
        timespan : float
            The timespan in seconds after which the amount of requests resets.
        count : int
            The number of requests allowed for a timespan before ratelimiting occurs.
        message_queue_size : int
            The number of message snowflakes sent by this context's member to store.
            Defaults to 0 meaning no previous message snowflakes are stored.

        """
        self.message_queue_size: int = message_queue_size

        self._message_queue: dict[str, t.Deque[hikari.Snowflake]] = {}
        """Dict of keys representing members and a list of their last few messages."""

        super().__init__(timespan, count)

    def _get_key(self, ctx: hikari.PartialMessage) -> str:
        if not ctx.author or not ctx.guild_id:
            raise ValueError("context missing required parameters")

        return str(ctx.guild_id) + "-" + str(ctx.author.id)

    def add_message(self, ctx: hikari.PartialMessage) -> None:
        """Add a message to this context's queue and start the ratelimiter."""
        self.add(ctx)
        if self.message_queue_size > 0:
            queue = self._message_queue.setdefault(self._get_key(ctx), deque(maxlen=self.message_queue_size))
            queue.append(ctx.id)

    def get_messages(self, ctx: hikari.PartialMessage) -> list[hikari.Snowflake] | None:
        """Get the message queue for this context.

        Returns
        -------
        list[hikari.Snowflakes] | None
            A list of snowflakes for messages sent by this member or
            none if this context has no message queue.

        """
        try:
            return list(self._message_queue[self._get_key(ctx)])
        except KeyError:
            return


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
