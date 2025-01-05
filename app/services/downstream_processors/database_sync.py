"""Implements a database synchronization processor."""
from typing import Any, Optional
import json

from app.services.downstream_processors.base_processor import BaseProcessor


class DatabaseSyncProcessor(BaseProcessor):
    """
    Processor that inserts messages into a database table.
    """

    def __init__(self, db_dsn: str) -> None:
        """
        Initialize the DatabaseSyncProcessor with a database DSN or config.

        :param db_dsn: A database DSN (e.g. postgresql://user:pass@host/db)
        :type db_dsn: str
        """
        self.db_dsn = db_dsn
        self._connection: Optional[Any] = None

    async def process(self, message: Any) -> None:
        """
        Insert the message content into a database.

        :param message: The Kafka message
        :type message: Any
        :return: None
        :rtype: None
        """
        # Example: parse JSON and insert into a table
        data_str = message.value.decode("utf-8")
        data_dict = json.loads(data_str)

        # Pseudocode for DB insert. Actual code would use an async DB driver or session.
        print(f"DatabaseSyncProcessor would insert: {data_dict} into DB: {self.db_dsn}")

    async def close(self) -> None:
        """
        Close any open DB connection.

        :return: None
        :rtype: None
        """
        if self._connection:
            # self._connection.close()
            pass