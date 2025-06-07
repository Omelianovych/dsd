from fastapi import FastAPI
from aiokafka import AIOKafkaConsumer
import asyncio
import json
from contextlib import asynccontextmanager
from common import consul_utils
import os

messages = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    port = int(os.environ.get("PORT", 50054))

    # Регистрация в Consul
    consul_utils.register_service("messages-service", port, "/health")

    # Получение конфигурации Kafka из Consul
    brokers = consul_utils.get_config_from_kv(
        consul_utils.KAFKA_BROKERS_KV_KEY,
        "host.docker.internal:9092,host.docker.internal:9093,host.docker.internal:9094"
    )
    topic = consul_utils.get_config_from_kv(
        consul_utils.KAFKA_TOPIC_KV_KEY,
        "messages"
    )

    print("Kafka brokers:", brokers)

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=[b.strip() for b in brokers.split(',')],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id="messages-service-group",
        auto_offset_reset='earliest'
    )

    # Стартуем консьюмер
    await consumer.start()

    # Получаем список подписанных топиков (await требуется)
    subscribed = await consumer.topics()
    # group_id хранится в приватном атрибуте _group_id
    print(f"Subscribed to {subscribed} with group {consumer._group_id}")

    app.state.consumer = consumer

    # Запускаем задачу только для чтения сообщений
    asyncio.create_task(consume_messages(consumer))

    yield

    # Корректно останавливаем консьюмера при завершении приложения
    await consumer.stop()

app = FastAPI(lifespan=lifespan)

async def consume_messages(consumer: AIOKafkaConsumer):
    try:
        async for msg in consumer:
            print(f"Received message partition={msg.partition}, offset={msg.offset}")
            messages.append(msg.value)
    except Exception as e:
        print(f"Kafka consumption error: {type(e).__name__}: {e}")

@app.get("/messages")
async def get_messages():
    return messages

@app.get("/health")
async def health_check():
    return {"status": "ok"}
