"""
Test ConsumerGroups Routes
==========================

Uses pytest and FastAPI's TestClient to test the /consumergroups endpoints,
including list and offsets retrieval.
"""

import pytest
from fastapi import status
from unittest.mock import patch, MagicMock

from app.main import app  # or your server.py where `app` is defined
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.mark.parametrize("all_groups,expected_list", [
    (False, ["local_group1", "local_group2"]),
    (True,  ["local_group1", "local_group2", "external_group"])
])
def test_list_consumer_groups(all_groups, expected_list):
    """
    Scenario: GET /consumergroups[?all_groups=bool]
    Tests both local-only (all_groups=false) and all (all_groups=true).
    """

    # Mock the KafkaMonitoringService calls
    with patch("app.api.v1.consumergroups_routes.KafkaMonitoringService") as mock_service_cls:
        mock_service = MagicMock()
        mock_service.list_consumer_groups_all.return_value = ["local_group1", "local_group2", "external_group"]
        mock_service.list_consumer_groups_local.return_value = ["local_group1", "local_group2"]

        mock_service_cls.return_value = mock_service

        response = client.get(f"/consumergroups?all_groups={str(all_groups).lower()}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # data example: {"consumer_groups": [...]} 
        assert "consumer_groups" in data
        assert data["consumer_groups"] == expected_list


def test_get_consumer_group_offsets_ok():
    """
    Scenario: GET /consumergroups/{group_id}/offsets returns valid offsets.
    """
    group_id = "payment_group"
    mock_offsets = [
        {
            "topic": "payments",
            "partition": 0,
            "current_offset": 42,
            "metadata": None
        },
        {
            "topic": "payments",
            "partition": 1,
            "current_offset": 100,
            "metadata": "some-meta"
        }
    ]

    with patch("app.api.v1.consumergroups_routes.KafkaMonitoringService") as mock_service_cls:
        mock_service = MagicMock()
        mock_service.get_consumer_group_offsets.return_value = {
            "group_id": group_id,
            "offsets": mock_offsets
        }
        mock_service_cls.return_value = mock_service

        response = client.get(f"/consumergroups/{group_id}/offsets")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["group_id"] == group_id
        assert len(data["offsets"]) == 2
        assert data["offsets"][0]["partition"] == 0


def test_get_consumer_group_offsets_not_found():
    """
    Scenario: GET /consumergroups/{group_id}/offsets for a group that doesn't exist
    should return 404.
    """
    group_id = "unknown_group"
    with patch("app.api.v1.consumergroups_routes.KafkaMonitoringService") as mock_service_cls:
        mock_service = MagicMock()
        # Return empty 'offsets' to trigger the 404
        mock_service.get_consumer_group_offsets.return_value = {
            "group_id": group_id,
            "offsets": []
        }
        mock_service_cls.return_value = mock_service

        response = client.get(f"/consumergroups/{group_id}/offsets")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert group_id in data["detail"]
