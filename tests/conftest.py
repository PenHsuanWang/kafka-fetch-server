# tests/conftest.py

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from app.services.kafka_manager_service import KafkaConsumerManager

# 1) Patch aiokafka to skip real network calls
@pytest_asyncio.fixture(scope="session", autouse=True)
async def mock_kafka_cluster():
    """
    Auto-used fixture that patches AIOKafkaConsumer to skip real network calls.
    """
    with patch("aiokafka.AIOKafkaConsumer.__init__", return_value=None):
        with patch("aiokafka.AIOKafkaConsumer.start", new=AsyncMock()):
            with patch("aiokafka.AIOKafkaConsumer.stop", new=AsyncMock()):
                yield  # Patches remain active until tests finish

# 2) Provide the manager fixture for direct unit tests
@pytest_asyncio.fixture
async def manager():
    """
    A fresh KafkaConsumerManager fixture for each test.
    Clears in-memory data to avoid cross-test contamination.
    """
    mgr = KafkaConsumerManager()

    # Clear everything
    mgr.consumer_store.clear()
    mgr.consumer_data.clear()
    mgr.processor_data.clear()
    mgr.operation_journal.clear()
    mgr.sync_in_progress = False

    yield mgr

    # Optional: any teardown logic, e.g. stopping active consumers.