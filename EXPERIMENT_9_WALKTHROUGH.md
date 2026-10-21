# Experiment 9: Raft-Based Leader Election & Failover
**Course:** Distributed Computing Lab (DC Lab)  
**Project Integration:** ResearchPilot AI

---

## 1. Experiment Overview & Objective

| Parameter | Details |
|---|---|
| **Experiment No.** | 9 |
| **Title** | Raft-Based Leader Election & Failover for Uninterrupted Coordination |
| **Goal** | Take a single-process coordinator service (our `LockManager` from Exp 5) and make it fault-tolerant by running it as a cluster of 3 replicas using the **Raft consensus algorithm**. |
| **Why this matters** | A centralized Lock Manager is a single point of failure. By using Raft, the cluster elects exactly one leader. If the leader crashes, the remaining nodes automatically elect a new leader, ensuring that the lock/coordination service never goes offline. |

---

## 2. Step-by-Step Code Setup

All files are located in `C:/Users/bharg/researchpilot-ai/grpc_experiment`. Because this uses pure Python gRPC, it runs entirely natively on Windows (no WSL, no passwords, no Redis needed!).

### Step 1: Protocol Buffer Definition (`proto/research.proto`)
I appended the following `RaftService` to your existing `.proto` file.
```protobuf
// --- Experiment 9: Raft Leader Election ---
service RaftService {
 rpc RequestVote (VoteRequest) returns (VoteReply);
 rpc AppendEntries (HeartbeatRequest) returns (HeartbeatReply);
}

message VoteRequest {
 int32 term = 1;
 string candidate_id = 2;
}

message VoteReply {
 int32 term = 1;
 bool vote_granted = 2;
}

message HeartbeatRequest {
 int32 term = 1;
 string leader_id = 2;
}

message HeartbeatReply {
 int32 term = 1;
 bool success = 2;
}
```

### Step 2: Compile Protocol Buffers
Generated the new Python stubs:
```bash
python -m grpc_tools.protoc -I=proto --python_out=. --grpc_python_out=. proto/research.proto
```

### Step 3: The Raft Coordinator Node (`raft_node.py`)
This script combines the **Raft Election Logic** and the **Lock Manager Logic**. The magic here is that the application-level logic (`AcquireLock`, `ReleaseLock`) is gated behind the `if self.state != "LEADER"` check. 

Key mechanics:
1. **Randomized Timeouts (1.5s - 3.0s):** Prevents split votes by ensuring one node usually times out first and requests votes.
2. **Term Numbers:** Lets nodes distinguish stale requests from an old leader versus fresh requests from a new one.
3. **Majority Voting:** A node needs $N//2 + 1$ (which is 2 out of 3) votes to become leader, ensuring we tolerate exactly 1 failure.

