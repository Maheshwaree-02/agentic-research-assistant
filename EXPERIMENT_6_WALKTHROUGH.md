# Experiment 6: Least Connections Load Balancing
**Course:** Distributed Computing Lab (DC Lab)  
**Project Integration:** ResearchPilot AI

---

## 1. Experiment Overview & Objective

| Parameter | Details |
|---|---|
| **Experiment No.** | 6 |
| **Title** | General Purpose Load Balancing Strategy: Least Connections |
| **Goal** | Implement a Load Balancer that routes incoming gRPC requests to whichever backend currently has the fewest active (in-flight) connections. |
| **Why Least Connections?** | Round Robin blindly alternates traffic, assuming all requests take the same amount of time. In our `ResearchPilot` scenario, some research tasks take 0.5s, while others take 2.5s. Least Connections avoids piling new requests onto a server that is stuck processing a heavy task, adapting dynamically to real-time load. |

---

## 2. Step-by-Step Code Setup

All files are located in `C:/Users/bharg/researchpilot-ai/grpc_experiment`. I have adapted the experiment to use a `ResearchWorkerService` instead of a generic worker to match your project style!

### Step 1: Protocol Buffer Definition (`proto/research.proto`)
I appended the following `ResearchWorkerService` to your existing `.proto` file:
```protobuf
// --- Experiment 6: Least Connections Load Balancing ---
service ResearchWorkerService {
  rpc HandleTask (ResearchTaskRequest) returns (ResearchTaskReply);
}

message ResearchTaskRequest {
  int32 task_id = 1;
  string query = 2;
}

message ResearchTaskReply {
  int32 task_id = 1;
  string handled_by = 2;
  string status = 3;
}
```

### Step 2: Compile Protocol Buffers
Generated the new Python stubs:
```bash
python -m grpc_tools.protoc -I=proto --python_out=. --grpc_python_out=. proto/research.proto
```

### Step 3: Backend Worker Node (`worker_server.py`)
Each backend takes a port number and simulates variable-length research tasks (0.5 to 2.5 seconds).
```python
import sys, time, random
from concurrent import futures
import grpc
import research_pb2, research_pb2_grpc

class ResearchWorkerServicer(research_pb2_grpc.ResearchWorkerServiceServicer):
    def __init__(self, name):
        self.name = name

    def HandleTask(self, request, context):
        work_time = random.uniform(0.5, 2.5) 
        print(f"[{self.name}] Handling research task {request.task_id}: '{request.query}' (will take {work_time:.1f}s)")
        time.sleep(work_time)
        print(f"[{self.name}] Finished task {request.task_id}")
        return research_pb2.ResearchTaskReply(task_id=request.task_id, handled_by=self.name, status="done")

def serve(port):
    name = f"ResearcherNode-{port}"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    research_pb2_grpc.add_ResearchWorkerServiceServicer_to_server(ResearchWorkerServicer(name), server)
    server.add_insecure_port(f"localhost:{port}")
    server.start()
    print(f"{name} listening on localhost:{port}")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve(int(sys.argv[1]))
```

### Step 4: The Load Balancer (`load_balancer.py`)
Maintains an `active` array representing the current number of in-flight connections per backend. It uses a thread-safe lock to find the `min(active)`, increments it before dispatching, and decrements it in a `finally` block when the RPC returns.
```python
import threading, time
import grpc
import research_pb2, research_pb2_grpc

BACKENDS = ["localhost:60201", "localhost:60202", "localhost:60203"]
NUM_REQUESTS = 9

active = [0] * len(BACKENDS)
lock = threading.Lock()

def pick_least_connections():
    with lock:
        idx = active.index(min(active))
        active[idx] += 1
        print(f"[LB] Routing -> {BACKENDS[idx]} (active connections now: {active})")
        return idx

def release(idx):
    with lock:
        active[idx] -= 1
        print(f"[LB] Released {BACKENDS[idx]} (active connections now: {active})")

def handle_request(req_id):
    idx = pick_least_connections()
    try:
        with grpc.insecure_channel(BACKENDS[idx]) as channel:
            stub = research_pb2_grpc.ResearchWorkerServiceStub(channel)
            reply = stub.HandleTask(research_pb2.ResearchTaskRequest(task_id=req_id, query=f"Analyze paper #{req_id}"))
            print(f"[LB] Request {req_id} -> handled by {reply.handled_by}")
    finally:
        release(idx)

def main():
    threads = []
    for req_id in range(1, NUM_REQUESTS + 1):
        t = threading.Thread(target=handle_request, args=(req_id,))
        threads.append(t)
        t.start()
        time.sleep(0.15) # stagger arrivals
        
    for t in threads:
        t.join()
        
    print(f"[LB] Final active connection counts (should all be 0): {active}")

if __name__ == "__main__":
    main()
```

---

## 3. Manual Execution Guide (How to run it)

You will need **4 Git Bash terminals** to demonstrate this.

### Step 1: Start Backend 1 (Terminal 1)
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python -u worker_server.py 60201
```

### Step 2: Start Backend 2 (Terminal 2)
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python -u worker_server.py 60202
```

### Step 3: Start Backend 3 (Terminal 3)
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python -u worker_server.py 60203
```

*(Ensure all 3 terminals print `ResearcherNode-6020x listening on localhost:6020x`)*

### Step 4: Run the Load Balancer (Terminal 4)
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python load_balancer.py
```

### What to check in the output:
1. **Dynamic Routing:** Watch the `[LB] Routing ->` logs in Terminal 4. It does **not** follow a strict `1->2->3->1->2->3` Round Robin pattern. Instead, it looks at the `[active connections now]` array and always routes to the node with the lowest number.
2. **Variable Processing:** If you look at Terminals 1–3, you will see some research tasks take 0.5s while others take 2.5s.
3. **No Leaks:** At the very end of Terminal 4, it prints `Final active connection counts (should all be 0): [0, 0, 0]`, proving every connection was safely released in the `finally` block!
