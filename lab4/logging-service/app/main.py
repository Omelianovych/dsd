import grpc
from concurrent import futures
import logging_pb2
import logging_pb2_grpc
import hazelcast
import os


hz = hazelcast.HazelcastClient(
    cluster_members=[
        "127.0.0.1:5701",
        "127.0.0.1:5702",
        "127.0.0.1:5703",
    ]
)
log_map = hz.get_map("log_messages").blocking()
uuid_set = hz.get_set("processed_uuids").blocking()

class LoggingService(logging_pb2_grpc.LoggingServiceServicer):
    def LogMessage(self, request, context):

        if uuid_set.contains(request.uuid):
            print("[DUPLICATE]", request.uuid)
            return logging_pb2.LogResponse(success=False)

        # Сохраняем сообщение в Hazelcast map
        log_map.put(request.uuid, request.message)
        uuid_set.add(request.uuid)

        print(f"[SAVED] {request.uuid}: {request.message}")
        return logging_pb2.LogResponse(success=True)

    def GetAllMessages(self, request, context):
        # Получаем все значения из distributed map
        all_messages = log_map.values()
        return logging_pb2.MessagesResponse(messages=list(all_messages))


def serve():
    port = os.getenv("LOGGING_SERVICE_PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    logging_pb2_grpc.add_LoggingServiceServicer_to_server(LoggingService(), server)
    server.add_insecure_port(f"[::]:{port}")
    print(f"Logging Service is running on port {port}...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
