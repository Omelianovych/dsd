import grpc
from concurrent import futures
import logging_pb2
import logging_pb2_grpc


messages_dict = {}
processed_uuids = set()

class LoggingService(logging_pb2_grpc.LoggingServiceServicer):
    def LogMessage(self, request, context):

        if request.uuid in processed_uuids:
            print("[DUPLICATE]")
            return logging_pb2.LogResponse(success=False)

        messages_dict[request.uuid] = request.message
        processed_uuids.add(request.uuid)
        print(f"[SAVED] {request.uuid}: {request.message}")
        return logging_pb2.LogResponse(success=True)

    def GetAllMessages(self, request, context):
        return logging_pb2.MessagesResponse(messages=list(messages_dict.values()))



def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    logging_pb2_grpc.add_LoggingServiceServicer_to_server(LoggingService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Logging Service is running on port 50051...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
