import random
import requests
import grpc
import logging_pb2_grpc
import logging_pb2
import messages_pb2_grpc
import messages_pb2
from fastapi import FastAPI
from pydantic import BaseModel
import uuid
from tenacity import retry, wait_fixed, stop_after_attempt, RetryError

def get_service_addresses(service_name: str):
    # Отримання IP з config-server
    response = requests.get(f"http://127.0.0.1:8002/services/{service_name}")
    response.raise_for_status()
    return response.json()


def get_grpc_stub_random(service_name: str, stub_class, pb2_grpc_module, port_field="50051"):
    addresses = get_service_addresses(service_name)
    random.shuffle(addresses)

    last_error = None

    for address in addresses:
        try:
            print(f"Trying {service_name} instance at {address}...")
            channel = grpc.insecure_channel(address)
            grpc.channel_ready_future(channel).result(timeout=2)
            stub = getattr(pb2_grpc_module, stub_class)(channel)
            return stub, channel
        except Exception as e:
            print(f"Failed to connect to {address}: {e}")
            last_error = e
            continue

    raise RuntimeError(f"All instances of {service_name} are unavailable. Last error: {last_error}")




app = FastAPI()

class MessageRequest(BaseModel):
    message: str

@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def send_log_message_to_logging_service(message_id: str, message: str):
    try:
        stub, channel = get_grpc_stub_random("logging-service", "LoggingServiceStub", logging_pb2_grpc)
        response = stub.LogMessage(logging_pb2.LogRequest(uuid=message_id, message=message))
        channel.close()
        return response
    except Exception as e:
        print(e)
        raise

@app.post("/send")
def send_message(request: MessageRequest):
    message_id = str(uuid.uuid4())
    try:
        response = send_log_message_to_logging_service(message_id, request.message)
        return {"success": response.success, "uuid": message_id, "message": request.message}
    except RetryError as e:
        return {"error": "Failed to send message after multiple attempts", "message": str(e)}

@app.get("/fetch")
def fetch_messages():
    # Logging Service
    logging_stub, logging_channel = get_grpc_stub_random("logging-service", "LoggingServiceStub", logging_pb2_grpc)
    log_response = logging_stub.GetAllMessages(logging_pb2.Empty())
    logging_channel.close()

    messages_stub, messages_channel = get_grpc_stub_random("messages-service", "MessagesServiceStub", messages_pb2_grpc)
    msg_response = messages_stub.GetStaticMessage(messages_pb2.Empty())
    messages_channel.close()

    combined_response = ", ".join(log_response.messages) + ", " + msg_response.message
    return {"messages": combined_response}