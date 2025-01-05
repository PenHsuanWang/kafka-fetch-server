"""
Routes for managing Kafka consumers via CLI-like REST endpoints.

Users can:
- Create a consumer
- List all consumers
- Retrieve a single consumer
- Update consumer details
- Start/Stop the consumer
- Delete the consumer
"""

from typing import List
from fastapi import APIRouter, HTTPException, status

from app.api.v1.schemas.consumer_requests import ConsumerCreateRequest, ConsumerUpdateRequest
from app.api.v1.schemas.consumer_responses import ConsumerResponse
from app.services.kafka_manager_service import KafkaConsumerManager

router = APIRouter()

@router.get("/", response_model=List[ConsumerResponse], status_code=status.HTTP_200_OK)
async def list_consumers() -> List[ConsumerResponse]:
    """
    List all consumers currently in memory.

    :return: A list of ConsumerResponse objects
    :rtype: List[ConsumerResponse]
    """
    manager = KafkaConsumerManager()
    consumers_data = await manager.list_consumers()
    # Convert each dict to the ConsumerResponse Pydantic model
    return [ConsumerResponse(**c) for c in consumers_data if c]

@router.post("/", response_model=ConsumerResponse, status_code=status.HTTP_201_CREATED)
async def create_consumer(payload: ConsumerCreateRequest) -> ConsumerResponse:
    """
    Create a new Kafka consumer in memory.

    :param payload: The consumer creation request (broker, topic, consumer_group, etc.)
    :type payload: ConsumerCreateRequest
    :return: Details of the newly created consumer
    :rtype: ConsumerResponse
    """
    manager = KafkaConsumerManager()
    result = await manager.create_consumer(payload)
    return ConsumerResponse(**result)

@router.get("/{consumer_id}", response_model=ConsumerResponse, status_code=status.HTTP_200_OK)
async def get_consumer(consumer_id: str) -> ConsumerResponse:
    """
    Retrieve details of an existing consumer by its ID.

    :param consumer_id: The UUID of the consumer
    :type consumer_id: str
    :return: The ConsumerResponse if found
    :rtype: ConsumerResponse
    :raises HTTPException 404: If consumer not found
    """
    manager = KafkaConsumerManager()
    data = await manager.get_consumer_record(consumer_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found"
        )
    return ConsumerResponse(**data)

@router.put("/{consumer_id}", response_model=ConsumerResponse, status_code=status.HTTP_200_OK)
async def update_consumer(consumer_id: str, payload: ConsumerUpdateRequest) -> ConsumerResponse:
    """
    Update an existing consumer's broker info, topic, or processor configurations.

    :param consumer_id: The UUID of the consumer to update
    :type consumer_id: str
    :param payload: Fields to update
    :type payload: ConsumerUpdateRequest
    :return: Updated consumer details
    :rtype: ConsumerResponse
    :raises HTTPException 404: If consumer not found
    """
    manager = KafkaConsumerManager()
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
    Start a stopped consumer by ID.

    :param consumer_id: The UUID of the consumer
    :type consumer_id: str
    :return: The updated consumer details (status=ACTIVE)
    :rtype: ConsumerResponse
    :raises HTTPException 404: If consumer not found
    """
    manager = KafkaConsumerManager()
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

    :param consumer_id: The UUID of the consumer
    :type consumer_id: str
    :return: The updated consumer details (status=INACTIVE)
    :rtype: ConsumerResponse
    :raises HTTPException 404: If consumer not found
    """
    manager = KafkaConsumerManager()
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

    :param consumer_id: The UUID of the consumer
    :type consumer_id: str
    :return: None
    :rtype: None
    :raises HTTPException 404: If consumer not found
    """
    manager = KafkaConsumerManager()
    success = await manager.delete_consumer(consumer_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found"
        )
    return None