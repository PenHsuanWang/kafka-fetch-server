"""
Singleton manager that stores all Kafka consumers in memory and supports future DB syncing.

This manager is designed to handle all in-memory interactions for Kafka consumers, such as
creation, update, deletion, and start/stop actions. It also provides a mechanism for recording
operations in a journal for future asynchronous persistence in a database.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List

from app.api.v1.schemas.consumer_requests import (
    ConsumerCreateRequest,
    ConsumerUpdateRequest,
    ProcessorConfig,
)
from app.services.message_extractor import MessageExtractor
from app.services.downstream_processors.processor_factory import ProcessorFactory

#: Constant representing a 'create' operation.
OP_CREATE = "CREATE"
#: Constant representing an 'update' operation.
OP_UPDATE = "UPDATE"
#: Constant representing a 'delete' operation.
OP_DELETE = "DELETE"


class KafkaConsumerManager:
    """
    A Singleton class that manages the lifecycle of Kafka consumers in memory,
    while providing a framework for asynchronous persistence to a database.

    **Key In-Memory Structures**:

    - ``consumer_store``: A mapping of ``consumer_id`` to a :class:`MessageExtractor`.
      This holds active consumer objects that are actually polling Kafka.
    - ``consumer_data``: A dict of ``consumer_id -> dict`` storing metadata for each consumer
      (e.g., broker IP, port, topic, group, status).
    - ``processor_data``: A dict of ``consumer_id -> list of processor dicts`` describing how
      messages are handled downstream.
    - ``operation_journal``: A list of (op_type, consumer_id) pairs used to track create/update/delete
      operations for asynchronous DB syncing.
    - ``sync_in_progress``: A boolean flag used to ensure only one sync_with_db operation runs at a time.
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        """
        Implements the Singleton pattern so only one instance exists in a given process.

        :return: The singleton instance of KafkaConsumerManager.
        :rtype: KafkaConsumerManager
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize in-memory structures in the singleton instance.
            cls._instance.consumer_store: Dict[str, MessageExtractor] = {}
            cls._instance.consumer_data: Dict[str, Dict[str, Any]] = {}
            cls._instance.processor_data: Dict[str, List[Dict[str, Any]]] = {}
            cls._instance.operation_journal: List[tuple] = []
            cls._instance.sync_in_progress: bool = False
        return cls._instance

    async def create_consumer(self, payload: ConsumerCreateRequest) -> Dict[str, Any]:
        """
        Create a new consumer in memory, build the :class:`MessageExtractor`, and optionally start it.
        A "CREATE" operation is added to the operation journal for future DB syncing.

        :param payload: The consumer creation request, containing broker info, topic, group, etc.
        :type payload: ConsumerCreateRequest
        :return: A dictionary describing the newly created consumer, including its status and processors.
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

        extractor = await self._build_extractor(consumer_id)
        self.consumer_store[consumer_id] = extractor

        if payload.auto_start:
            await extractor.start()
            self.consumer_data[consumer_id]["status"] = "ACTIVE"

        self._record_operation(OP_CREATE, consumer_id)
        return await self._map_consumer_record_to_response(consumer_id)

    async def get_consumer_record(self, consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the in-memory record for a consumer by its ID.

        :param consumer_id: The UUID of the consumer to fetch.
        :type consumer_id: str
        :return: The consumer's metadata and processors if found, otherwise None.
        :rtype: Optional[Dict[str, Any]]
        """
        if consumer_id not in self.consumer_data:
            return None
        return await self._map_consumer_record_to_response(consumer_id)

    async def list_consumers(self) -> List[Dict[str, Any]]:
        """
        Return a list of dictionaries describing each in-memory consumer.
        Used by the /consumers/ GET endpoint.
        """
        all_consumers = []
        for cid in self.consumer_data.keys():
            c_record = await self._map_consumer_record_to_response(cid)
            if c_record:
                all_consumers.append(c_record)
        return all_consumers

    async def start_consumer(self, consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Start a consumer if it exists in memory. If the corresponding :class:`MessageExtractor`
        does not exist yet, it is built.

        :param consumer_id: The UUID of the consumer to start.
        :type consumer_id: str
        :return: The updated consumer record, or None if the consumer does not exist.
        :rtype: Optional[Dict[str, Any]]
        """
        if consumer_id not in self.consumer_data:
            return None

        extractor = self.consumer_store.get(consumer_id)
        if not extractor:
            extractor = await self._build_extractor(consumer_id)
            if not extractor:
                return None
            self.consumer_store[consumer_id] = extractor

        await extractor.start()
        self.consumer_data[consumer_id]["status"] = "ACTIVE"

        self._record_operation(OP_UPDATE, consumer_id)
        return await self._map_consumer_record_to_response(consumer_id)

    async def stop_consumer(self, consumer_id: str) -> Optional[Dict[str, Any]]:
        """
        Stop an active consumer if it exists in memory.

        :param consumer_id: The UUID of the consumer to stop.
        :type consumer_id: str
        :return: The updated consumer record, or None if the consumer does not exist.
        :rtype: Optional[Dict[str, Any]]
        """
        if consumer_id not in self.consumer_data:
            return None

        extractor = self.consumer_store.get(consumer_id)
        if not extractor:
            return None

        await extractor.stop()
        self.consumer_data[consumer_id]["status"] = "INACTIVE"

        self._record_operation(OP_UPDATE, consumer_id)
        return await self._map_consumer_record_to_response(consumer_id)

    async def update_consumer(self, consumer_id: str, payload: ConsumerUpdateRequest) -> Optional[Dict[str, Any]]:
        """
        Update an existing consumer's broker info, topic, or processor configurations in memory.
        A new :class:`MessageExtractor` is built if the processors are updated.

        :param consumer_id: The UUID of the consumer to update.
        :type consumer_id: str
        :param payload: Fields to update (e.g. broker_ip, broker_port, topic, processor_configs).
        :type payload: ConsumerUpdateRequest
        :return: The updated consumer record, or None if not found.
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

        if payload.processor_configs is not None:
            new_proc_list = []
            for proc_cfg in payload.processor_configs:
                proc_dict = {
                    "id": str(uuid.uuid4()),
                    "processor_type": proc_cfg.processor_type,
                    "config": proc_cfg.config,
                    "created_at": None,
                    "updated_at": None
                }
                new_proc_list.append(proc_dict)
            self.processor_data[consumer_id] = new_proc_list

            if consumer_id in self.consumer_store:
                old_extractor = self.consumer_store[consumer_id]
                await old_extractor.stop()

                new_extractor = await self._build_extractor(consumer_id)
                self.consumer_store[consumer_id] = new_extractor

                if cdata["status"] == "ACTIVE":
                    await new_extractor.start()

        self._record_operation(OP_UPDATE, consumer_id)
        return await self._map_consumer_record_to_response(consumer_id)

    async def delete_consumer(self, consumer_id: str) -> bool:
        """
        Delete a consumer from the in-memory store. If currently active, it is first stopped.

        :param consumer_id: The UUID of the consumer to delete.
        :type consumer_id: str
        :return: True if the consumer was found and deleted, False otherwise.
        :rtype: bool
        """
        if consumer_id not in self.consumer_data:
            return False

        extractor = self.consumer_store.get(consumer_id)
        if extractor:
            await extractor.stop()
            del self.consumer_store[consumer_id]

        del self.consumer_data[consumer_id]
        if consumer_id in self.processor_data:
            del self.processor_data[consumer_id]

        self._record_operation(OP_DELETE, consumer_id)
        return True

    async def sync_with_db(self) -> None:
        """
        Example method to be called periodically or from a background task.
        It processes the `operation_journal` and applies CREATE/UPDATE/DELETE
        operations to the DB (pseudocode). Only one sync runs at a time.

        :return: None
        :rtype: None
        """
        async with self._lock:
            if self.sync_in_progress:
                # Already syncing, skip
                return
            self.sync_in_progress = True

        try:
            # Local copy of the journal
            ops_to_sync = []
            while self.operation_journal:
                ops_to_sync.append(self.operation_journal.pop(0))

            # TODO: Actual DB logic. For each (op_type, consumer_id):
            for (op_type, cid) in ops_to_sync:
                if op_type == OP_CREATE:
                    # e.g., retrieve consumer_data[cid], insert in DB
                    pass
                elif op_type == OP_UPDATE:
                    pass
                elif op_type == OP_DELETE:
                    pass

        finally:
            async with self._lock:
                self.sync_in_progress = False

    def _record_operation(self, op_type: str, consumer_id: str) -> None:
        """
        Record a create/update/delete operation for future DB synchronization.

        :param op_type: One of OP_CREATE, OP_UPDATE, or OP_DELETE.
        :type op_type: str
        :param consumer_id: The consumer UUID.
        :type consumer_id: str
        :return: None
        :rtype: None
        """
        self.operation_journal.append((op_type, consumer_id))

    async def _build_extractor(self, consumer_id: str) -> Optional[MessageExtractor]:
        """
        Build a :class:`MessageExtractor` from the in-memory consumer and processor data.

        :param consumer_id: The consumer UUID to look up in memory.
        :type consumer_id: str
        :return: A new MessageExtractor if data is found, otherwise None.
        :rtype: Optional[MessageExtractor]
        """
        if consumer_id not in self.consumer_data:
            return None

        cdata = self.consumer_data[consumer_id]
        proc_list = self.processor_data.get(consumer_id, [])

        processors = []
        for p_dict in proc_list:
            processor = await ProcessorFactory.create_processor(
                p_dict["processor_type"],
                p_dict["config"]
            )
            processors.append(processor)

        extractor = MessageExtractor(
            broker=f"{cdata['broker_ip']}:{cdata['broker_port']}",
            topic=cdata["topic"],
            group_id=cdata["consumer_group"],
            processors=processors,
            client_id=consumer_id
        )
        return extractor

    async def _map_consumer_record_to_response(self, consumer_id: str) -> Dict[str, Any]:
        """
        Convert the consumer and its processors from in-memory data into a dictionary
        suitable for returning from an API endpoint.

        :param consumer_id: The UUID of the consumer.
        :type consumer_id: str
        :return: A dictionary describing the consumer, including its processors, or an empty dict if not found.
        :rtype: Dict[str, Any]
        """
        if consumer_id not in self.consumer_data:
            return {}

        cdata = self.consumer_data[consumer_id]
        proc_list = self.processor_data.get(consumer_id, [])

        processor_details = []
        for p in proc_list:
            processor_details.append({
                "id": p["id"],
                "processor_type": p["processor_type"],
                "config": p["config"],
                "created_at": p["created_at"],
                "updated_at": p["updated_at"]
            })

        return {
            "consumer_id": cdata["consumer_id"],
            "broker_ip": cdata["broker_ip"],
            "broker_port": cdata["broker_port"],
            "topic": cdata["topic"],
            "consumer_group": cdata["consumer_group"],
            "status": cdata["status"],
            "processor_configs": processor_details,
            "created_at": cdata["created_at"],
            "updated_at": cdata["updated_at"]
        }