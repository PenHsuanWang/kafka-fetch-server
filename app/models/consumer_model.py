# app/models/consumer_model.py
from pydantic import BaseModel, Field
from typing import Optional

class ConsumerBase(BaseModel):
    """
    Base model for Consumers.

    :param consumer_name: A descriptive name for the consumer.
    :type consumer_name: str
    :param topic_name: The topic from which the consumer will read.
    :type topic_name: str
    :param group_id: Optional Kafka consumer group ID.
    :type group_id: str
    :param broker_ip: The IP address of the Kafka broker.
    :type broker_ip: str
    :param broker_port: The port of the Kafka broker.
    :type broker_port: int
    """
    consumer_name: str = Field(..., example="MyConsumer")
    topic_name: str = Field(..., example="my_topic")
    group_id: Optional[str] = Field(None, example="my_group")
    broker_ip: str = Field(..., example="127.0.0.1")
    broker_port: int = Field(..., example=9092)

class ConsumerCreate(ConsumerBase):
    """
    Model for creating a consumer. Inherits from ConsumerBase.
    """
    pass

class ConsumerResponse(BaseModel):
    """
    Response model for a consumer after creation or retrieval.

    :param consumer_id: The unique identifier of the consumer.
    :type consumer_id: str
    :param consumer_name: The name of the consumer.
    :type consumer_name: str
    :param topic_name: The topic from which the consumer reads.
    :type topic_name: str
    :param group_id: The Kafka consumer group ID.
    :type group_id: str, optional
    :param manager_id: The ID of the Kafka Manager under which this consumer operates.
    :type manager_id: int
    :param status: Current status of the consumer (e.g., "running", "stopped").
    :type status: str
    """
    consumer_id: str
    consumer_name: str
    topic_name: str
    group_id: Optional[str]
    manager_id: int
    status: str