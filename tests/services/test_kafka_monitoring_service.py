"""
Test KafkaMonitoringService
===========================

Unit tests for the kafka_monitoring_service.py module, ensuring it
correctly handles listing groups and offsets.
"""

import pytest
from unittest.mock import patch, MagicMock
from kafka.structs import TopicPartition, OffsetAndMetadata
from kafka.errors import KafkaError

from app.services.kafka_monitoring_service import KafkaMonitoringService
from app.services.kafka_consumer_serving_manager import KafkaConsumerServingManager


@pytest.fixture
def mock_manager():
    """
    Fixture to reset or mock KafkaConsumerServingManager for local consumer_data usage.
    """
    manager = KafkaConsumerServingManager.get_instance()
    # Clear out existing data for test isolation
    manager.consumer_data.clear()
    manager.processor_data.clear()
    manager.consumer_store.clear()

    # Setup some test data
    manager.consumer_data["c1"] = {
        "consumer_id": "c1",
        "consumer_group": "local_group1",
        "broker_ip": "localhost",
        "broker_port": 9092,
        "topic": "test-topic",
        "status": "ACTIVE"
    }
    manager.consumer_data["c2"] = {
        "consumer_id": "c2",
        "consumer_group": "local_group2",
        "broker_ip": "localhost",
        "broker_port": 9092,
        "topic": "test-topic2",
        "status": "INACTIVE"
    }

    yield manager

    # Teardown/cleanup
    manager.consumer_data.clear()
    manager.processor_data.clear()
    manager.consumer_store.clear()


def test_list_consumer_groups_local(mock_manager):
    """
    Ensures list_consumer_groups_local returns only the groups
    from the manager's data.
    """
    svc = KafkaMonitoringService(bootstrap_servers="dummy:9092")
    result = svc.list_consumer_groups_local()
    # We have "local_group1" and "local_group2" from mock_manager fixture
    assert set(result) == {"local_group1", "local_group2"}


@patch("app.services.kafka_monitoring_service.KafkaAdminClient")
def test_list_consumer_groups_all(mock_admin_cls, mock_manager):
    """
    Ensures list_consumer_groups_all calls KafkaAdminClient.list_consumer_groups()
    and returns the group IDs.
    """
    mock_admin = MagicMock()
    mock_admin_cls.return_value = mock_admin
    mock_admin.list_consumer_groups.return_value = [
        ("local_group1", "Stable"),
        ("local_group2", "Stable"),
        ("external_group", "Stable")
    ]

    svc = KafkaMonitoringService(bootstrap_servers="dummy:9092")
    all_groups = svc.list_consumer_groups_all()
    assert set(all_groups) == {"local_group1", "local_group2", "external_group"}


@patch("app.services.kafka_monitoring_service.KafkaAdminClient")
def test_get_consumer_group_offsets_ok(mock_admin_cls, mock_manager):
    """
    Scenario: get_consumer_group_offsets returns normal offsets data from KafkaAdminClient.
    """
    group_id = "test_group"
    mock_admin = MagicMock()
    mock_admin_cls.return_value = mock_admin

    # Construct some Kafka offset data
    tp1 = TopicPartition(topic="payments", partition=0)
    offmeta1 = OffsetAndMetadata(offset=123, metadata="m1")
    tp2 = TopicPartition(topic="payments", partition=1)
    offmeta2 = OffsetAndMetadata(offset=456, metadata=None)

    mock_admin.list_consumer_group_offsets.return_value = {
        tp1: offmeta1,
        tp2: offmeta2
    }

    svc = KafkaMonitoringService(bootstrap_servers="dummy:9092")
    result = svc.get_consumer_group_offsets(group_id)

    assert result["group_id"] == group_id
    assert len(result["offsets"]) == 2

    offsets_sorted = sorted(result["offsets"], key=lambda x: x["partition"])
    assert offsets_sorted[0]["topic"] == "payments"
    assert offsets_sorted[0]["partition"] == 0
    assert offsets_sorted[0]["current_offset"] == 123
    assert offsets_sorted[0]["metadata"] == "m1"

    assert offsets_sorted[1]["partition"] == 1
    assert offsets_sorted[1]["current_offset"] == 456


@patch("app.services.kafka_monitoring_service.KafkaAdminClient")
def test_get_consumer_group_offsets_unknown_group(mock_admin_cls, mock_manager):
    """
    Scenario: get_consumer_group_offsets returns empty if group doesn't exist.
    """
    group_id = "unknown_group"
    mock_admin = MagicMock()
    mock_admin_cls.return_value = mock_admin

    # Instead of UnknownConsumerGroupError, raise a generic KafkaError
    mock_admin.list_consumer_group_offsets.side_effect = KafkaError("Unknown group")

    svc = KafkaMonitoringService()
    result = svc.get_consumer_group_offsets(group_id)
    assert result["group_id"] == group_id
    # Because we treat KafkaError or empty offsets as "not found,"
    # the code sets result["offsets"] = []
    assert result["offsets"] == []
