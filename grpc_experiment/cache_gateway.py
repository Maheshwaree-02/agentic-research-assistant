import json
import grpc
import redis
import research_pb2
import research_pb2_grpc

REDIS_HOST = "localhost"
REDIS_PORT = 6379
CACHE_TTL_SECONDS = 10 # Short TTL so we can easily test misses in the lab

BACKEND_SERVICE_ADDR = "localhost:50051"

STALE_KEY_PREFIX = "stale:plan:" 
FRESH_KEY_PREFIX = "fresh:plan:" 

def get_redis():
    """Fresh connection per call, with a short timeout, so we can
    detect Redis being down quickly instead of hanging."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT,
                       socket_connect_timeout=1, socket_timeout=1, protocol=2)

def fetch_from_backend(topic):
    """Direct call to the real backend service (PlannerService from Exp 2/3)."""
    with grpc.insecure_channel(BACKEND_SERVICE_ADDR) as channel:
        stub = research_pb2_grpc.PlannerServiceStub(channel)
        response = stub.GeneratePlan(
            research_pb2.PlanRequest(topic=topic, goals="Experiment 8", depth="Quick"), 
            timeout=5
        )
        return {
            "topic": topic, 
            "questions": list(response.questions), 
            "message": response.message
        }

def get_plan(topic):
    fresh_key = f"{FRESH_KEY_PREFIX}{topic}"
    stale_key = f"{STALE_KEY_PREFIX}{topic}"

    # --- Try the cache first ---
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

    # --- Cache miss, or Redis itself is down: go to the real backend ---
    try:
        data = fetch_from_backend(topic)
        print(f"[Gateway] Fetched plan for '{topic}' from BACKEND")
        if r is not None:
            try:
                r.set(fresh_key, json.dumps(data), ex=CACHE_TTL_SECONDS)
                r.set(stale_key, json.dumps(data)) # no expiry - fault-tolerance backup
            except redis.exceptions.RedisError:
                print("[Gateway] Redis write failed, continuing without caching this result")
        return data, "backend"

    except grpc.RpcError as e:
        # --- Backend unreachable: fall back to a stale cached copy if we have one ---
        print(f"[Gateway] BACKEND UNAVAILABLE ({e.code()}) -- checking for stale cache")
        if r is not None:
            try:
                stale = r.get(stale_key)
                if stale:
                    print(f"[Gateway] Serving STALE cached copy for topic '{topic}'")
                    return json.loads(stale), "stale-fallback"
            except redis.exceptions.RedisError:
                pass
        raise RuntimeError(f"Topic '{topic}' unavailable: both backend and cache failed")

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "Distributed Caching"
    data, source = get_plan(topic)
    print(f"\nResult (source={source}):\n{json.dumps(data, indent=2)}")
