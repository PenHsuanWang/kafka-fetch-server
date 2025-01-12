"""
Kafka Consumer Serving Manager
=============================

Singleton manager that handles all operations on Kafka consumers:
create, status, health, start, stop, update, delete.

It maintains:
  - consumer_data: dict of consumer metadata (topic, group, status, etc.)
  - consumer_store: dict of actual consumer objects or 'MessageExtractor' instances
  - processor_data: dict of each consumer's downstream processor configs

:module: kafka_consumer_serving_manager
:author: Your Name
:created: 2025-01-01
:seealso: app.services.message_extractor
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional

from app.api.v1.schemas.consumer_requests import (
    ConsumerCreateRequest,
    ConsumerUpdateRequest
)
from app.services.downstream_processors.processor_factory import ProcessorFactory
from app.services.downstream_processors.base_processor import BaseProcessor
# IMPORTANT: Import the MessageExtractor class here.
from app.services.message_extractor import MessageExtractor


class KafkaConsumerServingManager:
    """
    A Singleton manager that coordinates in-memory Kafka consumers.

    **Fields**:
      - consumer_data: A mapping from consumer_id to metadata about the consumer
      - consumer_store: A mapping from consumer_id to the MessageExtractor instance
      - processor_data: A mapping from consumer_id to a list of downstream processor definitions
      - operation_journal: A log of (operation_type, consumer_id) tuples
    """

    _instance = None
    _lock = asyncio.Lock()

    def __init__(self):
        """
        Constructor is called once when the Singleton instance is created.
        It initializes the data structures that hold consumer information.
        """
        self.consumer_data: Dict[str, Dict[str, Any]] = {}
        self.consumer_store: Dict[str, Any] = {}
        self.processor_data: Dict[str, List[Dict[str, Any]]] = {}
        self.operation_journal: List[tuple] = []

    @classmethod
    def get_instance(cls) -> "KafkaConsumerServingManager":
        """
        Return the global singleton instance of KafkaConsumerServingManager.

        :return: The singleton instance of this class
        :rtype: KafkaConsumerServingManager
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ----------------------------------------------------------------
    # CRUD-Like Methods
    # ----------------------------------------------------------------

    async def create_consumer(self, payload: ConsumerCreateRequest) -> Dict[str, Any]:
        """
        Create a new consumer from the given request payload.

        :param payload: The ConsumerCreateRequest containing broker IP/port, topic, group, etc.
        :type payload: ConsumerCreateRequest
        :return: A dictionary describing the newly created consumer (as a response)
        :rtype: Dict[str, Any]
        """
        consumer_id = str(uuid.uuid4())

        self.consumer_data[consumer_id] = {
            "consumer_id": consumer_id,
            "broker_ip": payload.broker_ip,
            "broker_port": payload.broker_port,
            "topic": payload.topic,
            "consumer_group": payload.consumer_group,
            "status": "INACTIVE",
            "created_at": None,
            "updated_at": None
        }

        # Build downstream processors from the config
        proc_list = []
        for proc_cfg in payload.processor_configs:
            proc_dict = {
                "id": str(uuid.uuid4()),
                "processor_type": proc_cfg.processor_type,
                "config": proc_cfg.config,
                "created_at": None,
                "updated_at": None
            }
            proc_list.append(proc_dict)
        self.processor_data[consumer_id] = proc_list

        # Create the MessageExtractor (which references the downstream processors)
        extractor = await self._build_extractor(consumer_id)
        self.consumer_store[consumer_id] = extractor

        # If auto_start is True, start the consumer now
        if payload.auto_start:
            await extractor.start()
            self.consumer_data[consumer_id]["status"] = "ACTIVE"

        # Record this create operation in the journal
        self.operation_journal.append(("CREATE", consumer_id))

        return await self._map_consumer_to_response(consumer_id)

    async def get_consumer_record(self, consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the dictionary representing the specified consumer.

        :param consumer_id: The unique identifier (UUID) for the consumer
        :type consumer_id: str
        :return: The consumer data dict if found, else None
        :rtype: Optional[Dict[str, Any]]
        """
        if consumer_id not in self.consumer_data:
            return None
        return await self._map_consumer_to_response(consumer_id)

    async def list_consumers(self) -> List[Dict[str, Any]]:
        """
        List all registered consumers in memory.

        :return: A list of consumer records as dictionaries
        :rtype: List[Dict[str, Any]]
        """
        results = []
        for cid in self.consumer_data:
            rec = await self._map_consumer_to_response(cid)
            results.append(rec)
        return results

    async def update_consumer(self, consumer_id: str, payload: ConsumerUpdateRequest) -> Optional[Dict[str, Any]]:
        """
        Update an existing consumer's broker info, topic, or processor configurations.

        :param consumer_id: The UUID of the consumer to update
        :type consumer_id: str
        :param payload: Fields to update
        :type payload: ConsumerUpdateRequest
        :return: Updated consumer details or None if consumer not found
        :rtype: Optional[Dict[str, Any]]
        """
        if consumer_id not in self.consumer_data:
            return None

        cdata = self.consumer_data[consumer_id]
        if payload.broker_ip is not None:
            cdata["broker_ip"] = payload.broker_ip
        if payload.broker_port is not None:
            cdata["broker_port"] = payload.broker_port
        if payload.topic is not None:
            cdata["topic"] = payload.topic

        # If processor configs are updated, rebuild the stored list & re-init the consumer if needed
        if payload.processor_configs is not None:
            new_proc_list = []
            for pcfg in payload.processor_configs:
                proc_dict = {
                    "id": str(uuid.uuid4()),
                    "processor_type": pcfg.processor_type,
                    "config": pcfg.config,
                    "created_at": None,
                    "updated_at": None
                }
                new_proc_list.append(proc_dict)
            self.processor_data[consumer_id] = new_proc_list

            old_extractor = self.consumer_store.get(consumer_id)
            if old_extractor:
                await old_extractor.stop()
                new_extractor = await self._build_extractor(consumer_id)
                self.consumer_store[consumer_id] = new_extractor
                if cdata["status"] == "ACTIVE":
                    await new_extractor.start()

        self.operation_journal.append(("UPDATE", consumer_id))
        return await self._map_consumer_to_response(consumer_id)

    async def delete_consumer(self, consumer_id: str) -> bool:
        """
        Delete an existing consumer from memory. If active, it will be stopped first.

        :param consumer_id: The UUID of the consumer to delete
        :type consumer_id: str
        :return: True if the consumer was found and deleted, False otherwise
        :rtype: bool
        """
        if consumer_id not in self.consumer_data:
            return False

        extractor = self.consumer_store.get(consumer_id)
        if extractor:
            await extractor.stop()

        self.consumer_data.pop(consumer_id, None)
        self.consumer_store.pop(consumer_id, None)
        self.processor_data.pop(consumer_id, None)

        self.operation_journal.append(("DELETE", consumer_id))
        return True

    # ----------------------------------------------------------------
    # Lifecycle Management
    # ----------------------------------------------------------------

    async def start_consumer(self, consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Start a consumer by ID. If it doesn't exist or is already started, handle accordingly.

        :param consumer_id: The UUID of the consumer to start
        :type consumer_id: str
        :return: The updated consumer record, or None if not found
        :rtype: Optional[Dict[str, Any]]
        """
        if consumer_id not in self.consumer_data:
            return None

        extractor = self.consumer_store.get(consumer_id)
        if not extractor:
            extractor = await self._build_extractor(consumer_id)
            self.consumer_store[consumer_id] = extractor

        await extractor.start()
        self.consumer_data[consumer_id]["status"] = "ACTIVE"
        self.operation_journal.append(("UPDATE", consumer_id))
        return await self._map_consumer_to_response(consumer_id)

    async def stop_consumer(self, consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Stop a consumer by ID if it is currently active.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: The updated consumer record or None if not found
        :rtype: Optional[Dict[str, Any]]
        """
        if consumer_id not in self.consumer_data:
            return None

        extractor = self.consumer_store.get(consumer_id)
        if extractor:
            await extractor.stop()

        self.consumer_data[consumer_id]["status"] = "INACTIVE"
        self.operation_journal.append(("UPDATE", consumer_id))
        return await self._map_consumer_to_response(consumer_id)

    # ----------------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------------

    async def _build_extractor(self, consumer_id: str):
        """
        Construct and return a `MessageExtractor` instance for the given consumer_id.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: A MessageExtractor or None if the consumer_id is invalid
        :rtype: Optional[MessageExtractor]
        """
        if consumer_id not in self.consumer_data:
            return None

        cdata = self.consumer_data[consumer_id]
        proc_list = self.processor_data.get(consumer_id, [])

        processors: List[BaseProcessor] = []
        for p in proc_list:
            proc = await ProcessorFactory.create_processor(
                processor_type=p["processor_type"],
                config=p["config"]
            )
            processors.append(proc)

        # This is the class that actually interacts with Kafka
        # and applies the downstream processors to each message.
        extractor = MessageExtractor(
            broker=f"{cdata['broker_ip']}:{cdata['broker_port']}",
            topic=cdata["topic"],
            group_id=cdata["consumer_group"],
            processors=processors,
            client_id=consumer_id
        )
        return extractor

    async def _map_consumer_to_response(self, consumer_id: str) -> Dict[str, Any]:
        """
        Convert a consumer's in-memory record into a dictionary
        suitable for returning from an API endpoint.

        :param consumer_id: The UUID of the consumer
        :type consumer_id: str
        :return: A dictionary describing the consumer and its processors.
        :rtype: Dict[str, Any]
        """
        cdata = self.consumer_data.get(consumer_id)
        if not cdata:
            return {}

        proc_list = self.processor_data.get(consumer_id, [])

        return {
            "consumer_id": cdata["consumer_id"],
            "broker_ip": cdata["broker_ip"],
            "broker_port": cdata["broker_port"],
            "topic": cdata["topic"],
            "consumer_group": cdata["consumer_group"],
            "status": cdata["status"],
            "processors": proc_list,
            "created_at": cdata["created_at"],
            "updated_at": cdata["updated_at"]
        }
