"""Module defining the MessageExtractor, which consumes messages from Kafka asynchronously."""

import asyncio
from typing import List, Optional, Any

from aiokafka import AIOKafkaConsumer
from app.services.downstream_processors.base_processor import BaseProcessor


class MessageExtractor:
    """
    The MessageExtractor encapsulates a single Kafka consumer instance
    and routes messages to downstream processors.
    """

    def __init__(
        self,
        broker: str,
        topic: str,
        group_id: str,
        processors: List[BaseProcessor],
        client_id: Optional[str] = None
    ) -> None:
        """
        Initialize the MessageExtractor with Kafka config and downstream processors.

        :param broker: The Kafka bootstrap server (host:port)
        :type broker: str
        :param topic: The Kafka topic to subscribe to
        :type topic: str
        :param group_id: The Kafka consumer group ID
        :type group_id: str
        :param processors: A list of downstream processors to handle each message
        :type processors: List[BaseProcessor]
        :param client_id: Optional client ID for the Kafka consumer
        :type client_id: Optional[str]
        """
        self.broker = broker
        self.topic = topic
        self.group_id = group_id
        self.client_id = client_id
        self.processors = processors

        self._consumer: Optional[AIOKafkaConsumer] = None
        self._consume_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        """
        Start consuming messages from Kafka asynchronously.

        :return: None
        :rtype: None
        """
        if not self._consumer:
            self._consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=self.broker,
                group_id=self.group_id,
                client_id=self.client_id,
                auto_offset_reset="earliest",
                enable_auto_commit=True
            )
            await self._consumer.start()
            self._consume_task = asyncio.create_task(self._consume_loop())

    async def _consume_loop(self) -> None:
        """
        The main consumption loop, polling messages from Kafka and dispatching
        them to downstream processors.

        :return: None
        :rtype: None
        """
        try:
            async for msg in self._consumer:
                if self._stop_event.is_set():
                    break
                await self.handle_message(msg)
        except asyncio.CancelledError:
            # Graceful task cancellation
            pass
        except Exception as exc:
            # Log or handle unexpected errors
            print(f"MessageExtractor encountered an error: {exc}")
        finally:
            await self.stop()

    async def handle_message(self, msg: Any) -> None:
        """
        Dispatch a single Kafka message to all downstream processors.

        :param msg: The Kafka message
        :type msg: Any
        :return: None
        :rtype: None
        """
        tasks = [processor.process(msg) for processor in self.processors]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop(self) -> None:
        """
        Stop consuming messages and close downstream processors.

        :return: None
        :rtype: None
        """
        self._stop_event.set()

        if self._consumer:
            await self._consumer.stop()

        if self._consume_task:
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass

        # Close downstream processors if they define a close() method
        for processor in self.processors:
            await processor.close()