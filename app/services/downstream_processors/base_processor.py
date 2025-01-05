"""Defines the BaseProcessor interface for all downstream processors."""

from abc import ABC, abstractmethod
from typing import Any


class BaseProcessor(ABC):
    """
    Abstract base class for downstream processors.
    Each processor must implement `process(message)`.
    """

    @abstractmethod
    async def process(self, message: Any) -> None:
        """
        Process a single Kafka message.

        :param message: The Kafka message
        :type message: Any
        :return: None
        :rtype: None
        """
        raise NotImplementedError

    async def close(self) -> None:
        """
        Close any open resources (e.g., file handles, HTTP sessions, DB connections).

        :return: None
        :rtype: None
        """
        pass