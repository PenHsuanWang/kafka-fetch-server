"""Consumers API endpoints.

Defines the FastAPI endpoints for managing Kafka consumers (create, start, stop, etc.).
"""

from fastapi import APIRouter, HTTPException, status
from typing import Any

from app.api.schemas.consumer_requests import ConsumerCreateRequest, ConsumerUpdateRequest
from app.api.schemas.consumer_responses import ConsumerResponse
from app.services.consumer_service import ConsumerService

router = APIRouter()


@router.post("/", response_model=ConsumerResponse, status_code=status.HTTP_201_CREATED)
async def create_consumer(payload: ConsumerCreateRequest) -> ConsumerResponse:
    """
    Create a new Kafka consumer resource.

    :param payload: The consumer creation request body
    :type payload: ConsumerCreateRequest
    :return: The newly created consumer details
    :rtype: ConsumerResponse
    """
    result = await ConsumerService.create_consumer(payload)
    return ConsumerResponse(**result)


@router.get("/{consumer_id}", response_model=ConsumerResponse)
async def get_consumer(consumer_id: str) -> ConsumerResponse:
    """
    Retrieve an existing consumer by its ID.

    :param consumer_id: The UUID of the consumer
    :type consumer_id: str
    :return: Consumer details
    :rtype: ConsumerResponse
    """
    result = await ConsumerService.get_consumer(consumer_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found."
        )
    return ConsumerResponse(**result)


@router.post("/{consumer_id}/start", response_model=ConsumerResponse)
async def start_consumer(consumer_id: str) -> ConsumerResponse:
    """
    Start a stopped consumer.

    :param consumer_id: The UUID of the consumer
    :type consumer_id: str
    :return: The updated consumer details (status = ACTIVE)
    :rtype: ConsumerResponse
    """
    result = await ConsumerService.start_consumer(consumer_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found in store."
        )
    return ConsumerResponse(**result)


@router.post("/{consumer_id}/stop", response_model=ConsumerResponse)
async def stop_consumer(consumer_id: str) -> ConsumerResponse:
    """
    Stop an active consumer.

    :param consumer_id: The UUID of the consumer
    :type consumer_id: str
    :return: The updated consumer details (status = INACTIVE)
    :rtype: ConsumerResponse
    """
    result = await ConsumerService.stop_consumer(consumer_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found in store."
        )
    return ConsumerResponse(**result)


@router.put("/{consumer_id}", response_model=ConsumerResponse)
async def update_consumer(consumer_id: str, payload: ConsumerUpdateRequest) -> ConsumerResponse:
    """
    Update an existing consumer's configuration or downstream processors.

    :param consumer_id: The UUID of the consumer
    :type consumer_id: str
    :param payload: The updated consumer details
    :type payload: ConsumerUpdateRequest
    :return: The updated consumer details
    :rtype: ConsumerResponse
    """
    result = await ConsumerService.update_consumer(consumer_id, payload)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found."
        )
    return ConsumerResponse(**result)


@router.delete("/{consumer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_consumer(consumer_id: str) -> None:
    """
    Delete a consumer by its ID.

    :param consumer_id: The UUID of the consumer
    :type consumer_id: str
    :return: None
    :rtype: None
    """
    deleted = await ConsumerService.delete_consumer(consumer_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found."
        )
    return None