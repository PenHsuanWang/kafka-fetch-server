"""Response schemas (Pydantic) for consumer-related operations."""
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class ProcessorDetails(BaseModel):
    """
    Details of a downstream processor in a consumer response.
    """
    id: str
    processor_type: str
    config: dict
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ConsumerResponse(BaseModel):
    """
    Response model for a consumer resource.
    """
    consumer_id: str
    broker_ip: str
    broker_port: int
    topic: str
    consumer_group: str
    status: str
    processor_configs: List[ProcessorDetails] = []
    created_at: Optional[datetime]
    updated_at: Optional[datetime]