```python
import sys, time, random, threading
from concurrent import futures
import grpc
import research_pb2, research_pb2_grpc

ALL_NODES = {"A": "localhost:60401", "B": "localhost:60402", "C": "localhost:60403"}
HEARTBEAT_INTERVAL = 0.5
ELECTION_TIMEOUT_RANGE = (1.5, 3.0)

# Combine Raft logic and Lock Manager logic into a single cohesive node
class CoordinatorNode(research_pb2_grpc.RaftServiceServicer, research_pb2_grpc.LockServiceServicer):
    def __init__(self, node_id):
        self.id = node_id
        self.peers = {n: addr for n, addr in ALL_NODES.items() if n != node_id}
        self.lock = threading.Lock()
        self.state = "FOLLOWER"
        self.current_term = 0
        self.voted_for = None
        self.leader_id = None
        self.last_heartbeat = time.time()
        self.resource_locks = {"draft": None, "submission": None}

    def log(self, msg):
        print(f"[{self.id} term={self.current_term} {self.state}] {msg}", flush=True)

    def _reset_election_timer(self):
        self.last_heartbeat = time.time()

    def _random_timeout(self):
        return random.uniform(*ELECTION_TIMEOUT_RANGE)

    # --- Raft RPC Handlers ---
    def RequestVote(self, request, context):
        with self.lock:
            if request.term > self.current_term:
                self.current_term = request.term
                self.voted_for = None
                self.state = "FOLLOWER"

            grant = (request.term >= self.current_term and self.voted_for in (None, request.candidate_id))
            if grant:
                self.voted_for = request.candidate_id
                self._reset_election_timer()
                self.log(f"Voted for {request.candidate_id} (term {request.term})")
            return research_pb2.VoteReply(term=self.current_term, vote_granted=grant)

    def AppendEntries(self, request, context):
        with self.lock:
            if request.term >= self.current_term:
                self.current_term = request.term
                self.state = "FOLLOWER"
                self.leader_id = request.leader_id
                self._reset_election_timer()
                return research_pb2.HeartbeatReply(term=self.current_term, success=True)
            return research_pb2.HeartbeatReply(term=self.current_term, success=False)

    # --- Coordination Logic (Gated by Leadership) ---
    def AcquireLock(self, request, context):
        with self.lock:
            if self.state != "LEADER":
                hint = self.leader_id or "unknown"
                return research_pb2.LockReply(granted=False, message=f"not-leader, try={hint}")
            
            # Normal Lock Manager logic...
            resource, holder = request.resource_id, request.holder_id
            owner = self.resource_locks.get(resource)
            if owner is None:
                self.resource_locks[resource] = holder
                self.log(f"Granted lock '{resource}' to Node-{holder}")
                return research_pb2.LockReply(granted=True, message="granted")
            return research_pb2.LockReply(granted=False, message="locked")

    # (Background threads for _election_watchdog and _heartbeat_loop omitted here for brevity, see code file)

def serve(node_id):
    node = CoordinatorNode(node_id)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    
    # Register both Raft and LockService on the same server instance!
    research_pb2_grpc.add_RaftServiceServicer_to_server(node, server)
    research_pb2_grpc.add_LockServiceServicer_to_server(node, server)
    
    port = ALL_NODES[node_id].split(":")[1]
    server.add_insecure_port(f"localhost:{port}")
    server.start()
    print(f"RaftNode-{node_id} listening on {ALL_NODES[node_id]}")
    
    threading.Thread(target=node._election_watchdog, daemon=True).start()
    threading.Thread(target=node._heartbeat_loop, daemon=True).start()
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve(sys.argv[1])
```

---

## 4. Manual Execution Guide (How to Demo)

You will need **3 Git Bash terminals** to demonstrate this.

### Step 1: Start the Cluster (No timing pressure)
Start the three nodes normally, one after another. 

**Terminal 1:**
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python raft_node.py A
```
**Terminal 2:**
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python raft_node.py B
```
**Terminal 3:**
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python raft_node.py C
```

### What to check (Initial Election):
Within 1.5–3 seconds of all three being up, one node will spontaneously announce an election and win:
```text
[A term=1 CANDIDATE] Starting election
[B term=1 FOLLOWER] Voted for A (term 1)
[C term=1 FOLLOWER] Voted for A (term 1)
[A term=1 LEADER] *** ELECTED LEADER *** (3/3 votes)
```
Let it run for a few seconds. The system is stable (you won't see repeated elections).

### Step 2: Test the Failover!
1. Find whichever terminal became the `LEADER`.
2. **Kill that terminal** by pressing `Ctrl+C`.
3. Watch the remaining two terminals. Within 3 seconds, one of the surviving followers will realize the leader is dead (no heartbeats) and trigger a new election for **term=2**:
```text
[B term=2 CANDIDATE] Starting election
[C term=2 FOLLOWER] Voted for B (term 2)
[B term=2 LEADER] *** ELECTED LEADER *** (2/3 votes)
```

**Proof of Fault Tolerance:** The coordination service seamlessly recovered and promoted a new leader without any manual restart! All subsequent lock requests will now be handled by Node B.
