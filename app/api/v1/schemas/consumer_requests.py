"""Request schemas (Pydantic) for consumer-related operations."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ProcessorConfig(BaseModel):
    """
    Configuration for a single downstream processor.
    """
    processor_type: str = Field(..., description="Type of the processor (e.g. file_sink, database_sync).")
    config: dict = Field(..., description="Arbitrary config for the processor (JSON).")


class ConsumerCreateRequest(BaseModel):
    """
    Request body for creating a new consumer.
    """
    broker_ip: str
    broker_port: int
    topic: str
    consumer_group: str
    auto_start: bool = False
    processor_configs: List[ProcessorConfig] = Field(default_factory=list)


class ConsumerUpdateRequest(BaseModel):
    """
    Request body for updating an existing consumer.
    """
    broker_ip: Optional[str] = None
    broker_port: Optional[int] = None
    topic: Optional[str] = None
    processor_configs: Optional[List[ProcessorConfig]] = None
