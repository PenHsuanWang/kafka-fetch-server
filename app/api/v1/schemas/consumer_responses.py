"""
Consumer Responses Schemas
==========================

Defines Pydantic models for returning response data about Kafka
consumers and their downstream processors.

:module: consumer_responses
:author: Your Name
:created: 2025-01-01
:seealso: app.api.v1.schemas.consumer_requests
"""

from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime


class ProcessorDetails(BaseModel):
    """
    Details of a downstream processor in a consumer response.

    :ivar id: UUID of the processor.
    :vartype id: str
    :ivar processor_type: The type of the processor (e.g. 'file_sink', 'database_sync').
    :vartype processor_type: str
    :ivar config: A dictionary of config parameters for the processor.
    :vartype config: dict
    :ivar created_at: Timestamp of creation.
    :vartype created_at: datetime or None
    :ivar updated_at: Timestamp of last update.
    :vartype updated_at: datetime or None
    """

    id: str
    processor_type: str
    config: Dict[str, str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConsumerResponse(BaseModel):
    """
    Response model for a consumer resource.

    :ivar consumer_id: UUID of the consumer.
    :vartype consumer_id: str
    :ivar broker_ip: Broker IP address for this consumer.
    :vartype broker_ip: str
    :ivar broker_port: Broker port number for this consumer.
    :vartype broker_port: int
    :ivar topic: Kafka topic that is being consumed.
    :vartype topic: str
    :ivar consumer_group: Consumer group identifier for this consumer.
    :vartype consumer_group: str
    :ivar status: Current status of the consumer (e.g., 'ACTIVE', 'INACTIVE').
    :vartype status: str
    :ivar processor_configs: List of processors attached to this consumer.
    :vartype processor_configs: List[ProcessorDetails]
    :ivar created_at: Timestamp of consumer creation.
    :vartype created_at: datetime or None
    :ivar updated_at: Timestamp of last update.
    :vartype updated_at: datetime or None
    """

    consumer_id: str
    broker_ip: str
    broker_port: int
    topic: str
    consumer_group: str
    status: str
    processor_configs: List[ProcessorDetails] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
