import json
import aio_pika
from typing import List
from core.config.settings import settings
from loguru import logger

from entity.data_track import TrackEventRequest


class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.exchange_name = settings.rabbitmq.DATA_TRACKING_EXCHANGE
        self.queue_name = settings.rabbitmq.DATA_TRACKING_QUEUE
        self.rabbit_url = f"amqp://{settings.rabbitmq.USERNAME}:{settings.rabbitmq.PASSWORD}@{settings.rabbitmq.HOST}:{settings.rabbitmq.PORT}/"

    async def connect(self):
        if not self.connection:
            logger.info(f"Connecting to RabbitMQ at {self.rabbit_url}")
            try:
                self.connection = await aio_pika.connect_robust(self.rabbit_url)
                self.channel = await self.connection.channel()
                self.exchange = await self.channel.declare_exchange(
                    self.exchange_name, aio_pika.ExchangeType.DIRECT
                )

                logger.info(
                    f"Successfully connected to RabbitMQ and declared exchange '{self.exchange_name}' and queue '{self.queue_name}'"
                )
                logger.info(
                    f"Successfully connected to RabbitMQ and declared exchange '{self.exchange_name}'"
                )
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
                raise

    async def publish_events(self, events: List[TrackEventRequest]):
        await self.connect()
        try:
            for event in events:
                message = aio_pika.Message(
                    body=event.model_dump_json().encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                )
                await self.exchange.publish(message, routing_key=self.queue_name)
        except Exception as e:
            logger.error(f"Failed to publish events: {str(e)}")
            raise
