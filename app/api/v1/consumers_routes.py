"""
Consumers Routes
================

Defines the FastAPI routes for managing Kafka consumers. Each route delegates
to the singleton `KafkaConsumerServingManager` for actual create/update/delete
operations on Kafka consumers.

:module: consumers_routes
:author: Your Name
:created: 2025-01-01
:seealso: app.services.kafka_consumer_serving_manager
"""

from typing import List
from fastapi import APIRouter, HTTPException, status

from app.api.v1.schemas.consumer_requests import (
    ConsumerCreateRequest,
    ConsumerUpdateRequest
)
from app.api.v1.schemas.consumer_responses import ConsumerResponse
from app.services.kafka_consumer_serving_manager import KafkaConsumerServingManager

router = APIRouter()


@router.get("/", response_model=List[ConsumerResponse], status_code=status.HTTP_200_OK)
async def list_consumers() -> List[ConsumerResponse]:
    """
    List all consumers currently in memory.

    :return: A list of ConsumerResponse objects.
    :rtype: List[ConsumerResponse]
    """
    manager = KafkaConsumerServingManager.get_instance()
    consumers_data = await manager.list_consumers()
    return [ConsumerResponse(**c) for c in consumers_data]


@router.post("/", response_model=ConsumerResponse, status_code=status.HTTP_201_CREATED)
async def create_consumer(payload: ConsumerCreateRequest) -> ConsumerResponse:
    """
    Create a new consumer.

    :param payload: The consumer creation request (broker, topic, consumer_group, etc.).
    :type payload: ConsumerCreateRequest
    :return: A ConsumerResponse containing the newly created consumer.
    :rtype: ConsumerResponse
    """
    manager = KafkaConsumerServingManager.get_instance()
    result = await manager.create_consumer(payload)
    return ConsumerResponse(**result)


@router.get("/{consumer_id}", response_model=ConsumerResponse, status_code=status.HTTP_200_OK)
async def get_consumer(consumer_id: str) -> ConsumerResponse:
    """
    Retrieve details of an existing consumer by its ID.

    :param consumer_id: The UUID of the consumer.
    :type consumer_id: str
    :return: The ConsumerResponse if found.
    :rtype: ConsumerResponse
    :raises HTTPException 404: If the consumer is not found.
    """
    manager = KafkaConsumerServingManager.get_instance()
    data = await manager.get_consumer_record(consumer_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found"
        )
    return ConsumerResponse(**data)


@router.put("/{consumer_id}", response_model=ConsumerResponse, status_code=status.HTTP_200_OK)
async def update_consumer(consumer_id: str,
                          payload: ConsumerUpdateRequest) -> ConsumerResponse:
    """
    Update an existing consumer's broker info, topic, or processor configurations.

    :param consumer_id: The UUID of the consumer to update.
    :type consumer_id: str
    :param payload: Fields to update (broker_ip, broker_port, topic, processor_configs).
    :type payload: ConsumerUpdateRequest
    :return: Updated consumer details.
    :rtype: ConsumerResponse
    :raises HTTPException 404: If consumer is not found.
    """
    manager = KafkaConsumerServingManager.get_instance()
    updated = await manager.update_consumer(consumer_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found"
        )
    return ConsumerResponse(**updated)


@router.post("/{consumer_id}/start", response_model=ConsumerResponse, status_code=status.HTTP_200_OK)
async def start_consumer(consumer_id: str) -> ConsumerResponse:
    """
    Start a stopped consumer by its ID.

    :param consumer_id: The UUID of the consumer.
    :type consumer_id: str
    :return: The updated consumer details (status='ACTIVE').
    :rtype: ConsumerResponse
    :raises HTTPException 404: If consumer is not found.
    """
    manager = KafkaConsumerServingManager.get_instance()
    started = await manager.start_consumer(consumer_id)
    if not started:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found"
        )
    return ConsumerResponse(**started)


@router.post("/{consumer_id}/stop", response_model=ConsumerResponse, status_code=status.HTTP_200_OK)
async def stop_consumer(consumer_id: str) -> ConsumerResponse:
    """
    Stop an active consumer by ID.

    :param consumer_id: The UUID of the consumer.
    :type consumer_id: str
    :return: The updated consumer details (status='INACTIVE').
    :rtype: ConsumerResponse
    :raises HTTPException 404: If consumer is not found.
    """
    manager = KafkaConsumerServingManager.get_instance()
    stopped = await manager.stop_consumer(consumer_id)
    if not stopped:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found"
        )
    return ConsumerResponse(**stopped)


@router.delete("/{consumer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_consumer(consumer_id: str) -> None:
    """
    Delete a consumer by ID. The consumer is stopped first if active.

    :param consumer_id: The UUID of the consumer.
    :type consumer_id: str
    :return: None
    :rtype: None
    :raises HTTPException 404: If consumer is not found.
    """
    manager = KafkaConsumerServingManager.get_instance()
    success = await manager.delete_consumer(consumer_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found"
        )
    return None
