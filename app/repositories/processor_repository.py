"""Repository for handling operations on the `downstream_processors` table."""
from typing import List

from app.db.session import async_session
from app.models.downstream_processor import DownstreamProcessor
from app.api.schemas.consumer_requests import ProcessorConfig


class ProcessorRepository:
    """
    Handles DB interactions for DownstreamProcessor records.
    """

    @staticmethod
    async def create(consumer_id: str, config: ProcessorConfig) -> DownstreamProcessor:
        """
        Create a new downstream processor record associated with a consumer.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :param config: The processor config
        :type config: ProcessorConfig
        :return: The newly created DownstreamProcessor object
        :rtype: DownstreamProcessor
        """
        async with async_session() as session:
            record = DownstreamProcessor(
                consumer_id=consumer_id,
                processor_type=config.processor_type,
                config=config.config
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    @staticmethod
    async def get_by_consumer_id(consumer_id: str) -> List[DownstreamProcessor]:
        """
        Retrieve all downstream processors for a given consumer.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: A list of DownstreamProcessor records
        :rtype: List[DownstreamProcessor]
        """
        async with async_session() as session:
            results = await session.execute(
                """
                SELECT * FROM downstream_processors
                WHERE consumer_id = :cid
                """,
                {"cid": consumer_id}
            )
            # For async usage with 2.0+ engines, you might need different patterns:
            rows = results.fetchall()
            return [row._mapping for row in rows]  # or an ORM approach

    @staticmethod
    async def delete_by_consumer_id(consumer_id: str) -> None:
        """
        Delete all processor records associated with a consumer.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: None
        :rtype: None
        """
        async with async_session() as session:
            await session.execute(
                """
                DELETE FROM downstream_processors
                WHERE consumer_id = :cid
                """,
                {"cid": consumer_id}
            )
            await session.commit()