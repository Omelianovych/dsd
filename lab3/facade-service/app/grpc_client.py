import grpc
import logging_pb2_grpc
import messages_pb2_grpc

LOGGING_SERVICE_ADDRESS = "localhost:50051"
MESSAGES_SERVICE_ADDRESS = "localhost:50052"


def get_logging_client():
    channel = grpc.insecure_channel(LOGGING_SERVICE_ADDRESS)
    return logging_pb2_grpc.LoggingServiceStub(channel)

def get_messages_client():
    channel = grpc.insecure_channel(MESSAGES_SERVICE_ADDRESS)
    return messages_pb2_grpc.MessagesServiceStub(channel)