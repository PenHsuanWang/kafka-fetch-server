"""Implements a file-based downstream processor using aiofiles."""
import aiofiles
from typing import Any

from app.services.downstream_processors.base_processor import BaseProcessor


class FileSinkProcessor(BaseProcessor):
    """
    Processor that writes incoming Kafka messages to a file (line by line).
    """

    def __init__(self, file_path: str) -> None:
        """
        Initialize the FileSinkProcessor with a file path.

        :param file_path: The path to the output file
        :type file_path: str
        """
        self.file_path = file_path

    async def process(self, message: Any) -> None:
        """
        Append the message's payload to the file.

        :param message: The Kafka message
        :type message: Any
        :return: None
        :rtype: None
        """
        content = message.value.decode("utf-8") if hasattr(message.value, "decode") else str(message.value)
        async with aiofiles.open(self.file_path, "a") as f:
            await f.write(content + "\n")