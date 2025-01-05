"""Factory class for creating downstream processor instances."""
from typing import Any

from app.services.downstream_processors.base_processor import BaseProcessor
from app.services.downstream_processors.file_sink import FileSinkProcessor
from app.services.downstream_processors.database_sync import DatabaseSyncProcessor
from app.services.downstream_processors.streaming_forwarder import StreamingForwarderProcessor


class ProcessorFactory:
    """
    A factory to create processor instances based on type and config.
    """

    @staticmethod
    async def create_processor(processor_type: str, config: dict) -> BaseProcessor:
        """
        Create a processor instance given a type and configuration.

        :param processor_type: The processor type (e.g. 'file_sink')
        :type processor_type: str
        :param config: A dictionary of config parameters
        :type config: dict
        :return: A specialized processor instance
        :rtype: BaseProcessor
        :raises ValueError: If the processor_type is unknown
        """
        if processor_type == "file_sink":
            file_path = config["file_path"]
            return FileSinkProcessor(file_path)
        elif processor_type == "database_sync":
            db_dsn = config["db_dsn"]
            return DatabaseSyncProcessor(db_dsn)
        elif processor_type == "streaming_forwarder":
            endpoint_url = config["endpoint_url"]
            return StreamingForwarderProcessor(endpoint_url)
        else:
            raise ValueError(f"Unknown processor type: {processor_type}")