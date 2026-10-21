# Experiment 7: Eventual Consistency (Gossip + LWW)
**Course:** Distributed Computing Lab (DC Lab)  
**Project Integration:** ResearchPilot AI

---

## 1. Experiment Overview & Objective

| Parameter | Details |
|---|---|
| **Experiment No.** | 7 |
| **Title** | Eventual Consistency via Gossip Replication + Last-Write-Wins (LWW) |
| **Goal** | Implement a replicated data store for `ResearchPilot` reports where writes are accepted locally and immediately (favoring availability), then propagated to other replicas asynchronously. |
| **Conflict Resolution** | When two replicas receive conflicting concurrent writes for the same report topic, resolve the conflict deterministically using **Last-Write-Wins (LWW)** based on Lamport logical timestamps. |

### Why Eventual Consistency?
Strong consistency (like our Deadlock locking experiment) is safe but slow and less available—if one replica goes down, writes block. Eventual consistency trades that safety for speed. A client writing a Research Report never waits on other replicas, and the system tolerates temporary disagreement as long as it's guaranteed to converge once things settle down.

---

## 2. Step-by-Step Code Setup

All files are located in `C:/Users/bharg/researchpilot-ai/grpc_experiment`. I adapted the experiment to use a `ReportReplicaService` simulating a distributed cache for our Research Reports!

### Step 1: Protocol Buffer Definition (`proto/research.proto`)
I appended the following `ReportReplicaService` to your existing `.proto` file:
```protobuf
// --- Experiment 7: Eventual Consistency (Gossip + LWW) ---
service ReportReplicaService {
 rpc SaveReport (ReportUpdate) returns (ReportAck);
 rpc SyncReport (ReportUpdate) returns (ReportAck);
 rpc GetReport (ReportQuery) returns (ReportState);
}

message ReportUpdate {
 string topic = 1;
 string content = 2;
 int32 lamport_timestamp = 3;
 string origin_replica = 4;
}

message ReportAck {
 bool accepted = 1;
 string replica = 2;
 int32 lamport_timestamp = 3;
}

message ReportQuery {
 string topic = 1;
}

message ReportState {
 string topic = 1;
 string content = 2;
 int32 lamport_timestamp = 3;
 string origin_replica = 4;
}
```

### Step 2: Compile Protocol Buffers
Generated the new Python stubs:
```bash
python -m grpc_tools.protoc -I=proto --python_out=. --grpc_python_out=. proto/research.proto
```

### Step 3: The Replica Node (`replica_node.py`)
Implements the core distributed concepts:
1. **Accept-then-gossip:** `SaveReport` handler applies the write locally, replies immediately, and launches a background thread to gossip.
2. **Lamport Clocks:** Tick on send, `max(local, received) + 1` on receive.
3. **Last-Write-Wins (LWW):** `_apply_if_newer` only overwrites the local store if the incoming `(lamport_timestamp, origin_replica)` tuple is strictly greater than the current one.
```python
import sys, time, threading
from concurrent import futures
import grpc
import research_pb2, research_pb2_grpc

ALL_REPLICAS = {"A": "localhost:60301", "B": "localhost:60302", "C": "localhost:60303"}

class ReplicaNode(research_pb2_grpc.ReportReplicaServiceServicer):
    def __init__(self, name):
        self.name = name
        self.peers = {n: addr for n, addr in ALL_REPLICAS.items() if n != name}
        self.clock = 0
        self.lock = threading.Lock()
        self.store = {} # topic -> (content, lamport_timestamp, origin_replica)

    def log(self, msg):
        print(f"[{self.name} t={self.clock:>2}] {msg}", flush=True)

    def tick(self):
        with self.lock:
            self.clock += 1
            return self.clock

    def update_clock(self, received_ts):
        with self.lock:
            self.clock = max(self.clock, received_ts) + 1
            return self.clock

    def _apply_if_newer(self, topic, content, ts, origin):
        with self.lock:
            current = self.store.get(topic)
            if current is None or (ts, origin) > (current[1], current[2]):
                self.store[topic] = (content, ts, origin)
                self.log(f"APPLIED '{topic}' = \"{content}\" (ts={ts}, origin={origin})")
                return True
            self.log(f"IGNORED stale update for '{topic}'")
            return False

    def _gossip(self, topic, content, ts, origin):
        for peer_name, addr in self.peers.items():
            try:
                with grpc.insecure_channel(addr) as channel:
                    stub = research_pb2_grpc.ReportReplicaServiceStub(channel)
                    stub.SyncReport(research_pb2.ReportUpdate(
                        topic=topic, content=content,
                        lamport_timestamp=ts, origin_replica=origin))
                    self.log(f"Gossiped '{topic}' -> {peer_name}")
            except grpc.RpcError as e:
                self.log(f"Gossip to {peer_name} failed: {e.code()}")

    def SaveReport(self, request, context):
        ts = self.tick()
        self._apply_if_newer(request.topic, request.content, ts, self.name)
        threading.Thread(target=self._gossip, args=(request.topic, request.content, ts, self.name), daemon=True).start()
        return research_pb2.ReportAck(accepted=True, replica=self.name, lamport_timestamp=ts)

    def SyncReport(self, request, context):
        self.update_clock(request.lamport_timestamp)
        self._apply_if_newer(request.topic, request.content, request.lamport_timestamp, request.origin_replica)
        return research_pb2.ReportAck(accepted=True, replica=self.name, lamport_timestamp=self.clock)

    def GetReport(self, request, context):
        with self.lock:
            entry = self.store.get(request.topic)
            if entry is None:
                return research_pb2.ReportState(topic=request.topic, content="", lamport_timestamp=0, origin_replica="")
            content, ts, origin = entry
            return research_pb2.ReportState(topic=request.topic, content=content, lamport_timestamp=ts, origin_replica=origin)

def serve(name, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    research_pb2_grpc.add_ReportReplicaServiceServicer_to_server(ReplicaNode(name), server)
    server.add_insecure_port(f"localhost:{port}")
    server.start()
    print(f"Replica-{name} listening on localhost:{port}")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve(sys.argv[1], int(sys.argv[2]))
```

### Step 4: The Client Simulator (`replica_client.py`)
Deliberately creates a conflict by writing to Node A and Node C almost simultaneously, then checks the system state during and after the convergence window.

---

## 3. Manual Execution Guide (How to run it)

You will need **4 Git Bash terminals** to demonstrate this.

### Step 1: Start Replica Node A (Terminal 1)
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python -u replica_node.py A 60301
```

### Step 2: Start Replica Node B (Terminal 2)
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python -u replica_node.py B 60302
```

### Step 3: Start Replica Node C (Terminal 3)
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python -u replica_node.py C 60303
```

*(Ensure all 3 terminals print `Replica-X listening on localhost:6030X`)*

### Step 4: Run the Client to force the race condition (Terminal 4)
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python replica_client.py
```

### What to check in the output:
1. **The "Immediately After" Disagreement:** The client output immediately after the writes will show that Node A and Node C disagree (they each think their local draft is the truth), and Node B might be entirely empty or only have one update because Gossip is still traveling!
2. **LWW Conflict Resolution:** Look at Node A and Node C's terminal logs. You will see an `APPLIED` log for the local write, followed by an `IGNORED stale update` if the arriving gossip has a lower Lamport timestamp than the stored write.
3. **The "After Convergence" Agreement:** After waiting 2 seconds for all asynchronous gossip to complete, the client will query all three replicas again and print `*** CONVERGED: all replicas agree ***` showing that the tie-breaker correctly synchronized the entire cluster!
