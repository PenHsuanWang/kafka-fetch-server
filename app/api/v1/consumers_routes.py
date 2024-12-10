from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
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
    return KafkaRepository()

def get_kafka_manager_repository_dependency() -> IKafkaManagerRepository:
    return KafkaManagerRepository()

def get_monitoring_service(
    kafka_repository: IKafkaRepository = Depends(get_kafka_repository_dependency),
    kafka_manager_repository: IKafkaManagerRepository = Depends(get_kafka_manager_repository_dependency)
) -> MonitoringService:
    return MonitoringService(kafka_repository, kafka_manager_repository)

def get_consumer_service(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    kafka_repository: IKafkaRepository = Depends(get_kafka_repository_dependency)
) -> ConsumerService:
    return ConsumerService(kafka_repository, monitoring_service)

def get_kafka_manager_service_dependency(
    kafka_manager_repository: IKafkaManagerRepository = Depends(get_kafka_manager_repository_dependency),
    kafka_repository: IKafkaRepository = Depends(get_kafka_repository_dependency)
) -> KafkaManagerService:
    return KafkaManagerService(kafka_manager_repository, kafka_repository)

def get_user_service_dependency() -> UserService:
    user_repository = UserRepository()
    return UserService(user_repository)

def get_current_user(token: str = Depends(oauth2_scheme), service: UserService = Depends(get_user_service_dependency)) -> UserInDB:
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
):
    """Create a new Kafka Consumer under a specific Kafka Manager."""
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
):
    """List all Kafka Consumers under a specific Kafka Manager."""
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
    """Delete a Kafka Consumer under a specific Kafka Manager."""
    # Validate the manager exists.
    manager = kafka_manager_service.get_manager(manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Kafka Manager not found")

    success = service.close_consumer(consumer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Consumer not found")
    return
