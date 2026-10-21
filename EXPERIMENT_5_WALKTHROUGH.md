# Experiment 5: Simulate & Resolve Deadlocks (AutoSave vs Final Submission)
**Course:** Distributed Computing Lab (DC Lab) — B.E. Semester VII  
**Department:** Information Technology  

---

## 1. Experiment Overview & Objective

| Parameter | Details |
|---|---|
| **Experiment No.** | 5 |
| **Title** | Simulate & Resolve Deadlocks using Central Lock Manager (Wait-For Graph) |
| **Domain** | Distributed Synchronization & Deadlock Management |
| **Communication Layer** | gRPC (HTTP/2 with Protocol Buffers) |
| **Competing Nodes** | Node 1 (`autosave`) and Node 2 (`submission`) |
| **Shared Resources** | `draft` lock and `submission` lock |

### Aim
To design, implement, and analyze a distributed locking mechanism over gRPC that:
1. **Simulates a Circular-Wait Deadlock:** Demonstrates how concurrent processes requesting multiple shared resources in reverse order enter an indefinite block (deadlock).
2. **Detects & Resolves Deadlocks:** Implements a centralized **Wait-For Graph (WFG)** with depth-first cycle detection (`_would_cycle`) to detect potential deadlock cycles before blocking and preemptively abort/retry the offending request.

---

## 2. Core Concepts & Architectural Theory

```
                       ┌─────────────────────────┐
                       │   Central Lock Manager  │
                       │     (Port: 60100)       │
                       │  • Tracks Lock Holders  │
                       │  • Maintains WFG        │
                       │  • Cycle Detection      │
                       └────────────┬────────────┘
                                    │
               gRPC Acquire/Release │ gRPC Acquire/Release
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
        ┌─────────────────────────┐   ┌─────────────────────────┐
        │  Worker 1: AutoSave     │   │ Worker 2: Submission    │
        │  Lock Order:            │   │ Lock Order:             │
        │  1. 'draft'             │   │ 1. 'submission'         │
        │  2. 'submission'        │   │ 2. 'draft'              │
        └─────────────────────────┘   └─────────────────────────┘
```

### The Deadlock Scenario (Circular Wait)
- **AutoSave (Node 1):** Grabs `draft` lock $\rightarrow$ sleeps 1.5s $\rightarrow$ attempts to acquire `submission` lock.
- **Final Submission (Node 2):** Grabs `submission` lock $\rightarrow$ sleeps 1.5s $\rightarrow$ attempts to acquire `draft` lock.
- **The Conflict:** Node 1 holds `draft` and waits for `submission` (held by Node 2). Node 2 holds `submission` and waits for `draft` (held by Node 1). A cycle $(1 \to 2 \to 1)$ is formed.

### Detection Mechanism (Wait-For Graph Cycle Traversal)
When a request arrives for an already-held resource, before placing the requester on a blocking `Condition.wait()`, the manager walks the wait-for chain:
$$\text{Holder} \xrightarrow{\text{waits for}} \text{Resource} \xrightarrow{\text{owned by}} \text{Owner} \xrightarrow{\text{waits for}} \dots$$
If the traversal leads back to the $\text{Holder}$, a cycle is detected. The manager immediately returns `granted=False (deadlock-abort)` to break the circular dependency.

---

## 3. Step-by-Step Code Setup

All files are located in `C:/Users/bharg/researchpilot-ai/grpc_experiment`.

### Step 1: Protocol Buffer Definition (`proto/research.proto`)
Append the `LockService` RPC definition:
```protobuf
// --- Experiment 5: Deadlock simulation & resolution ---
service LockService {
  rpc AcquireLock (LockRequest) returns (LockReply);
  rpc ReleaseLock (LockRequest) returns (LockReply);
}

message LockRequest {
  string resource_id = 1;
  int32 holder_id = 2;
  int32 timestamp = 3;
}

message LockReply {
  bool granted = 1;
  string message = 2;
}
```

