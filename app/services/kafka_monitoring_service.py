# file: app/services/kafka_monitoring_service.py

"""
Kafka Monitoring Service
========================

Provides methods to list consumer groups and retrieve offset details
via Kafka AdminClient (from the kafka-python library). It also provides
a method to compute consumer group lag for a given topic.
"""

from typing import List, Dict, Any
from kafka import KafkaAdminClient, KafkaConsumer, errors
from kafka.structs import TopicPartition, OffsetAndMetadata

from app.services.kafka_consumer_serving_manager import KafkaConsumerServingManager


class KafkaMonitoringService:
    """
    A service that uses KafkaAdminClient to retrieve consumer group metadata,
    such as group listings and current offsets, and computes consumer group lag.
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
            offsets_map = admin_client.list_consumer_group_offsets(group_id)
            # offsets_map is a dict: {TopicPartition(topic='...', partition=0): OffsetAndMetadata(offset=..., metadata=...)}
            for tp, offmeta in offsets_map.items():
                entry = {
                    "topic": tp.topic,
                    "partition": tp.partition,
                    "current_offset": offmeta.offset,
                    "metadata": offmeta.metadata
                }
                result["offsets"].append(entry)
        except errors.KafkaError as e:
            print(f"Error fetching offsets for group {group_id}: {e}")
            result["offsets"] = []
        finally:
            if 'admin_client' in locals():
                admin_client.close()
        return result

    def get_consumer_group_lag(self, group_id: str, topic: str) -> Dict[str, Any]:
        """
        Compute lag information for the specified consumer group and topic.
        It retrieves the group's committed offsets via the AdminClient,
        then creates a temporary KafkaConsumer (without group_id) to query the
        log-end offsets for the topic's partitions, and finally computes the lag.

        :param group_id: The Kafka consumer group ID.
        :type group_id: str
        :param topic: The topic to query.
        :type topic: str
        :return: A dictionary such as:
            {
                "group_id": "groupA",
                "topic": "topicA",
                "partitions": {
                    0: { "current_offset": 123, "log_end_offset": 130, "lag": 7 },
                    1: { ... },
                    ...
                }
            }
        :rtype: Dict[str, Any]
        """
        result = {
            "group_id": group_id,
            "topic": topic,
            "partitions": {}
        }
        # Step 1: Use AdminClient to get the committed offsets for the given group and topic.
        group_offsets = {}
        try:
            admin_client = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            offsets_map = admin_client.list_consumer_group_offsets(group_id)
            # Filter offsets for the given topic.
            for tp, offmeta in offsets_map.items():
                if tp.topic == topic:
                    group_offsets[tp.partition] = offmeta.offset
        except errors.KafkaError as e:
            print(f"Error fetching offsets for group {group_id}: {e}")
        finally:
            if 'admin_client' in locals():
                admin_client.close()

        if not group_offsets:
            raise Exception(f"No committed offsets found for group '{group_id}' on topic '{topic}'")

        # Step 2: Create a temporary KafkaConsumer (without group_id) to get log-end offsets.
        consumer = KafkaConsumer(
            bootstrap_servers=self.bootstrap_servers,
            group_id=None,  # do not join consumer group，just used to be check-up tool
            enable_auto_commit=False,
            auto_offset_reset="latest"
        )
        try:
            partitions = [TopicPartition(topic, p) for p in group_offsets.keys()]
            consumer.assign(partitions)
            # Poll once to ensure metadata is updated.
            consumer.poll(timeout_ms=5000)
            end_offsets = consumer.end_offsets(partitions)
            for tp in partitions:
                current_offset = group_offsets.get(tp.partition, 0)
                log_end_offset = end_offsets.get(tp, 0)
                lag = log_end_offset - current_offset if log_end_offset >= current_offset else 0
                result["partitions"][tp.partition] = {
                    "current_offset": current_offset,
                    "log_end_offset": log_end_offset,
                    "lag": lag
                }
        except Exception as e:
            print(f"Error fetching log end offsets: {e}")
            result["partitions"] = {}
        finally:
            consumer.close()

        return result