# file: app/api/v1/schemas/consumergroups_requests.py

"""
Consumer Groups Requests Schemas
================================

Defines Pydantic models for any input data relevant to consumer group
monitoring endpoints (e.g., query params).
"""

from pydantic import BaseModel

class ConsumerGroupListQuery(BaseModel):
    """
    Query parameters for listing consumer groups.

    :ivar all_groups: If True, list all known groups in the Kafka cluster.
                      If False, only list the groups used by this service.
    :vartype all_groups: bool
    """
    all_groups: bool = False