### Step 2: Compile Protocol Buffers
Generate Python stubs (`research_pb2.py` and `research_pb2_grpc.py`):
```bash
python -m grpc_tools.protoc -I=proto --python_out=. --grpc_python_out=. proto/research.proto
```

### Step 3: Central Lock Manager (`lock_manager.py`)
Implements mutex locks, condition variables, wait-for mappings, and cycle detection:
```python
import sys, threading, time
from concurrent import futures
import grpc
import research_pb2, research_pb2_grpc

DETECT = (len(sys.argv) > 1 and sys.argv[1] == "detect")

class LockManager(research_pb2_grpc.LockServiceServicer):
    def __init__(self):
        self.mutex = threading.Lock()
        self.locks = {"draft": None, "submission": None}
        self.wait_for = {} # holder_id -> resource_id
        self.conditions = {"draft": threading.Condition(), "submission": threading.Condition()}

    def _would_cycle(self, holder, resource):
        visited = set()
        current_resource = resource
        while True:
            owner = self.locks.get(current_resource)
            if owner is None or owner == holder:
                return owner == holder
            if owner in visited:
                return False
            visited.add(owner)
            current_resource = self.wait_for.get(owner)
            if current_resource is None:
                return False

    def AcquireLock(self, request, context):
        resource, holder, ts = request.resource_id, request.holder_id, request.timestamp
        cond = self.conditions[resource]

        with cond:
            with self.mutex:
                owner = self.locks.get(resource)
                if owner is None:
                    self.locks[resource] = holder
                    self.wait_for.pop(holder, None)
                    return research_pb2.LockReply(granted=True, message="granted")
                
                if DETECT and self._would_cycle(holder, resource):
                    print(f"[LockManager] DEADLOCK DETECTED: Node-{holder} -> '{resource}' "
                          f"(held by Node-{owner}) would close a cycle. Aborting Node-{holder}.")
                    return research_pb2.LockReply(granted=False, message="deadlock-abort")
                
                self.wait_for[holder] = resource
                print(f"[LockManager] Node-{holder} WAITING for '{resource}' (held by Node-{owner})")
            
            while True:
                with self.mutex:
                    owner = self.locks.get(resource)
                    if owner is None:
                        self.locks[resource] = holder
                        self.wait_for.pop(holder, None)
                        return research_pb2.LockReply(granted=True, message="granted-after-wait")
                cond.wait(timeout=1)

    def ReleaseLock(self, request, context):
        resource, holder = request.resource_id, request.holder_id
        cond = self.conditions[resource]

        with cond:
            with self.mutex:
                if self.locks.get(resource) == holder:
                    self.locks[resource] = None
            cond.notify_all()
        return research_pb2.LockReply(granted=True, message="released")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    research_pb2_grpc.add_LockServiceServicer_to_server(LockManager(), server)
    server.add_insecure_port("localhost:60100")
    server.start()
    print(f"LockManager started on localhost:60100 (deadlock detection = {DETECT})")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
```

### Step 4: Worker Process (`worker.py`)
Simulates competing roles with reverse acquisition order:
```python
import sys, time, grpc
import research_pb2, research_pb2_grpc

def acquire(stub, resource, holder, ts):
    reply = stub.AcquireLock(research_pb2.LockRequest(resource_id=resource, holder_id=holder, timestamp=ts))
    print(f"Node-{holder}: '{resource}' -> granted={reply.granted} ({reply.message})")
    return reply.granted

def release(stub, resource, holder):
    stub.ReleaseLock(research_pb2.LockRequest(resource_id=resource, holder_id=holder, timestamp=0))

def run(node_id, first, second):
    ts = node_id
    with grpc.insecure_channel("localhost:60100") as channel:
        stub = research_pb2_grpc.LockServiceStub(channel)
        held = []
        
        if acquire(stub, first, node_id, ts):
            held.append(first)
            time.sleep(1.5) # window for contention
            
            if acquire(stub, second, node_id, ts):
                held.append(second)
            else:
                print(f"Node-{node_id}: ABORTED -- releasing held locks and retrying")
                for r in held:
                    release(stub, r, node_id)
                held = []
                time.sleep(1)
                
                # Retry acquisition
                if acquire(stub, second, node_id, ts):
                    held.append(second)
                    if acquire(stub, first, node_id, ts):
                        held.append(first)
                        
        time.sleep(0.5)
        for r in held:
            release(stub, r, node_id)
        print(f"Node-{node_id}: DONE")

if __name__ == "__main__":
    node_id, role = int(sys.argv[1]), sys.argv[2]
    if role == "autosave":
        run(node_id, "draft", "submission")
    else:
        run(node_id, "submission", "draft")
```

