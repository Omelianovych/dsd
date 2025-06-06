import grpc
from concurrent import futures
import messages_pb2
import messages_pb2_grpc

class MessagesService(messages_pb2_grpc.MessagesServiceServicer):
    def GetStaticMessage(self, request, context):
        return messages_pb2.MessageResponse(message="not implemented yet")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messages_pb2_grpc.add_MessagesServiceServicer_to_server(MessagesService(), server)
    server.add_insecure_port("[::]:50054")
    print("MessagesService gRPC server started on port 50054")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()