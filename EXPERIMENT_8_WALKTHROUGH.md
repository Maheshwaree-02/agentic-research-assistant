# Experiment 8: Redis Caching for Fault Tolerance (Cache-Aside)
**Course:** Distributed Computing Lab (DC Lab)  
**Project Integration:** ResearchPilot AI

---

## 1. Experiment Overview & Objective

| Parameter | Details |
|---|---|
| **Experiment No.** | 8 |
| **Title** | Redis Caching for Fault Tolerance (Cache-Aside Pattern) |
| **Goal** | Add a caching layer (`cache_gateway.py`) in front of the existing `PlannerService` backend. |
| **Fault Tolerance** | Demonstrate that the system degrades gracefully and remains highly available even if either the Cache (Redis) fails or the real Database (gRPC Backend) fails. |

### How this connects to your project
We didn't rebuild the entire database. Instead, we used the exact same `planner_server.py` you built in **Experiment 2**. This demonstrates a realistic microservice evolution: you don't rebuild the core service; you wrap it with a fast edge-caching layer to reduce load and increase availability!

---

## 2. Code Setup

All files are located in `C:/Users/bharg/researchpilot-ai/grpc_experiment`.

### The Cache Gateway (`cache_gateway.py`)
This script acts as the middleman between the user and the `PlannerService`. It implements the **Cache-Aside (Lazy Loading)** pattern with two fault-tolerance fallback paths:

1. **Happy Path:**
   - Client requests a Research Plan.
   - Gateway checks Redis (`fresh:plan:Topic`).
   - If missing, it calls the gRPC backend, caches the result in Redis with a 10s TTL, and saves a *permanent* backup key (`stale:plan:Topic`).
2. **Fault Path 1 (Redis is Down):**
   - The Gateway catches the connection error and instantly passes the request through to the gRPC backend. The client still gets the result, just without the speed boost.
3. **Fault Path 2 (Backend is Down):**
   - The gRPC call fails. Instead of crashing, the Gateway checks Redis for the *permanent backup key* (`stale`). It serves the stale plan to the user, proving high availability!

```python
import json
import grpc
import redis
import research_pb2
import research_pb2_grpc

REDIS_HOST = "localhost"
REDIS_PORT = 6379
CACHE_TTL_SECONDS = 10 
BACKEND_SERVICE_ADDR = "localhost:50051"

STALE_KEY_PREFIX = "stale:plan:" 
FRESH_KEY_PREFIX = "fresh:plan:" 

def get_redis():
    # Short timeouts so we fail-fast if Redis is offline
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_connect_timeout=1, socket_timeout=1)

def fetch_from_backend(topic):
    with grpc.insecure_channel(BACKEND_SERVICE_ADDR) as channel:
        stub = research_pb2_grpc.PlannerServiceStub(channel)
        response = stub.GeneratePlan(research_pb2.PlanRequest(topic=topic, goals="Exp 8", depth="Quick"), timeout=5)
        return {"topic": topic, "questions": list(response.questions), "message": response.message}

def get_plan(topic):
    fresh_key = f"{FRESH_KEY_PREFIX}{topic}"
    stale_key = f"{STALE_KEY_PREFIX}{topic}"

    try:
        r = get_redis()
        cached = r.get(fresh_key)
        if cached:
            print(f"[Gateway] CACHE HIT for topic '{topic}'")
            return json.loads(cached), "cache-hit"
        print(f"[Gateway] CACHE MISS for topic '{topic}' -- querying backend")
    except redis.exceptions.RedisError as e:
        print(f"[Gateway] REDIS UNAVAILABLE ({e}) -- falling back to backend directly")
        r = None

    try:
        data = fetch_from_backend(topic)
        print(f"[Gateway] Fetched plan for '{topic}' from BACKEND")
        if r is not None:
            try:
                r.set(fresh_key, json.dumps(data), ex=CACHE_TTL_SECONDS)
                r.set(stale_key, json.dumps(data)) # Never expires
            except redis.exceptions.RedisError:
                pass
        return data, "backend"
    except grpc.RpcError as e:
        print(f"[Gateway] BACKEND UNAVAILABLE ({e.code()}) -- checking for stale cache")
        if r is not None:
            try:
                stale = r.get(stale_key)
                if stale:
                    print(f"[Gateway] Serving STALE cached copy for topic '{topic}'")
                    return json.loads(stale), "stale-fallback"
            except redis.exceptions.RedisError:
                pass
        raise RuntimeError("Topic unavailable: both backend and cache failed")

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "Distributed Caching"
    data, source = get_plan(topic)
    print(f"\nResult (source={source}):\n{json.dumps(data, indent=2)}")
```

---

## 3. Manual Execution Guide (How to Demo)

### Step 1: Start Redis (No Passwords, No WSL Required!)
I have downloaded a portable Windows version of Redis directly into your folder.
Open **Terminal 1** and run:
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment/redis_win
./redis-server.exe
```
*(Leave this running. No Linux or sudo passwords needed!)*

### Step 2: Start your Backend Server
Open **Terminal 2** and start the existing Backend Server (from Experiment 2):
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python -u planner_server.py
```

### Step 3: Prove the Cache-Aside Pattern
Open **Terminal 3** and hit the Gateway:
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
python cache_gateway.py "Docker vs VMs"
```
* **First run:** You will see `CACHE MISS... Fetched from BACKEND`.
* **Run the exact same command again immediately:** You will see `CACHE HIT` and the source will say `source=cache-hit`. The backend terminal won't print anything because the request was intercepted by Redis!

### Step 4: Prove Fault Tolerance Path 1 (Redis is Down)
1. Go to **Terminal 1** and press `Ctrl+C` to kill the Redis server.
2. Go to **Terminal 3** and run:
   ```bash
   python cache_gateway.py "Machine Learning"
   ```
*Result:* The gateway prints `REDIS UNAVAILABLE -- falling back to backend directly`. It gracefully degrades, routing the traffic to Terminal 2, and you still get your answer!

### Step 5: Prove Fault Tolerance Path 2 (Backend is Down)
1. **Restart your Redis Server** in Terminal 1 (`./redis-server.exe`).
2. Make sure the cache is warm by running a successful query in Terminal 3:
   ```bash
   python cache_gateway.py "Docker vs VMs"
   ```
3. **Kill the Backend Server:** Go to **Terminal 2** and press `Ctrl+C` to stop `planner_server.py`.
4. Wait 10 seconds for the `fresh` cache to expire.
5. **Hit the Gateway** in Terminal 3:
   ```bash
   python cache_gateway.py "Docker vs VMs"
   ```
*Result:* The gateway will print `BACKEND UNAVAILABLE -- checking for stale cache`. Because we saved a permanent backup key, it will say `Serving STALE cached copy`. Even though your actual database/service is completely down, your user still gets a response!
