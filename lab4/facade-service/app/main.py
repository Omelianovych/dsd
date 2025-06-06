import asyncio
import json
import os
import random
import uuid
from contextlib import asynccontextmanager

import httpx
import grpc
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


import logging_pb2
import logging_pb2_grpc


CONFIG_SERVER_URL = os.getenv("CONFIG_SERVER_URL", "http://localhost:8002")
KAFKA_TOPIC = "messages"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092,localhost:9093,localhost:9094").split(
    ',')



@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await app.state.producer.start()

    app.state.http_client = httpx.AsyncClient()
    yield
    await app.state.producer.stop()
    await app.state.http_client.aclose()


app = FastAPI(lifespan=lifespan)


class MessageRequest(BaseModel):
    message: str



async def get_service_addresses(service_name: str) -> list[str]:

    try:
        response = await app.state.http_client.get(f"{CONFIG_SERVER_URL}/services/{service_name}")
        response.raise_for_status()
        return response.json()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        print(f"Could not connect to config-server for {service_name}: {e}")
        return []



@app.post("/send")
async def send_message(request: MessageRequest):
    message_id = str(uuid.uuid4())
    message_data = {"uuid": message_id, "message": request.message}


    try:
        value_bytes = json.dumps(message_data).encode('utf-8')
        await app.state.producer.send_and_wait(KAFKA_TOPIC, value=value_bytes)
        print(f"Message {message_id} sent to Kafka.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message to Kafka: {e}")


    try:
        logging_addresses = await get_service_addresses("logging-service")

        with grpc.insecure_channel(random.choice(logging_addresses)) as channel:
            stub = logging_pb2_grpc.LoggingServiceStub(channel)
            stub.LogMessage(logging_pb2.LogRequest(uuid=message_id, message=request.message))
            print(f"gRPC log sent for {message_id} successfully.")
    except Exception as e:
        print(f"CRITICAL: Failed to log message {message_id} to gRPC service: {e}")

    return {"status": "accepted", "uuid": message_id}




async def get_messages_from_messages_service(addresses: list[str]):

    if not addresses:
        return {"error": "No messages-service instances available", "messages": []}

    address = random.choice(addresses)
    try:
        response = await app.state.http_client.get(f"http://{address}/messages")
        response.raise_for_status()

        return {"instance": address, "messages": response.json()}
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return {"error": f"Failed to fetch from {address}: {e}", "messages": []}


async def get_logs_from_logging_service(addresses: list[str]):

    if not addresses:
        return {"error": "No logging-service instances available", "messages": []}


    address = random.choice(addresses)
    try:
        # Використовуємо асинхронний gRPC канал
        async with grpc.aio.insecure_channel(address) as channel:
            stub = logging_pb2_grpc.LoggingServiceStub(channel)
            request = logging_pb2.GetAllMessagesRequest()
            response = await stub.GetAllMessages(request)
            return {"instance": address, "messages": list(response.messages)}
    except grpc.aio.AioRpcError as e:
        return {"error": f"Failed to fetch from gRPC {address}: {e}", "messages": []}

@app.get("/fetch")
async def fetch_messages():

    messages_service_addrs = await get_service_addresses("messages-service")
    logging_service_addrs = await get_service_addresses("logging-service")


    messages_task = asyncio.create_task(get_messages_from_messages_service(messages_service_addrs))
    logging_task = asyncio.create_task(get_logs_from_logging_service(logging_service_addrs))


    messages_result = await messages_task
    logging_result = await logging_task

    return {
        "from_messages_service": {
            "instance": messages_result.get("instance"),
            "messages": messages_result.get("messages", []),
            "count": len(messages_result.get("messages", [])),
        },
        "from_logging_service": {
            "instance": logging_result.get("instance"),
            "messages": logging_result.get("messages", []),  # Только текст сообщений
            "count": len(logging_result.get("messages", [])),
        }
    }