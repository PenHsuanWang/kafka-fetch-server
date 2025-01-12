# file: app/api/v1/consumergroups_routes.py

"""
Consumer Groups Routes
======================

Defines FastAPI routes for monitoring Kafka consumer groups, similar to
how consumers_routes.py manages individual consumers.

:module: consumergroups_routes
:author: Your Name
:created: 2025-01-01
:seealso: app.services.kafka_monitoring_service
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query

from app.api.v1.schemas.consumergroups_responses import (
    ConsumerGroupListResponse,
    ConsumerGroupOffsetsResponse
)
from app.services.kafka_monitoring_service import KafkaMonitoringService


router = APIRouter()


@router.get("/", response_model=ConsumerGroupListResponse, status_code=status.HTTP_200_OK)
def list_consumer_groups(all_groups: bool = Query(False)) -> ConsumerGroupListResponse:
    """
    Lists either all consumer groups in the cluster (all_groups=true)
    or only those used by this service (all_groups=false).

    :param all_groups: If True, lists all groups in Kafka. If False, only local groups.
    :type all_groups: bool
    :return: A ConsumerGroupListResponse containing a list of group IDs
    :rtype: ConsumerGroupListResponse
    """
    monitoring_service = KafkaMonitoringService(bootstrap_servers="localhost:9092")

    if all_groups:
        group_ids = monitoring_service.list_consumer_groups_all()
    else:
        group_ids = monitoring_service.list_consumer_groups_local()

    return ConsumerGroupListResponse(consumer_groups=group_ids)


@router.get("/{group_id}/offsets",
            response_model=ConsumerGroupOffsetsResponse,
            status_code=status.HTTP_200_OK)
def get_consumer_group_offsets(group_id: str) -> ConsumerGroupOffsetsResponse:
    """
    Retrieve offset details for the given consumer group from Kafka.

    :param group_id: The Kafka consumer group ID
    :type group_id: str
    :return: ConsumerGroupOffsetsResponse with offset data
    :rtype: ConsumerGroupOffsetsResponse
    :raises HTTPException 404: If the group doesn't exist or has no offsets
    """
    monitoring_service = KafkaMonitoringService(bootstrap_servers="localhost:9092")
    raw_result = monitoring_service.get_consumer_group_offsets(group_id)

    # If 'offsets' is empty, we treat the group as not found or no offsets
    if not raw_result["offsets"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer group '{group_id}' not found or no offsets committed."
        )

    # Convert raw_result to a Pydantic response model
    return ConsumerGroupOffsetsResponse(**raw_result)
