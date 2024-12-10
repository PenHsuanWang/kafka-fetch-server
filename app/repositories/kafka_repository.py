from abc import ABC, abstractmethod
from typing import Optional, Dict
from confluent_kafka import Consumer


class IKafkaRepository(ABC):
    @abstractmethod
    def create_consumer(
            self,
            consumer_name: str,
            broker_ip: str,
            broker_port: int,
            topic: str,
            group_id: Optional[str] = None,
            manager_id: int = 1
    ) -> Consumer:
        pass

    @abstractmethod
    def get_all_consumers(self) -> Dict[str, Consumer]:
        pass

    @abstractmethod
    def get_consumers_by_manager(self, manager_id: int) -> Dict[str, Consumer]:
        pass

    @abstractmethod
    def close_consumer(self, consumer_id: str) -> bool:
        pass

    @abstractmethod
    def get_consumer_metadata(self, consumer_id: str) -> Optional[Dict]:
        pass


class KafkaRepository(IKafkaRepository):
    def __init__(self):
        # Storing consumers in memory for demonstration.
        self._consumers: Dict[str, Consumer] = {}
        self._consumer_metadata: Dict[str, Dict] = {}

    def create_consumer(
            self,
            consumer_name: str,
            broker_ip: str,
            broker_port: int,
            topic: str,
            group_id: Optional[str] = None,
            manager_id: int = 1
    ) -> Consumer:
        # Configuration for the Kafka consumer.
        conf = {
            'bootstrap.servers': f"{broker_ip}:{broker_port}",
            'group.id': group_id or consumer_name,
            'auto.offset.reset': 'earliest'
        }
        consumer = Consumer(conf)
        consumer.subscribe([topic])

        # Store the consumer and its metadata.
        self._consumers[consumer_name] = consumer
        self._consumer_metadata[consumer_name] = {
            'manager_id': manager_id,
            'topic_name': topic,
            'group_id': group_id or consumer_name,
            'consumer_name': consumer_name
        }
        return consumer

    def get_all_consumers(self) -> Dict[str, Consumer]:
        return self._consumers

    def get_consumers_by_manager(self, manager_id: int) -> Dict[str, Consumer]:
        return {
            cid: cons for cid, cons in self._consumers.items()
            if self._consumer_metadata[cid]['manager_id'] == manager_id
        }

    def close_consumer(self, consumer_id: str) -> bool:
        consumer = self._consumers.get(consumer_id)
        if consumer:
            consumer.close()
            del self._consumers[consumer_id]
            del self._consumer_metadata[consumer_id]
            return True
        return False

    def get_consumer_metadata(self, consumer_id: str) -> Optional[Dict]:
        return self._consumer_metadata.get(consumer_id)