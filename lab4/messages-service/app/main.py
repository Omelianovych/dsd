import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI

# Настройки Kafka
KAFKA_TOPIC = "messages"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092,localhost:9093,localhost:9094").split(
    ',')


messages: List[Dict[str, Any]] = []


async def consume(consumer: AIOKafkaConsumer):
    await consumer.start()
    try:
        async for msg in consumer:
            print(f"Consumed message: {msg.value}")
            messages.append(msg.value)
    finally:
        await consumer.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):

    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="messages_group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest'
    )


    consume_task = asyncio.create_task(consume(consumer))
    yield

    consume_task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/messages")
async def get_messages() -> List[Dict[str, Any]]:

    return messages


@app.get("/health")
async def health_check():
    return {"status": "ok"}