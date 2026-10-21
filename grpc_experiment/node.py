import sys, time, threading
from concurrent import futures
import grpc
import research_pb2, research_pb2_grpc

PEERS = {1: "localhost:60051", 2: "localhost:60052", 3: "localhost:60053"}

class Node:
    def __init__(self, node_id):
        self.id = node_id
        self.peers = {nid: addr for nid, addr in PEERS.items() if nid != node_id}
        self.clock = 0
        self.state = "RELEASED" # RELEASED -> WANTED -> HELD
        self.request_time = None
        self.lock = threading.Lock()
        self.deferred = [] # threading.Events for peers we're making wait

    def tick(self):
        with self.lock:
            self.clock += 1
            return self.clock

    def update(self, received_ts):
        with self.lock:
            self.clock = max(self.clock, received_ts) + 1
            return self.clock

    def serve(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        research_pb2_grpc.add_MutexServiceServicer_to_server(_Servicer(self), server)
        server.add_insecure_port(PEERS[self.id])
        server.start()
        return server

    def _call_with_retry(self, addr, my_ts, max_wait=30):
        # Peers may not be up yet - retry instead of crashing
        deadline = time.time() + max_wait
        while time.time() < deadline:
            try:
                with grpc.insecure_channel(addr) as channel:
                    stub = research_pb2_grpc.MutexServiceStub(channel)
                    return stub.RequestAccess(
                        research_pb2.AccessRequest(node_id=self.id, timestamp=my_ts)
                    )
            except grpc.RpcError:
                time.sleep(0.5)
        raise RuntimeError(f"Could not reach {addr}")

    def request_cs(self):
        my_ts = self.tick()
        with self.lock:
            self.state = "WANTED"
            self.request_time = my_ts
            
        print(f"Node-{self.id}: WANTS critical section (clock={my_ts})")

        for peer_id, addr in self.peers.items():
            reply = self._call_with_retry(addr, my_ts)
            self.update(reply.timestamp)
            print(f"Node-{self.id}: GRANTS received from Node-{peer_id}")

        with self.lock:
            self.state = "HELD"
            
        print(f"Node-{self.id}: ENTERED critical section")
        time.sleep(1.5) # simulate doing the submission
        self.release_cs()

    def release_cs(self):
        with self.lock:
            self.state = "RELEASED"
            to_release, self.deferred = self.deferred, []
            
        for event in to_release:
            event.set() # let deferred peers' RPCs finally return
        print(f"Node-{self.id}: EXITED critical section. Released {len(to_release)} deferred requests.")


class _Servicer(research_pb2_grpc.MutexServiceServicer):
    def __init__(self, node):
        self.node = node

    def RequestAccess(self, request, context):
        node = self.node
        node.update(request.timestamp)

        with node.lock:
            defer = (
                node.state == "HELD"
                or (node.state == "WANTED"
                    and (node.request_time, node.id) < (request.timestamp, request.node_id))
            )

        if defer:
            print(f"Node-{node.id}: DEFERS request from Node-{request.node_id}")
            event = threading.Event()
            with node.lock:
                node.deferred.append(event)
            event.wait() # blocks the RPC response — this IS the defer

        send_ts = node.tick()
        return research_pb2.AccessReply(node_id=node.id, timestamp=send_ts)


def main():
    if len(sys.argv) < 2:
        print("Usage: python node.py <node_id>")
        sys.exit(1)
        
    node_id = int(sys.argv[1])
    node = Node(node_id)
    server = node.serve()
    
    print(f"Node-{node.id} Started. Waiting for peers...")
    time.sleep(6) # let all 3 nodes finish starting up first
    node.request_cs()
    
    time.sleep(2)
    server.stop(0)

if __name__ == "__main__":
    main()
