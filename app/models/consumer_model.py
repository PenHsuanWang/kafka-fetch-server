from pydantic import BaseModel, Field
from typing import Optional


class ConsumerBase(BaseModel):
    consumer_name: str = Field(..., example="MyConsumer")
    topic_name: str = Field(..., example="my_topic")
    group_id: Optional[str] = Field(None, example="my_group")
    # For demonstration, let's assume we also provide broker details here.
    broker_ip: str = Field(..., example="127.0.0.1")
    broker_port: int = Field(..., example=9092)


class ConsumerCreate(ConsumerBase):
    pass


class ConsumerResponse(BaseModel):
    consumer_id: str
    consumer_name: str
    topic_name: str
    group_id: Optional[str]
    manager_id: int
    status: str
