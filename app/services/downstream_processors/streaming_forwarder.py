"""Implements an HTTP-based streaming forwarder processor."""
from typing import Any
import json
import aiohttp

from app.services.downstream_processors.base_processor import BaseProcessor


class StreamingForwarderProcessor(BaseProcessor):
    """
    Processor that forwards messages to an external HTTP endpoint via POST.
    """

    def __init__(self, endpoint_url: str) -> None:
        """
        Initialize the StreamingForwarderProcessor with an endpoint URL.

        :param endpoint_url: The URL of the external service to forward to
        :type endpoint_url: str
        """
        self.endpoint_url = endpoint_url
        self._session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def process(self, message: Any) -> None:
        """
        Forward the Kafka message to the configured endpoint via HTTP POST.

        :param message: The Kafka message
        :type message: Any
        :return: None
        :rtype: None
        """
        content = message.value.decode("utf-8") if hasattr(message.value, "decode") else str(message.value)
        data = json.loads(content)
        async with self._session.post(self.endpoint_url, json=data) as resp:
            if resp.status >= 400:
                # Log or handle error
                print(f"Forwarder failed with status {resp.status}")

    async def close(self) -> None:
        """
        Close the HTTP session.

        :return: None
        :rtype: None
        """
        if not self._session.closed:
            await self._session.close()