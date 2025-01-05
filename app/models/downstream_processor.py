"""SQLAlchemy model for the `downstream_processors` table."""
from sqlalchemy import Column, String, JSON, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class DownstreamProcessor(Base):
    """
    The DownstreamProcessor model represents a single processor configuration
    associated with a Consumer.
    """
    __tablename__ = "downstream_processors"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    consumer_id = Column(UUID(as_uuid=True), ForeignKey("consumers.id"), nullable=False)
    processor_type = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), onupdate=text("NOW()"))

    def __repr__(self) -> str:
        """
        Return a string representation of the DownstreamProcessor model.

        :return: String representation
        :rtype: str
        """
        return (f"<DownstreamProcessor id={self.id} consumer_id={self.consumer_id} "
                f"type={self.processor_type}>")