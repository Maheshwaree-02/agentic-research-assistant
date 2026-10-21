import os
import time
import threading
import grpc
import research_pb2
import research_pb2_grpc

TARGET_ADDR = os.environ.get("TARGET_ADDR", "localhost:60201")
NUM_REQUESTS = 20

def handle_request(req_id):
    # This is the Kubernetes gRPC Trap Fix!
    # By using dns:/// and "round_robin", gRPC will balance requests across all 3 pods
    # instead of sending all 20 requests to a single pod.
    options = [("grpc.lb_policy_name", "round_robin")]
    
    try:
        with grpc.insecure_channel(TARGET_ADDR, options=options) as channel:
            stub = research_pb2_grpc.ResearchWorkerServiceStub(channel)
            reply = stub.HandleTask(research_pb2.ResearchTaskRequest(task_id=req_id, query=f"K8s Load Test #{req_id}"))
            print(f"Request {req_id} -> handled by {reply.handled_by}")
    except Exception as e:
        print(f"Request {req_id} failed: {e}")

def main():
    print(f"Starting load test against {TARGET_ADDR}")
    threads = []
    
    for req_id in range(1, NUM_REQUESTS + 1):
        t = threading.Thread(target=handle_request, args=(req_id,))
        threads.append(t)
        t.start()
        time.sleep(0.05) # stagger arrivals like real traffic
        
    for t in threads:
        t.join()
        
    print("Load test complete.")

if __name__ == "__main__":
    main()
