import threading, time
import grpc
import research_pb2, research_pb2_grpc

BACKENDS = ["localhost:60201", "localhost:60202", "localhost:60203"]
NUM_REQUESTS = 9

active = [0] * len(BACKENDS) # active[i] = current in-flight connections to BACKENDS[i]
lock = threading.Lock()

def pick_least_connections():
    """Core strategy: pick the backend with the fewest active
    connections right now, and increment its count immediately so
    the very next request sees the updated picture."""
    with lock:
        idx = active.index(min(active))
        active[idx] += 1
        print(f"[LoadBalancer] Routing -> {BACKENDS[idx]} (active connections now: {active})")
        return idx

def release(idx):
    with lock:
        active[idx] -= 1
        print(f"[LoadBalancer] Released {BACKENDS[idx]} (active connections now: {active})")

def handle_request(req_id):
    idx = pick_least_connections()
    addr = BACKENDS[idx]
    try:
        with grpc.insecure_channel(addr) as channel:
            stub = research_pb2_grpc.ResearchWorkerServiceStub(channel)
            query = f"Analyze distributed system paper #{req_id}"
            reply = stub.HandleTask(research_pb2.ResearchTaskRequest(task_id=req_id, query=query))
            print(f"[LoadBalancer] Request {req_id} -> handled by {reply.handled_by}")
    finally:
        release(idx)

def main():
    print(f"[LoadBalancer] Starting Least Connections Router. Backends: {BACKENDS}")
    threads = []
    
    for req_id in range(1, NUM_REQUESTS + 1):
        t = threading.Thread(target=handle_request, args=(req_id,))
        threads.append(t)
        t.start()
        time.sleep(0.15) # stagger arrivals, like real traffic
        
    for t in threads:
        t.join()
        
    print("\n[LoadBalancer] All research requests processed.")
    print(f"[LoadBalancer] Final active connection counts (should all be 0): {active}")

if __name__ == "__main__":
    main()
