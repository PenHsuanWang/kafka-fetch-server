"""Repository for handling operations on the `consumers` table."""
from typing import Any, Optional

from app.db.session import async_session
from app.models.consumer import Consumer
from app.api.schemas.consumer_requests import ConsumerCreateRequest, ConsumerUpdateRequest


class ConsumerRepository:
    """
    Handles DB interactions for Consumer records.
    """

    @staticmethod
    async def create(payload: ConsumerCreateRequest) -> Consumer:
        """
        Create a new consumer record in the database.

        :param payload: The creation payload
        :type payload: ConsumerCreateRequest
        :return: The newly created Consumer ORM object
        :rtype: Consumer
        """
        async with async_session() as session:
            consumer = Consumer(
                broker_ip=payload.broker_ip,
                broker_port=payload.broker_port,
                topic=payload.topic,
                consumer_group=payload.consumer_group,
                status="INACTIVE"
            )
            session.add(consumer)
            await session.commit()
            await session.refresh(consumer)
            return consumer

    @staticmethod
    async def get_by_id(consumer_id: str) -> Optional[Consumer]:
        """
        Retrieve a consumer by its ID.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: The Consumer object if found, else None
        :rtype: Optional[Consumer]
        """
        async with async_session() as session:
            return await session.get(Consumer, consumer_id)

    @staticmethod
    async def update(consumer_id: str, payload: ConsumerUpdateRequest) -> Optional[Consumer]:
        """
        Update fields of an existing consumer record.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :param payload: Fields to update
        :type payload: ConsumerUpdateRequest
        :return: The updated Consumer object if found, else None
        :rtype: Optional[Consumer]
        """
        async with async_session() as session:
            consumer = await session.get(Consumer, consumer_id)
            if not consumer:
                return None
            if payload.broker_ip is not None:
                consumer.broker_ip = payload.broker_ip
            if payload.broker_port is not None:
                consumer.broker_port = payload.broker_port
            if payload.topic is not None:
                consumer.topic = payload.topic
            # We do not directly change status here, only upon start/stop operations
            await session.commit()
            await session.refresh(consumer)
            return consumer

    @staticmethod
    async def update_status(consumer_id: str, status: str) -> None:
        """
        Update the status of a consumer (ACTIVE, INACTIVE, ERROR).

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :param status: The new status
        :type status: str
        :return: None
        :rtype: None
        """
        async with async_session() as session:
            consumer = await session.get(Consumer, consumer_id)
            if consumer:
                consumer.status = status
                await session.commit()

    @staticmethod
    async def delete(consumer_id: str) -> bool:
        """
        Delete a consumer by ID.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: True if deleted, False if not found
        :rtype: bool
        """
        async with async_session() as session:
            consumer = await session.get(Consumer, consumer_id)
            if not consumer:
                return False
            await session.delete(consumer)
            await session.commit()
            return True