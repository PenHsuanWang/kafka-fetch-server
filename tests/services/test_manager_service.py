# tests/test_manager_service.py

import pytest
import asyncio
from app.api.v1.schemas.consumer_requests import ConsumerCreateRequest, ConsumerUpdateRequest, ProcessorConfig
from app.services.kafka_manager_service import KafkaConsumerManager


@pytest.mark.asyncio
async def test_create_consumer_no_processors(manager: KafkaConsumerManager):
    """
    Creating a consumer with empty processor_configs. Should succeed with 0 processors.
    """
    req = ConsumerCreateRequest(
        broker_ip="localhost",
        broker_port=9092,
        topic="no_proc_topic",
        consumer_group="no_proc_group",
        auto_start=False,
        processor_configs=[]
    )
    result = await manager.create_consumer(req)
    cid = result["consumer_id"]

    assert len(manager.processor_data[cid]) == 0
    assert len(manager.consumer_store[cid].processors) == 0
    assert manager.consumer_data[cid]["status"] == "INACTIVE"


@pytest.mark.asyncio
async def test_create_consumer_invalid_processor_type(manager: KafkaConsumerManager):
    """
    If ProcessorFactory encounters an unknown processor_type, it may raise ValueError.
    """
    req = ConsumerCreateRequest(
        broker_ip="localhost",
        broker_port=9092,
        topic="invalid_type_topic",
        consumer_group="invalid_type_group",
        auto_start=False,
        processor_configs=[
            ProcessorConfig(
                processor_type="unknown_type",
                config={"foo": "bar"}
            )
        ]
    )
    with pytest.raises(ValueError) as excinfo:
        await manager.create_consumer(req)
    assert "Unknown processor type" in str(excinfo.value)


@pytest.mark.asyncio
async def test_start_already_active_consumer(manager: KafkaConsumerManager):
    """
    Start a consumer that is already active. Expect a no-op or consistent data.
    """
    req = ConsumerCreateRequest(
        broker_ip="localhost",
        broker_port=9092,
        topic="already_active",
        consumer_group="already_active_group",
        auto_start=True,
        processor_configs=[]
    )
    created = await manager.create_consumer(req)
    cid = created["consumer_id"]
    assert manager.consumer_data[cid]["status"] == "ACTIVE"

    # Attempt to start again
    started_again = await manager.start_consumer(cid)
    assert started_again["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_stop_consumer_already_inactive(manager: KafkaConsumerManager):
    """
    Stop an already inactive consumer -> no changes or error.
    """
    req = ConsumerCreateRequest(
        broker_ip="localhost",
        broker_port=9092,
        topic="already_inactive",
        consumer_group="already_inactive_group",
        auto_start=False,
        processor_configs=[]
    )
    created = await manager.create_consumer(req)
    cid = created["consumer_id"]
    assert manager.consumer_data[cid]["status"] == "INACTIVE"

    # Stop again
    stopped = await manager.stop_consumer(cid)
    assert stopped["status"] == "INACTIVE"


@pytest.mark.asyncio
async def test_update_remove_all_processors(manager: KafkaConsumerManager):
    """
    Update a consumer to remove all processors -> old extractor stopped, new one with 0 processors.
    If consumer was active, the new extractor restarts.
    """
    req = ConsumerCreateRequest(
        broker_ip="localhost",
        broker_port=9092,
        topic="remove_all_proc",
        consumer_group="remove_all_group",
        auto_start=True,
        processor_configs=[
            ProcessorConfig(processor_type="file_sink", config={"file_path": "/tmp/file.log"})
        ]
    )
    created = await manager.create_consumer(req)
    cid = created["consumer_id"]
    assert manager.consumer_data[cid]["status"] == "ACTIVE"
    assert len(manager.processor_data[cid]) == 1

    upd = ConsumerUpdateRequest(
        processor_configs=[]
    )
    updated = await manager.update_consumer(cid, upd)
    assert updated is not None
    assert updated["status"] == "ACTIVE"
    # Now zero processors
    assert len(updated["processor_configs"]) == 0
    assert len(manager.processor_data[cid]) == 0


@pytest.mark.asyncio
async def test_delete_consumer_nonexistent(manager: KafkaConsumerManager):
    """
    Deleting a nonexistent consumer -> returns False
    """
    success = await manager.delete_consumer("random-nonexistent-id")
    assert success is False


@pytest.mark.asyncio
async def test_parallel_calls_same_request(manager: KafkaConsumerManager):
    """
    Demonstrate concurrency: two tasks calling create_consumer with same request
    at roughly the same time. Each gets a unique consumer_id though, since manager uses UUID.
    """
    req = ConsumerCreateRequest(
        broker_ip="localhost",
        broker_port=9092,
        topic="parallel_topic",
        consumer_group="parallel_group",
        auto_start=False,
        processor_configs=[]
    )

    async def create():
        return await manager.create_consumer(req)

    t1 = asyncio.create_task(create())
    t2 = asyncio.create_task(create())
    results = await asyncio.gather(t1, t2, return_exceptions=True)

    cid1 = results[0]["consumer_id"]
    cid2 = results[1]["consumer_id"]
    assert cid1 != cid2
    assert cid1 in manager.consumer_data
    assert cid2 in manager.consumer_data


@pytest.mark.asyncio
async def test_manager_sync_with_db_journal(manager: KafkaConsumerManager):
    """
    Example test for the sync_with_db method, ensuring the operation_journal is consumed.
    Here, we won't have a real DB; we just confirm the journal gets cleared.
    """
    # Create consumer -> OP_CREATE is recorded
    req = ConsumerCreateRequest(
        broker_ip="localhost",
        broker_port=9092,
        topic="journal_topic",
        consumer_group="journal_group",
        auto_start=False,
        processor_configs=[]
    )
    created = await manager.create_consumer(req)
    cid = created["consumer_id"]

    # We expect OP_CREATE in the journal
    assert len(manager.operation_journal) == 1
    await manager.sync_with_db()
    # Once synced, the journal should be empty
    assert len(manager.operation_journal) == 0