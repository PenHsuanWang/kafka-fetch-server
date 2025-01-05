"""Singleton manager that coordinates all active Kafka consumers and stores them in memory."""

import asyncio
from typing import Dict, Any, Optional

from app.api.schemas.consumer_requests import ConsumerCreateRequest, ConsumerUpdateRequest
from app.repositories.consumer_repository import ConsumerRepository
from app.repositories.processor_repository import ProcessorRepository
from app.services.message_extractor import MessageExtractor
from app.services.downstream_processors.processor_factory import ProcessorFactory


class KafkaConsumerManager:
    """
    A Singleton class that manages the lifecycle of Kafka consumers.
    Maintains an in-memory store (consumer_store) mapping consumer_id to MessageExtractor.
    """

    _instance = None
    consumer_store: Dict[str, MessageExtractor] = {}
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        """
        Implements the Singleton pattern: only one instance per process.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def create_consumer(self, payload: ConsumerCreateRequest) -> Dict[str, Any]:
        """
        Create a new consumer record in the DB, build the MessageExtractor, and optionally start it.

        :param payload: The consumer creation payload
        :type payload: ConsumerCreateRequest
        :return: A dictionary representing the newly created consumer
        :rtype: Dict[str, Any]
        """
        consumer_record = await ConsumerRepository.create(payload)

        # Insert processor configs
        for proc_cfg in payload.processor_configs:
            await ProcessorRepository.create(consumer_id=str(consumer_record.id), config=proc_cfg)

        # Build the MessageExtractor
        extractor = await self._build_extractor(consumer_record.id)
        self.consumer_store[str(consumer_record.id)] = extractor

        # Auto-start if requested
        if payload.auto_start:
            await extractor.start()
            await ConsumerRepository.update_status(str(consumer_record.id), "ACTIVE")

        return await self._map_consumer_record_to_response(consumer_record.id)

    async def get_consumer_record(self, consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the consumer record (including processors) from the DB.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: A dictionary of consumer details if found, else None
        :rtype: Optional[Dict[str, Any]]
        """
        record = await ConsumerRepository.get_by_id(consumer_id)
        if not record:
            return None
        return await self._map_consumer_record_to_response(consumer_id)

    async def start_consumer(self, consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Start a consumer if it's in the store and inactive.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: Updated consumer details if found, else None
        :rtype: Optional[Dict[str, Any]]
        """
        extractor = self.consumer_store.get(consumer_id)
        if not extractor:
            # Possibly consumer not loaded in memory
            # Attempt to build it from DB
            new_extractor = await self._build_extractor(consumer_id)
            if not new_extractor:
                return None
            self.consumer_store[consumer_id] = new_extractor
            extractor = new_extractor

        await extractor.start()
        await ConsumerRepository.update_status(consumer_id, "ACTIVE")
        return await self._map_consumer_record_to_response(consumer_id)

    async def stop_consumer(self, consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Stop a consumer if it's active.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: Updated consumer details if found, else None
        :rtype: Optional[Dict[str, Any]]
        """
        extractor = self.consumer_store.get(consumer_id)
        if not extractor:
            return None
        await extractor.stop()
        await ConsumerRepository.update_status(consumer_id, "INACTIVE")
        return await self._map_consumer_record_to_response(consumer_id)

    async def update_consumer(self, consumer_id: str, payload: ConsumerUpdateRequest) -> Optional[Dict[str, Any]]:
        """
        Update an existing consumer record and rebuild the extractor if necessary.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :param payload: The update payload
        :type payload: ConsumerUpdateRequest
        :return: Updated consumer details if found, else None
        :rtype: Optional[Dict[str, Any]]
        """
        updated_record = await ConsumerRepository.update(consumer_id, payload)
        if not updated_record:
            return None

        # Recreate processor configs if provided
        if payload.processor_configs is not None:
            await ProcessorRepository.delete_by_consumer_id(consumer_id)
            for proc_cfg in payload.processor_configs:
                await ProcessorRepository.create(consumer_id, proc_cfg)

        # If the consumer is in memory, stop and rebuild
        if consumer_id in self.consumer_store:
            old_extractor = self.consumer_store[consumer_id]
            await old_extractor.stop()
            new_extractor = await self._build_extractor(consumer_id)
            self.consumer_store[consumer_id] = new_extractor

        return await self._map_consumer_record_to_response(consumer_id)

    async def delete_consumer(self, consumer_id: str) -> bool:
        """
        Delete a consumer from the store and DB.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: True if the consumer was found and deleted, otherwise False
        :rtype: bool
        """
        # Stop if active
        if consumer_id in self.consumer_store:
            extractor = self.consumer_store[consumer_id]
            await extractor.stop()
            del self.consumer_store[consumer_id]

        success = await ConsumerRepository.delete(consumer_id)
        if not success:
            return False
        await ProcessorRepository.delete_by_consumer_id(consumer_id)
        return True

    async def _build_extractor(self, consumer_id: str) -> Optional[MessageExtractor]:
        """
        Build a MessageExtractor from a consumer record and its processors.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: A newly created MessageExtractor if record exists, else None
        :rtype: Optional[MessageExtractor]
        """
        record = await ConsumerRepository.get_by_id(consumer_id)
        if not record:
            return None

        processor_records = await ProcessorRepository.get_by_consumer_id(consumer_id)
        processors = []
        for p_rec in processor_records:
            processor = await ProcessorFactory.create_processor(p_rec.processor_type, p_rec.config)
            processors.append(processor)

        extractor = MessageExtractor(
            broker=f"{record.broker_ip}:{record.broker_port}",
            topic=record.topic,
            group_id=record.consumer_group,
            processors=processors,
            client_id=str(record.id)
        )
        return extractor

    async def _map_consumer_record_to_response(self, consumer_id: str) -> Dict[str, Any]:
        """
        Build a dictionary describing the consumer + processors for API responses.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: A dictionary representing the consumer and its processors
        :rtype: Dict[str, Any]
        """
        rec = await ConsumerRepository.get_by_id(consumer_id)
        if not rec:
            return {}

        proc_recs = await ProcessorRepository.get_by_consumer_id(consumer_id)
        processor_list = []
        for p in proc_recs:
            processor_list.append({
                "id": str(p.id),
                "processor_type": p.processor_type,
                "config": p.config,
                "created_at": p.created_at,
                "updated_at": p.updated_at
            })

        return {
            "consumer_id": str(rec.id),
            "broker_ip": rec.broker_ip,
            "broker_port": rec.broker_port,
            "topic": rec.topic,
            "consumer_group": rec.consumer_group,
            "status": rec.status,
            "processor_configs": processor_list,
            "created_at": rec.created_at,
            "updated_at": rec.updated_at
        }