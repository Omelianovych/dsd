from fastapi import FastAPI
import grpc_client
import logging_pb2
import messages_pb2
import uuid
from pydantic import BaseModel

app = FastAPI()

logging_stub = grpc_client.get_logging_client()
messages_stub = grpc_client.get_messages_client()

class MessageRequest(BaseModel):
    message: str

@app.post("/send")
def send_message(request: MessageRequest):
    message_id = str(uuid.uuid4())
    response = logging_stub.LogMessage(logging_pb2.LogRequest(uuid=message_id, message=request.message))  # Отправляем в logging-service

    return {"success": response.success, "uuid": message_id, "message": request.message}

@app.get("/fetch")
def fetch_messages():
    log_response = logging_stub.GetAllMessages(logging_pb2.Empty())
    msg_response = messages_stub.GetStaticMessage(messages_pb2.Empty())
    combined_response = ", ".join(log_response.messages) + ", " + msg_response.message
    # combined_response = msg_response.message
    return {"messages": combined_response}
