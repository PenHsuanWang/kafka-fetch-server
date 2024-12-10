from typing import List
from uuid import uuid4
from app.models.consumer_model import ConsumerCreate, ConsumerResponse
from app.repositories.kafka_repository import IKafkaRepository
from app.services.monitoring_service import MonitoringService
from app.core.logger import logger

class ConsumerService:
    def __init__(self, kafka_repository: IKafkaRepository, monitoring_service: MonitoringService):
        self.kafka_repository = kafka_repository
        self.monitoring_service = monitoring_service

    def create_consumer(self, manager_id: int, consumer_data: ConsumerCreate) -> ConsumerResponse:
        # Generate a unique consumer_id (UUID) to differentiate consumers.
        consumer_id = str(uuid4())
        self.kafka_repository.create_consumer(
            consumer_name=consumer_data.consumer_name,
            broker_ip=consumer_data.broker_ip,
            broker_port=consumer_data.broker_port,
            topic=consumer_data.topic_name,
            group_id=consumer_data.group_id,
            manager_id=manager_id
        )
        logger.info(f"Created Consumer: {consumer_data.consumer_name} (ID: {consumer_id}) under Manager ID {manager_id}")
        return ConsumerResponse(
            consumer_id=consumer_id,
            consumer_name=consumer_data.consumer_name,
            topic_name=consumer_data.topic_name,
            group_id=consumer_data.group_id,
            manager_id=manager_id,
            status="created"
        )

    def list_consumers(self, manager_id: int) -> List[ConsumerResponse]:
        consumers = self.kafka_repository.get_consumers_by_manager(manager_id)
        response = []
        for cid, consumer in consumers.items():
            metadata = self.kafka_repository.get_consumer_metadata(cid)
            response.append(ConsumerResponse(
                consumer_id=cid,
                consumer_name=metadata['consumer_name'],
                topic_name=metadata['topic_name'],
                group_id=metadata['group_id'],
                manager_id=manager_id,
                status="active"
            ))
        logger.info(f"Listing {len(response)} consumers under Manager ID {manager_id}")
        return response

    def close_consumer(self, consumer_id: str) -> bool:
        success = self.kafka_repository.close_consumer(consumer_id)
        if success:
            logger.info(f"Closed Consumer ID {consumer_id}")
        else:
            logger.warning(f"Attempted to close non-existent Consumer ID {consumer_id}")
        return success
