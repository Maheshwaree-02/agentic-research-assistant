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
            
            time.sleep(1.5) # widens the window for a deadlock to actually form
            
            if acquire(stub, second, node_id, ts):
                held.append(second)
            else:
                print(f"Node-{node_id}: ABORTED -- releasing held locks and retrying")
                for r in held:
                    release(stub, r, node_id)
                held = []
                time.sleep(1)
                
                # Retry
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
