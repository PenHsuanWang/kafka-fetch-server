"""
consumers_routes.py

This module defines the FastAPI routes for managing Kafka consumers under a specific Kafka Manager.

**Endpoints**:
- `POST /`: Create a new Kafka Consumer under a given Kafka Manager.
- `GET /`: List all Kafka Consumers under a given Kafka Manager.
- `DELETE /{consumer_id}`: Delete a specific Kafka Consumer under a given Kafka Manager.

These endpoints rely on various services:
- `ConsumerService` for consumer creation, listing, and deletion.
- `KafkaManagerService` to validate the existence of the specified Kafka Manager.
- `UserService` to handle user authentication and authorization.

Dependencies:
- `oauth2_scheme` from `app.core.security` is used to extract the authentication token.
- `decode_access_token` to decode and validate JWT tokens.
- `UserService` to retrieve user details from the provided token.
- `ConsumerService` and `KafkaManagerService` to manage consumers and verify manager existence.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from app.models.consumer_model import ConsumerCreate, ConsumerResponse
from app.services.consumer_service import ConsumerService
from app.repositories.kafka_repository import KafkaRepository, IKafkaRepository
from app.repositories.kafka_manager_repository import KafkaManagerRepository, IKafkaManagerRepository
from app.services.monitoring_service import MonitoringService
from app.services.kafka_manager_service import KafkaManagerService
from app.models.user_model import UserInDB
from app.core.security import oauth2_scheme, decode_access_token
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository, IUserRepository

router = APIRouter()


def get_kafka_repository_dependency() -> IKafkaRepository:
    """
    Dependency injector for the Kafka repository.

    :return: An implementation of IKafkaRepository
    :rtype: IKafkaRepository
    """
    return KafkaRepository()


def get_kafka_manager_repository_dependency() -> IKafkaManagerRepository:
    """
    Dependency injector for the Kafka Manager repository.

    :return: An implementation of IKafkaManagerRepository
    :rtype: IKafkaManagerRepository
    """
    return KafkaManagerRepository()


def get_monitoring_service(
        kafka_repository: IKafkaRepository = Depends(get_kafka_repository_dependency),
        kafka_manager_repository: IKafkaManagerRepository = Depends(get_kafka_manager_repository_dependency)
) -> MonitoringService:
    """
    Dependency injector for MonitoringService.

    :param kafka_repository: Kafka repository dependency
    :type kafka_repository: IKafkaRepository
    :param kafka_manager_repository: Kafka Manager repository dependency
    :type kafka_manager_repository: IKafkaManagerRepository
    :return: An instance of MonitoringService
    :rtype: MonitoringService
    """
    return MonitoringService(kafka_repository, kafka_manager_repository)


def get_consumer_service(
        monitoring_service: MonitoringService = Depends(get_monitoring_service),
        kafka_repository: IKafkaRepository = Depends(get_kafka_repository_dependency)
) -> ConsumerService:
    """
    Dependency injector for ConsumerService.

    :param monitoring_service: MonitoringService dependency
    :type monitoring_service: MonitoringService
    :param kafka_repository: Kafka repository dependency
    :type kafka_repository: IKafkaRepository
    :return: An instance of ConsumerService
    :rtype: ConsumerService
    """
    return ConsumerService(kafka_repository, monitoring_service)


def get_kafka_manager_service_dependency(
        kafka_manager_repository: IKafkaManagerRepository = Depends(get_kafka_manager_repository_dependency),
        kafka_repository: IKafkaRepository = Depends(get_kafka_repository_dependency)
) -> KafkaManagerService:
    """
    Dependency injector for KafkaManagerService.

    :param kafka_manager_repository: Kafka Manager repository dependency
    :type kafka_manager_repository: IKafkaManagerRepository
    :param kafka_repository: Kafka repository dependency
    :type kafka_repository: IKafkaRepository
    :return: An instance of KafkaManagerService
    :rtype: KafkaManagerService
    """
    return KafkaManagerService(kafka_manager_repository, kafka_repository)


def get_user_service_dependency() -> UserService:
    """
    Dependency injector for UserService.

    :return: An instance of UserService
    :rtype: UserService
    """
    user_repository: IUserRepository = UserRepository()
    return UserService(user_repository)


def get_current_user(
        token: str = Depends(oauth2_scheme),
        service: UserService = Depends(get_user_service_dependency)
) -> UserInDB:
    """
    Dependency injector to retrieve the current authenticated user.

    :param token: OAuth2 bearer token
    :type token: str
    :param service: UserService dependency
    :type service: UserService
    :raises HTTPException: If the user is not authenticated or token is invalid.
    :return: The current authenticated UserInDB
    :rtype: UserInDB
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    user = service.get_user(email=email)
    if user is None:
        raise credentials_exception
    return user


