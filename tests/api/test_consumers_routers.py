# tests/test_consumers_routes.py

import pytest
from fastapi import status
from typing import List

# We'll use test_client from conftest.py
# We'll store a created_consumer_id for reuse across tests
created_consumer_id = None

def test_list_consumers_initially_empty(test_client):
    """
    Scenario: No consumers exist initially.
    Expected: GET /consumers returns []
    """
    response = test_client.get("/consumers/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_create_consumer_valid_payload(test_client):
    """
    Scenario: POST with valid fields -> Should create consumer, return 201 + JSON with consumer_id.
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
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "consumer_id" in data
    assert data["status"] == "ACTIVE"

    global created_consumer_id
    created_consumer_id = data["consumer_id"]


def test_list_consumers_non_empty(test_client):
    """
    Scenario: After one consumer is created, listing should show it.
    """
    response = test_client.get("/consumers/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["consumer_id"] == created_consumer_id


def test_create_consumer_missing_broker_ip(test_client):
    """
    Scenario: Missing broker_ip -> Pydantic validation error -> 422 Unprocessable
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
    """
    payload = {
        "broker_ip": "localhost",
        "broker_port": -1,
        "topic": "invalid_port",
        "consumer_group": "test_group"
    }
    response = test_client.post("/consumers/", json=payload)
    # could be 422 from Pydantic or 400 if you do custom validation
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]


def test_get_consumer_ok(test_client):
    """
    Scenario: GET /consumers/{id} on an existing consumer.
    """
    response = test_client.get(f"/consumers/{created_consumer_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["consumer_id"] == created_consumer_id


def test_get_consumer_not_found(test_client):
    """
    Scenario: GET /consumers/{id} with a random ID -> 404
    """
    response = test_client.get("/consumers/random-nonexistent-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_start_consumer_already_active(test_client):
    """
    Scenario: The consumer was created with auto_start=True, so it's ACTIVE.
              Starting again might be no-op or success.
    """
    response = test_client.post(f"/consumers/{created_consumer_id}/start")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ACTIVE"


def test_stop_consumer_ok(test_client):
    """
    Scenario: POST /consumers/{id}/stop -> Should become INACTIVE
    """
    response = test_client.post(f"/consumers/{created_consumer_id}/stop")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "INACTIVE"


def test_stop_consumer_already_inactive(test_client):
    """
    Scenario: The consumer is already INACTIVE -> Stopping again is a no-op or success.
    """
    response = test_client.post(f"/consumers/{created_consumer_id}/stop")
    # Implementation detail: could remain 200 or return a custom message
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "INACTIVE"


def test_update_consumer_partial_fields(test_client):
    """
    Scenario: Provide only 'broker_port' to update. The rest remain unchanged.
    """
    payload = {"broker_port": 9999}
    response = test_client.put(f"/consumers/{created_consumer_id}", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["broker_port"] == 9999
    # confirm other fields remain
    assert data["topic"] == "test_topic"


def test_update_consumer_invalid_processor_config(test_client):
    """
    Scenario: Provide a processor type without required config -> 422 or 400.
    """
    payload = {
        "processor_configs": [
            {"processor_type": "file_sink"}  # missing "file_path"
        ]
    }
    response = test_client.put(f"/consumers/{created_consumer_id}", json=payload)
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]


def test_delete_consumer_ok(test_client):
    """
    Scenario: DELETE /consumers/{id} -> 204, then subsequent GET returns 404
    """
    response = test_client.delete(f"/consumers/{created_consumer_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # check retrieving after deletion
    response2 = test_client.get(f"/consumers/{created_consumer_id}")
    assert response2.status_code == status.HTTP_404_NOT_FOUND


def test_delete_consumer_already_deleted(test_client):
    """
    Scenario: Deleting the same consumer ID again -> 404
    """
    resp = test_client.delete(f"/consumers/{created_consumer_id}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND