# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# # @File    : test_input.py
import json

import pika

# 定义队列名字
queue_name = "KIDO-DEVICE-STATUS-REPORT"

# 创建连接
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host="localhost"
    )
)
# 获取信道
channel = connection.channel()
# 创建一个队列
channel.queue_declare(
    queue=queue_name,  # 队列名称
    durable=True,  # 队列消息是否持久化
)

message = "Hello, World"
# 消息发送
channel.basic_publish(
    exchange="",  # 交换机类型
    routing_key=queue_name,  # 路由key, 执行队列
    body=message.encode("UTF-8") # 消息体
)
print('[x] Send "Hello World!"')