@router.post("/", response_model=ConsumerResponse, status_code=status.HTTP_201_CREATED)
def create_consumer(
        manager_id: int,
        consumer: ConsumerCreate,
        service: ConsumerService = Depends(get_consumer_service),
        kafka_manager_service: KafkaManagerService = Depends(get_kafka_manager_service_dependency),
        current_user: UserInDB = Depends(get_current_user)
) -> ConsumerResponse:
    """
    Create a new Kafka Consumer under a specific Kafka Manager.

    **Parameters**:
    - **manager_id** (int): The ID of the Kafka Manager under which this consumer should be created.
    - **consumer** (ConsumerCreate): The data required to create a new consumer.
    - **service** (ConsumerService): Injected ConsumerService instance.
    - **kafka_manager_service** (KafkaManagerService): Injected KafkaManagerService instance.
    - **current_user** (UserInDB): The currently authenticated user.

    **Returns**:
    ConsumerResponse: The created consumer object.

    **Raises**:
    HTTPException(404): If the specified Kafka Manager is not found.
    HTTPException(400): If there was an error creating the consumer.
    """
    # Ensure the manager exists before creating a consumer.
    manager = kafka_manager_service.get_manager(manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Kafka Manager not found")

    try:
        consumer_obj = service.create_consumer(manager_id, consumer)
        return consumer_obj
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ConsumerResponse])
def list_consumers(
        manager_id: int,
        service: ConsumerService = Depends(get_consumer_service),
        kafka_manager_service: KafkaManagerService = Depends(get_kafka_manager_service_dependency),
        current_user: UserInDB = Depends(get_current_user)
) -> List[ConsumerResponse]:
    """
    List all Kafka Consumers under a specific Kafka Manager.

    **Parameters**:
    - **manager_id** (int): The ID of the Kafka Manager to list consumers from.
    - **service** (ConsumerService): Injected ConsumerService instance.
    - **kafka_manager_service** (KafkaManagerService): Injected KafkaManagerService instance.
    - **current_user** (UserInDB): The currently authenticated user.

    **Returns**:
    List[ConsumerResponse]: A list of all consumers under the given Kafka Manager.

    **Raises**:
    HTTPException(404): If the specified Kafka Manager is not found.
    """
    # Validate the manager exists.
    manager = kafka_manager_service.get_manager(manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Kafka Manager not found")

    return service.list_consumers(manager_id)


@router.delete("/{consumer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_consumer(
        manager_id: int,
        consumer_id: str,
        service: ConsumerService = Depends(get_consumer_service),
        kafka_manager_service: KafkaManagerService = Depends(get_kafka_manager_service_dependency),
        current_user: UserInDB = Depends(get_current_user)
):
    """
    Delete a Kafka Consumer under a specific Kafka Manager.

    **Parameters**:
    - **manager_id** (int): The ID of the Kafka Manager that owns the consumer.
    - **consumer_id** (str): The ID of the consumer to delete.
    - **service** (ConsumerService): Injected ConsumerService instance.
    - **kafka_manager_service** (KafkaManagerService): Injected KafkaManagerService instance.
    - **current_user** (UserInDB): The currently authenticated user.

    **Returns**:
    None

    **Raises**:
    HTTPException(404): If either the Kafka Manager or the Consumer is not found.
    """
    # Validate the manager exists.
    manager = kafka_manager_service.get_manager(manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Kafka Manager not found")

    success = service.close_consumer(consumer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Consumer not found")
    return
