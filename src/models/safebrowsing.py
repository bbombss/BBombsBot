import asyncio
import json
import logging
import typing as t

import aiohttp

logger = logging.getLogger(__name__)

LOOKUP_API_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find?key={key}"


class SafeBrowsingResult:
    """Safebrowsing api result object."""

    def __init__(
        self,
        url: str,
        status: str,
        type: str | None = None,
        cache_duration: float | None = None,
    ) -> None:
        """Safebrowsing api result object.

        Parameters
        ----------
        url : str
            The requested url.
        status : str
            Status of requested url, safe or unsafe.
        type : str | None
            Type threat the url poses, defaults to None.
        cache_duration : float | None
            The amount of time the url must be considered unsafe, defaults to None.

        """
        self.url: str = url
        self.status: str = status
        self.type: str | None = type
        self.cache_duration: float | None = cache_duration


class SafeBrowsingCache:
    """Safebrowsing results cache."""

    def __init__(self):
        self._cache = {}

    def get(self, url: str) -> SafeBrowsingResult | None:
        return self._cache.get(url)

    def set(self, url: str, result: SafeBrowsingResult) -> None:
        self._cache[url] = result


# Missing ratelimiter for failed requests
class SafebrowsingClient:
    """Safebrowsing client to interface with Google safebrowsing lookup api."""

    def __init__(self, api_key: str, client_id: str, client_version: str) -> None:
        """Safebrowsing client to interface with Google safebrowsing lookup api.

        Parameters
        ----------
        api_key : str
            The api key.
        client_id : str
            Client ID used to identify the requesting entity.
        client_version : str
            Client version used to identify the requesting entity.

        """
        self.api_key = api_key
        self.client_id = client_id
        self.client_version = client_version

        self._session: aiohttp.ClientSession = aiohttp.ClientSession()
        self._cache: SafeBrowsingCache = SafeBrowsingCache()
        self._queue: asyncio.Queue = asyncio.Queue()
        self._batch_size: int = 5
        self._event = asyncio.Event()

        # Start a background task to process URLs in batches
        self._task: asyncio.Task[t.Any] = asyncio.create_task(self._run_queue())

    async def check(self, urls: list[str]) -> list[SafeBrowsingResult]:
        """Check if any provided urls are on a safebrowsing list.

        Parameters
        ----------
        urls : list[str]
            List of urls to be queued and sent to the api.

        Returns
        -------
        results : list[SafeBrowsingResult]
            List of result objects for each requested url.

        """
        for url in urls:
            if self._cache.get(url) is None:
                await self._queue.put(url)

        # Make sure all urls have results
        while any(self._cache.get(url) is None for url in urls):
            # Wait for cache update
            await self._event.wait()

        return [self._cache.get(url) for url in urls]  # type: ignore

    async def close(self) -> None:
        """Stop the queue task and close the aiohttp client session."""
        self._task.cancel()
        await self._session.close()

    async def _run_queue(self) -> None:
        while True:
            urls = [await self._queue.get()]

            # Get as many pending urls from queue as possible
            while len(urls) < self._batch_size and not self._queue.empty():
                urls.append(self._queue.get_nowait())

            results = await self._lookup_urls(urls)

            for result in results.values():
                self._cache.set(result.url, result)
                self._event.set()
                self._event.clear()

    async def _lookup_urls(self, urls: list[str]) -> dict[str, SafeBrowsingResult]:
        response = await self._request_api(urls)

        results = {}

        for url in urls:
            for match in response["matches"]:
                if url == match["threat"]["url"]:
                    results[url] = SafeBrowsingResult(
                        url,
                        "unsafe",
                        match["threatType"],
                        float(match["cacheDuration"].strip("s")),
                    )

            if not results[url]:
                results[url] = SafeBrowsingResult(url, "safe")

        return results

    async def _request_api(self, urls: list[str]) -> dict[str, t.Any]:
        threatEntries = [{"url": url} for url in urls]

        request_body = {
            "client": {"clientId": self.client_id, "clientVersion": self.client_version},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": threatEntries,
            },
        }

        async with self._session.request(
            "POST", LOOKUP_API_URL.format(key=self.api_key), json=request_body
        ) as resp:
            if resp.status == 200:
                response = await resp.json()
                return response

            else:
                logger.error(
                    f"""Failed Safebrowing Lookup request:
{resp.status}
{json.dumps(await resp.json(), indent=3)}"""
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
