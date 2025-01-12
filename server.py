"""FastAPI entry point.

Defines the FastAPI `app` and includes routers for the Kafka Consumer Management endpoints.
"""

from fastapi import FastAPI
from app.api.v1.consumers_routes import router as consumers_router
from app.api.v1.consumergroups_routes import router as consumergroups_router


app = FastAPI(title="Kafka Consumer Management Service")

# Include the consumers router under "/consumers".
app.include_router(consumers_router, prefix="/consumers", tags=["Consumers"])
app.include_router(consumergroups_router, prefix="/consumergroups", tags=["ConsumerGroups"])

# Here you could add additional routes, security middlewares, exception handlers, etc.
