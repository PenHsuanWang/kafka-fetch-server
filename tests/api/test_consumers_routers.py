"""
Test Consumers Routes
=====================

Uses pytest and FastAPI's TestClient to test the `consumers_routes` module,
including both normal use-cases (create, update, start, stop, delete) and
exception handling (e.g., 404 Not Found, 422 for validation errors).

:module: test_consumers_routes
:author: Your Name
:created: 2025-01-01
:seealso: app.api.v1.consumers_routes
"""

import pytest
from fastapi import status
from typing import List

from app.services.kafka_consumer_serving_manager import KafkaConsumerServingManager

created_consumer_id = None  # Will store the first created consumer's ID

def test_list_consumers_initially_empty(test_client):
    """
    Scenario: No consumers exist initially.
    Expected: GET /consumers returns an empty list [].
    """
    # Ensure manager is empty before testing
    manager = KafkaConsumerServingManager.get_instance()
    manager.consumer_data.clear()
    manager.consumer_store.clear()
    manager.processor_data.clear()

    response = test_client.get("/consumers/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_create_consumer_valid_payload(test_client):
    """
    Scenario: POST /consumers with valid fields should create a consumer,
    returning 201 and JSON containing `consumer_id` and `status` == "ACTIVE"
    (because auto_start=True).
    """
    payload = {
        "broker_ip": "localhost",
        "broker_port": 9092,
        "topic": "test_topic",
        "consumer_group": "test_group",
        "auto_start": True,
        "processor_configs": [
            {
                "processor_type": "file_sink",
                "config": {"file_path": "/tmp/test.log"}
            }
        ]
    }
    response = test_client.post("/consumers/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert "consumer_id" in data
    assert data["status"] == "ACTIVE"

    # Save for subsequent tests
    global created_consumer_id
    created_consumer_id = data["consumer_id"]


def test_list_consumers_non_empty(test_client):
    """
    Scenario: After one consumer is created, listing should show exactly one consumer.
    """
    response = test_client.get("/consumers/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["consumer_id"] == created_consumer_id


def test_create_consumer_missing_broker_ip(test_client):
    """
    Scenario: Missing 'broker_ip' -> Pydantic validation error -> 422 Unprocessable Entity.
    """
    payload = {
        # "broker_ip" is missing
        "broker_port": 9092,
        "topic": "missing_broker_ip",
        "consumer_group": "test_group"
    }
    response = test_client.post("/consumers/", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_consumer_invalid_port(test_client):
    """
    Scenario: Negative or out-of-range broker_port -> 422 or 400.
    We expect Pydantic to raise 422 by default.
    """
    payload = {
        "broker_ip": "localhost",
        "broker_port": -1,
        "topic": "invalid_port",
        "consumer_group": "test_group"
    }
    response = test_client.post("/consumers/", json=payload)
    # By default, Pydantic int fields won't accept negative if you set constraints,
    # or the logic might treat negative as valid. Adjust as needed.
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]


def test_get_consumer_ok(test_client):
    """
    Scenario: GET /consumers/{id} on an existing consumer returns 200 with correct data.
    """
    response = test_client.get(f"/consumers/{created_consumer_id}")
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["consumer_id"] == created_consumer_id


def test_get_consumer_not_found(test_client):
    """
    Scenario: GET /consumers/{id} with a random, nonexistent ID -> 404 Not Found
    """
    response = test_client.get("/consumers/random-nonexistent-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]


def test_start_consumer_already_active(test_client):
    """
    Scenario: The consumer was created with auto_start=True, so it's ACTIVE.
              Starting again might be a no-op but should still return 200.
    """
    response = test_client.post(f"/consumers/{created_consumer_id}/start")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ACTIVE"


def test_stop_consumer_ok(test_client):
    """
    Scenario: POST /consumers/{id}/stop -> Should become INACTIVE.
    """
    response = test_client.post(f"/consumers/{created_consumer_id}/stop")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "INACTIVE"


def test_stop_consumer_already_inactive(test_client):
    """
    Scenario: The consumer is already INACTIVE -> Stopping again is a no-op or success (200).
    """
    response = test_client.post(f"/consumers/{created_consumer_id}/stop")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "INACTIVE"


def test_update_consumer_partial_fields(test_client):
    """
    Scenario: Provide only 'broker_port' to update. 
              The rest remain unchanged from initial creation.
    """
    payload = {"broker_port": 9999}
    response = test_client.put(f"/consumers/{created_consumer_id}", json=payload)
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["broker_port"] == 9999
    # confirm other fields remain as originally set
    assert data["topic"] == "test_topic"


def test_update_consumer_invalid_processor_config(test_client):
    """
    Scenario: Provide a processor config missing required fields -> 422 or 400.
    E.g., 'file_sink' but missing 'file_path' in config.
    """
    payload = {
        "processor_configs": [
            {"processor_type": "file_sink"}  # incomplete, missing config details
        ]
    }
    response = test_client.put(f"/consumers/{created_consumer_id}", json=payload)
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]


def test_delete_consumer_ok(test_client):
    """
    Scenario: DELETE /consumers/{id} -> 204, then subsequent GET returns 404.
    """
    response = test_client.delete(f"/consumers/{created_consumer_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # confirm it was deleted
    response2 = test_client.get(f"/consumers/{created_consumer_id}")
    assert response2.status_code == status.HTTP_404_NOT_FOUND


def test_delete_consumer_already_deleted(test_client):
    """
    Scenario: Deleting the same consumer ID again -> 404 Not Found.
    """
    resp = test_client.delete(f"/consumers/{created_consumer_id}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("invalid_id", [
    " ",        # space
    "not-a-uuid",  # random string
    "12345",    # numeric but not a real ID
])
def test_get_consumer_invalid_id_format(test_client, invalid_id):
    """
    Scenario: GET with an ID that doesn't conform to typical UUID format.
    It should still respond with 404, since the route expects a real ID.
    """
    response = test_client.get(f"/consumers/{invalid_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_multiple_consumers_ok(test_client):
    """
    Scenario: Create multiple consumers in a row, then list them to ensure they're both present.
    """
    # Clear manager first
    manager = KafkaConsumerServingManager.get_instance()
    manager.consumer_data.clear()
    manager.consumer_store.clear()
    manager.processor_data.clear()

    payload1 = {
        "broker_ip": "127.0.0.1",
        "broker_port": 9092,
        "topic": "multi-1",
        "consumer_group": "group-m1"
    }
    payload2 = {
        "broker_ip": "127.0.0.1",
        "broker_port": 9093,
        "topic": "multi-2",
        "consumer_group": "group-m2"
    }

    resp1 = test_client.post("/consumers/", json=payload1)
    resp2 = test_client.post("/consumers/", json=payload2)
    assert resp1.status_code == status.HTTP_201_CREATED
    assert resp2.status_code == status.HTTP_201_CREATED

    list_resp = test_client.get("/consumers/")
    assert list_resp.status_code == status.HTTP_200_OK
    data = list_resp.json()
    assert len(data) == 2
    topics = [c["topic"] for c in data]
    assert "multi-1" in topics
    assert "multi-2" in topics


def test_concurrent_creates_no_kafka_connection(test_client):
    """
    Scenario: Simulate creating multiple consumers "concurrently."
    We rely on the mock to ensure no real Kafka connections are made.
    """
    manager = KafkaConsumerServingManager.get_instance()
    manager.consumer_data.clear()
    manager.consumer_store.clear()
    manager.processor_data.clear()

    payloads = [
        {"broker_ip": "10.0.0.1", "broker_port": 9092, "topic": "parallel1", "consumer_group": "grp-par1"},
        {"broker_ip": "10.0.0.2", "broker_port": 9093, "topic": "parallel2", "consumer_group": "grp-par2"}
    ]

    for p in payloads:
        resp = test_client.post("/consumers/", json=p)
        assert resp.status_code == status.HTTP_201_CREATED

    # Quick check that both were created
    list_resp = test_client.get("/consumers/")
    assert list_resp.status_code == status.HTTP_200_OK
    data = list_resp.json()
    assert len(data) == 2
