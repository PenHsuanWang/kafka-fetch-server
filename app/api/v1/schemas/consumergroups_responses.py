# file: app/api/v1/schemas/consumergroups_responses.py

"""
Consumer Groups Responses Schemas
=================================

Defines Pydantic models for returning consumer group monitoring data,
such as group listings and offset details.
"""

from typing import List, Optional
from pydantic import BaseModel


class ConsumerGroupListResponse(BaseModel):
    """
    Response model for listing consumer groups.

    :ivar consumer_groups: A list of consumer group IDs known to the system or cluster.
    :vartype consumer_groups: List[str]
    """
    consumer_groups: List[str]


class PartitionOffsetDetails(BaseModel):
    """
    Details about a single partition's offset in a consumer group.

    :ivar topic: The Kafka topic name.
    :vartype topic: str
    :ivar partition: The partition number.
    :vartype partition: int
    :ivar current_offset: The last committed offset for this group.
    :vartype current_offset: int
    :ivar metadata: Optional metadata associated with the offset commit.
    :vartype metadata: str or None
    """
    topic: str
    partition: int
    current_offset: int
    metadata: Optional[str] = None


class ConsumerGroupOffsetsResponse(BaseModel):
    """
    Response model for a consumer group's offset information.

    :ivar group_id: The Kafka consumer group ID.
    :vartype group_id: str
    :ivar offsets: A list of partition offset details.
    :vartype offsets: List[PartitionOffsetDetails]
    """
    group_id: str
    offsets: List[PartitionOffsetDetails]
