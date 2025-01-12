# file: app/services/kafka_monitoring_service.py

"""
Kafka Monitoring Service
========================

Provides methods to list consumer groups and retrieve offset details
via Kafka AdminClient (from the kafka-python library).
"""

from typing import List, Dict, Any
from kafka import KafkaAdminClient, errors
from kafka.structs import TopicPartition, OffsetAndMetadata

from app.services.kafka_consumer_serving_manager import KafkaConsumerServingManager


class KafkaMonitoringService:
    """
    A service that uses KafkaAdminClient to retrieve consumer group metadata,
    such as group listings and current offsets.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        :param bootstrap_servers: The Kafka broker(s) to connect to.
                                 e.g. "host1:9092,host2:9092"
        :type bootstrap_servers: str
        """
        self.bootstrap_servers = bootstrap_servers

    def list_consumer_groups_all(self) -> List[str]:
        """
        List all consumer group IDs known to the Kafka cluster.

        :return: A list of consumer group IDs (strings).
        :rtype: List[str]
        """
        try:
            admin_client = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            group_overviews = admin_client.list_consumer_groups()
            group_ids = [g[0] for g in group_overviews]  # each g is (group_id, state, ...)
            return group_ids
        except errors.KafkaError as e:
            print(f"Kafka error in list_consumer_groups_all: {e}")
            return []
        finally:
            if 'admin_client' in locals():
                admin_client.close()

    def list_consumer_groups_local(self) -> List[str]:
        """
        List only the consumer groups that the local manager has created in memory.

        :return: A list of consumer group IDs
        :rtype: List[str]
        """
        manager = KafkaConsumerServingManager.get_instance()
        group_ids = set()
        for cdata in manager.consumer_data.values():
            group_ids.add(cdata["consumer_group"])
        return list(group_ids)

    def get_consumer_group_offsets(self, group_id: str) -> Dict[str, Any]:
        """
        Retrieve offset information for the given consumer group from Kafka.

        :param group_id: The Kafka consumer group ID
        :type group_id: str
        :return: A dict with offset info, e.g.:
            {
                "group_id": "...",
                "offsets": [
                    { "topic": "...", "partition": 0, "current_offset": 123, "metadata": "..." },
                    ...
                ]
            }
        :rtype: Dict[str, Any]
        """
        result = {
            "group_id": group_id,
            "offsets": []
        }
        try:
            admin_client = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            offsets_map = admin_client.list_consumer_group_offsets(group_id)  # {TopicPartition: OffsetAndMetadata}

            for tp, offmeta in offsets_map.items():
                entry = {
                    "topic": tp.topic,
                    "partition": tp.partition,
                    "current_offset": offmeta.offset,
                    "metadata": offmeta.metadata
                }
                result["offsets"].append(entry)

        except errors.UnknownConsumerGroupError:
            # The group doesn't exist or has no offsets
            result["offsets"] = []
        except errors.KafkaError as e:
            print(f"Error fetching offsets for group {group_id}: {e}")
        finally:
            if 'admin_client' in locals():
                admin_client.close()

        return result
