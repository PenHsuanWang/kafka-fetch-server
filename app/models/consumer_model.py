"""SQLAlchemy model for the `consumers` table."""
from sqlalchemy import Column, String, Integer, Enum, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Consumer(Base):
    """
    The Consumer model represents a Kafka consumer configuration.
    """
    __tablename__ = "consumers"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    broker_ip = Column(String, nullable=False)
    broker_port = Column(Integer, nullable=False)
    topic = Column(String, nullable=False)
    consumer_group = Column(String, nullable=False)
    status = Column(Enum("ACTIVE", "INACTIVE", "ERROR", name="consumer_status"), default="INACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), onupdate=text("NOW()"))

    def __repr__(self) -> str:
        """
        Return a string representation of the Consumer model.

        :return: String representation
        :rtype: str
        """
        return f"<Consumer id={self.id} topic={self.topic} status={self.status}>"