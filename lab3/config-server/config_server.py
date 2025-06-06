from fastapi import FastAPI
from typing import List

app = FastAPI()


logging_service_addresses = [
    "127.0.0.1:50051",
    "127.0.0.1:50052",
    "127.0.0.1:50053"
]


messages_service_addresses = [
    "127.0.0.1:50054"
]

@app.get("/services/logging-service", response_model=List[str])
def get_logging_services():
    return logging_service_addresses

@app.get("/services/messages-service", response_model=List[str])
def get_messages_service():
    return messages_service_addresses
