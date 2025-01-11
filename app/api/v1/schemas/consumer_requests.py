"""
Consumer Requests Schemas
=========================

Defines Pydantic models for handling incoming request data related to Kafka
consumers, including creation and update operations.

:module: consumer_requests
:author: Your Name
:created: 2025-01-01
:seealso: app.api.v1.schemas.consumer_responses
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, conint


class ProcessorConfig(BaseModel):
    """
    Configuration for a single downstream processor.

    :ivar processor_type: Type of the processor (e.g. 'file_sink', 'database_sync').
    :vartype processor_type: str
    :ivar config: Arbitrary config parameters in a dictionary form (e.g. JSON).
    :vartype config: dict
    """

    processor_type: str = Field(
        ...,
        description="Type of the processor (e.g. file_sink, database_sync)."
    )
    config: Dict[str, str] = Field(
        ...,
        description="Arbitrary config for the processor (JSON)."
    )


class ConsumerCreateRequest(BaseModel):
    """
    Request body for creating a new Kafka consumer.

    :ivar broker_ip: IP address of the Kafka broker.
    :vartype broker_ip: str
    :ivar broker_port: Port of the Kafka broker (must be > 0).
    :vartype broker_port: int
    :ivar topic: Name of the Kafka topic to consume from.
    :vartype topic: str
    :ivar consumer_group: Consumer group identifier.
    :vartype consumer_group: str
    :ivar auto_start: If True, the consumer will automatically start upon creation.
    :vartype auto_start: bool
    :ivar processor_configs: List of downstream processor configurations.
    :vartype processor_configs: List[ProcessorConfig]
    """

    broker_ip: str
    # Use conint(gt=0) to ensure broker_port must be greater than 0
    broker_port: conint(gt=0) = Field(
        ...,
        description="Port of the Kafka broker (must be a positive integer)."
    )
    topic: str
    consumer_group: str
    auto_start: bool = False
    processor_configs: List[ProcessorConfig] = Field(default_factory=list)


class ConsumerUpdateRequest(BaseModel):
    """
    Request body for updating an existing consumer.

    :ivar broker_ip: (Optional) New IP address for the broker.
    :vartype broker_ip: str or None
    :ivar broker_port: (Optional) New port for the broker (must be > 0 if provided).
    :vartype broker_port: int or None
    :ivar topic: (Optional) New topic to consume from.
    :vartype topic: str or None
    :ivar processor_configs: (Optional) New list of downstream processor configs.
    :vartype processor_configs: List[ProcessorConfig] or None
    """

    broker_ip: Optional[str] = None
    # Similarly, you can constrain update requests if you want
    broker_port: Optional[conint(gt=0)] = None
    topic: Optional[str] = None
    processor_configs: Optional[List[ProcessorConfig]] = None
