from fastapi import FastAPI
import grpc_client
import logging_pb2
import messages_pb2
import uuid
from pydantic import BaseModel
from tenacity import retry, wait_fixed, stop_after_attempt, RetryError

app = FastAPI()

logging_stub = grpc_client.get_logging_client()
messages_stub = grpc_client.get_messages_client()

class MessageRequest(BaseModel):
    message: str

@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def send_log_message_to_logging_service(message_id: str, message: str):
    try:
        logging_stub = grpc_client.get_logging_client()
        response = logging_stub.LogMessage(logging_pb2.LogRequest(uuid=message_id, message=message))
        return response
    except Exception as e:
        print(e)
        raise

@app.post("/send")
def send_message(request: MessageRequest):
    message_id = str(uuid.uuid4())  # Генерируем UUID
    try:
        response = send_log_message_to_logging_service(message_id, request.message)
        return {"success": response.success, "uuid": message_id, "message": request.message}
    except RetryError as e:
        return {"error": "Failed to send message after multiple attempts", "message": str(e)}

@app.get("/fetch")
def fetch_messages():
    log_response = logging_stub.GetAllMessages(logging_pb2.Empty())
    msg_response = messages_stub.GetStaticMessage(messages_pb2.Empty())
    combined_response = ", ".join(log_response.messages) + ", " + msg_response.message
    return {"messages": combined_response}
