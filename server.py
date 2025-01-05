"""FastAPI entry point.

Defines the FastAPI `app` and includes routers for the Kafka Consumer Management endpoints.
"""

from fastapi import FastAPI
from app.api.consumers import router as consumers_router


app = FastAPI(title="Kafka Consumer Management Service")

# Include the consumers router under "/consumers".
app.include_router(consumers_router, prefix="/consumers", tags=["Consumers"])

# Here you could add additional routes, security middlewares, exception handlers, etc.
