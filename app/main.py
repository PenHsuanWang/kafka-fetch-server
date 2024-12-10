# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from app.api.v1 import consumers, kafka_managers, monitoring, users
from app.core.config import settings
from app.repositories.kafka_repository import KafkaRepository
from app.repositories.kafka_manager_repository import KafkaManagerRepository
from app.repositories.user_repository import UserRepository
from app.services.monitoring_service import MonitoringService
from app.services.consumer_service import ConsumerService
from app.services.kafka_manager_service import KafkaManagerService
from app.services.user_service import UserService
from app.core.security import SECRET_KEY, ALGORITHM
from jose import JWTError, jwt
from app.models.user import TokenData, UserInDB
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
from app.core.logger import logger

# Initialize shared instances
kafka_repository = KafkaRepository()
kafka_manager_repository = KafkaManagerRepository()
monitoring_service = MonitoringService(kafka_repository, kafka_manager_repository)
consumer_service = ConsumerService(kafka_repository, monitoring_service)
kafka_manager_service = KafkaManagerService(kafka_manager_repository, kafka_repository)
user_repository = UserRepository()
user_service = UserService(user_repository)

app = FastAPI(
    title="Kafka Consumer Service",
    description="API to manage Kafka managers, consumers, and monitor their status",
    version="2.0.0"
)

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(kafka_managers.router, prefix="/api/v1/kafka-managers", tags=["kafka-managers"])
app.include_router(consumers.router, prefix="/api/v1/kafka-managers/{manager_id}/consumers", tags=["consumers"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = user_service.get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

@app.on_event("shutdown")
def shutdown_event():
    # Close all consumers gracefully
    consumers = kafka_repository.get_all_consumers()
    for consumer in consumers.values():
        consumer.close()
    logger.info("Application shutdown: All consumers closed gracefully.")