---

## 4. Manual Execution Guide

### Preparation: Open 3 Separate Git Bash Windows
In all 3 windows, navigate to the experiment folder:
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
```

---

### Part A: Run 1 — Simulate the Deadlock (Without Detection)

#### Step 1: Start Central Lock Manager (Terminal 1)
```bash
python -u lock_manager.py
```
*Output:*
```text
LockManager started on localhost:60100 (deadlock detection = False)
```

#### Step 2: Prepare Workers (Terminals 2 & 3)
- In **Terminal 2**, type (do NOT press Enter yet):
  ```bash
  python worker.py 1 autosave
  ```
- In **Terminal 3**, type (do NOT press Enter yet):
  ```bash
  python worker.py 2 submission
  ```

#### Step 3: Launch Both Concurrently
Press **Enter on Terminal 2**, then immediately (**within 1 second**) press **Enter on Terminal 3**.

#### Step 4: Observe Deadlock
- **Terminal 1 (Lock Manager):**
  ```text
  [LockManager] Node-1 WAITING for 'submission' (held by Node-2)
  [LockManager] Node-2 WAITING for 'draft' (held by Node-1)
  ```
- **Terminals 2 & 3:** Both hang indefinitely waiting for the second lock.
- **Stop:** Press `Ctrl + C` in all 3 terminals.

---

### Part B: Run 2 — Detect & Resolve Deadlock (With Detection)

#### Step 1: Start Central Lock Manager in Detect Mode (Terminal 1)
```bash
python -u lock_manager.py detect
```
*Output:*
```text
LockManager started on localhost:60100 (deadlock detection = True)
```

#### Step 2: Launch Workers Concurrently (Terminals 2 & 3)
- In **Terminal 2**:
  ```bash
  python worker.py 1 autosave
  ```
- In **Terminal 3** (press Enter immediately after Terminal 2):
  ```bash
  python worker.py 2 submission
  ```

#### Step 3: Observe Resolution
- **Terminal 1 (Lock Manager):**
  ```text
  [LockManager] Node-1 WAITING for 'submission' (held by Node-2)
  [LockManager] DEADLOCK DETECTED: Node-2 -> 'draft' (held by Node-1) would close a cycle. Aborting Node-2.
  ```
- **Terminal 2 (Node 1 - AutoSave):**
  ```text
  Node-1: 'draft' -> granted=True (granted)
  Node-1: 'submission' -> granted=True (granted-after-wait)
  Node-1: DONE
  ```
- **Terminal 3 (Node 2 - Final Submission):**
  ```text
  Node-2: 'submission' -> granted=True (granted)
  Node-2: 'draft' -> granted=False (deadlock-abort)
  Node-2: ABORTED -- releasing held locks and retrying
  Node-2: 'draft' -> granted=True (granted)
  Node-2: 'submission' -> granted=True (granted)
  Node-2: DONE
  ```

---

## 5. Conclusion (For DC Lab Record)

> In this experiment, a centralized deadlock simulation and detection system was developed using gRPC. By simulating conflicting resource acquisition orders between concurrent processes (`autosave` vs `submission`), the emergence of a circular wait condition was demonstrated. Utilizing a **Wait-For Graph (WFG)** with depth-first cycle traversal, the Central Lock Manager successfully identified potential deadlocks prior to blocking, preempted the younger transaction, and facilitated lock release and retry, thereby establishing deadlock-free distributed synchronization.
