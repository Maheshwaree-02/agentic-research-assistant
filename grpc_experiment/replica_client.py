import time, threading, grpc
import research_pb2, research_pb2_grpc

REPLICAS = {"A": "localhost:60301", "B": "localhost:60302", "C": "localhost:60303"}

def save(replica_name, topic, content):
    with grpc.insecure_channel(REPLICAS[replica_name]) as channel:
        stub = research_pb2_grpc.ReportReplicaServiceStub(channel)
        ack = stub.SaveReport(research_pb2.ReportUpdate(
            topic=topic, content=content, lamport_timestamp=0, origin_replica=""))
        print(f"[Client] Saved on Replica-{replica_name}: \"{content}\" "
              f"-> accepted={ack.accepted}, replica_ts={ack.lamport_timestamp}")

def read(replica_name, topic):
    with grpc.insecure_channel(REPLICAS[replica_name]) as channel:
        stub = research_pb2_grpc.ReportReplicaServiceStub(channel)
        state = stub.GetReport(research_pb2.ReportQuery(topic=topic))
        return state.content, state.lamport_timestamp, state.origin_replica

def main():
    topic = "distributed-systems-report-1"
    print("=== Simulating two concurrent writers hitting DIFFERENT replicas ===\n")
    
    # Simulate two users saving a draft of the same report at the same time to different edge nodes
    t1 = threading.Thread(target=save, args=("A", topic, "Draft v1 - saved to Node A"))
    t2 = threading.Thread(target=save, args=("C", topic, "Draft v1 - saved to Node C"))
    
    t1.start()
    time.sleep(0.05) # near-simultaneous, not identical - creates a real race
    t2.start()
    
    t1.join()
    t2.join()
    
    print("\n=== Immediately after writes (replicas may still be mid-gossip) ===")
    for name in REPLICAS:
        content, ts, origin = read(name, topic)
        print(f"Replica-{name}: \"{content}\" (ts={ts}, origin={origin})")
        
    print("\nWaiting 2s for gossip to finish propagating...\n")
    time.sleep(2)
    
    print("=== After convergence window ===")
    results = {}
    for name in REPLICAS:
        content, ts, origin = read(name, topic)
        results[name] = content
        print(f"Replica-{name}: \"{content}\"")
        
    if len(set(results.values())) == 1:
        print(f"\n*** CONVERGED: all replicas agree on: \"{list(results.values())[0]}\" ***")
    else:
        print(f"\n*** NOT YET CONVERGED: {set(results.values())} ***")

if __name__ == "__main__":
    main()
