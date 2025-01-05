"""Business logic layer for Kafka consumers."""
from typing import Dict, Any, Optional

from app.services.kafka_consumer_manager import KafkaConsumerManager
from app.api.schemas.consumer_requests import ConsumerCreateRequest, ConsumerUpdateRequest


class ConsumerService:
    """
    ConsumerService orchestrates the creation, update, start, stop,
    and deletion of Kafka consumers.
    """

    @staticmethod
    async def create_consumer(payload: ConsumerCreateRequest) -> Dict[str, Any]:
        """
        Create a new consumer with the given payload.

        :param payload: The consumer creation request
        :type payload: ConsumerCreateRequest
        :return: A dictionary representing the newly created consumer
        :rtype: Dict[str, Any]
        """
        manager = KafkaConsumerManager()
        return await manager.create_consumer(payload)

    @staticmethod
    async def get_consumer(consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve consumer details by ID.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: Consumer details dict if found, else None
        :rtype: Optional[Dict[str, Any]]
        """
        manager = KafkaConsumerManager()
        return await manager.get_consumer_record(consumer_id)

    @staticmethod
    async def start_consumer(consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Start a stopped consumer.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: Updated consumer dict if found, else None
        :rtype: Optional[Dict[str, Any]]
        """
        manager = KafkaConsumerManager()
        return await manager.start_consumer(consumer_id)

    @staticmethod
    async def stop_consumer(consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Stop an active consumer.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: Updated consumer dict if found, else None
        :rtype: Optional[Dict[str, Any]]
        """
        manager = KafkaConsumerManager()
        return await manager.stop_consumer(consumer_id)

    @staticmethod
    async def update_consumer(consumer_id: str, payload: ConsumerUpdateRequest) -> Optional[Dict[str, Any]]:
        """
        Update an existing consumer's properties or processor configs.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :param payload: The update payload
        :type payload: ConsumerUpdateRequest
        :return: Updated consumer dict if found, else None
        :rtype: Optional[Dict[str, Any]]
        """
        manager = KafkaConsumerManager()
        return await manager.update_consumer(consumer_id, payload)

    @staticmethod
    async def delete_consumer(consumer_id: str) -> bool:
        """
        Delete a consumer by its ID.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: True if successfully deleted, False otherwise
        :rtype: bool
        """
        manager = KafkaConsumerManager()
        return await manager.delete_consumer(consumer_id)