import sys, time, random
from concurrent import futures
import grpc
import research_pb2, research_pb2_grpc

class ResearchWorkerServicer(research_pb2_grpc.ResearchWorkerServiceServicer):
    def __init__(self, name):
        self.name = name

    def HandleTask(self, request, context):
        # Simulate variable processing time for different research queries
        work_time = random.uniform(0.5, 2.5) 
        print(f"[{self.name}] Handling research task {request.task_id}: '{request.query}' "
              f"(will take {work_time:.1f}s)")
        time.sleep(work_time)
        print(f"[{self.name}] Finished task {request.task_id}")
        
        return research_pb2.ResearchTaskReply(
            task_id=request.task_id,
            handled_by=self.name,
            status="done"
        )

def serve(port):
    name = f"ResearcherNode-{port}"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    research_pb2_grpc.add_ResearchWorkerServiceServicer_to_server(ResearchWorkerServicer(name), server)
    server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()
    print(f"{name} listening on 0.0.0.0:{port}")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python worker_server.py <port>")
        sys.exit(1)
    serve(int(sys.argv[1]))
