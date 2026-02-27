#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : status_submit.py

import time
import threading
from loguru import logger
from concurrent.futures import ThreadPoolExecutor

RABBITMQ_USERNAME = "guest"
RABBITMQ_PASSWORD = "guest"
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672

queue_name = 'KIDO-DEVICE-STATUS-REPORT'
CELERY_BROKER_URL = f"amqp://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

import pika


# TODO: 工程化

#
def process_message(ch, method, properties, body):
    logger.info(f"Thread {threading.current_thread().name} is processing message: {body.decode()}")
    # TODO: 写入redis
    ch.basic_ack(delivery_tag=method.delivery_tag)

def create_connection():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
            return connection
        except Exception as e:
            logger.error(f"Connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)


def create_consumer_thread():
    connection = create_connection()
    channel = connection.channel()

    # 声明队列，确保队列存在
    channel.queue_declare(queue=queue_name, durable=True)

    # 设置消费者回调函数
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=process_message,
        auto_ack=False  # 使用手动确认消息
    )

    try:
        logger.info("Starting to consume messages...")
        channel.start_consuming()
    except Exception as e:
        logger.error(f"Stream connection lost: {e}")
        # 重启消费者
        start_consumers()


def start_consumers():
    # 线程池的大小，可以根据你的需求进行调整
    THREAD_POOL_SIZE = 5
    executor = ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE)
    for i in range(THREAD_POOL_SIZE):
        executor.submit(create_consumer_thread)


if __name__ == "__main__":
    start_consumers()

