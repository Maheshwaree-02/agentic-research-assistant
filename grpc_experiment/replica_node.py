import sys, time, threading
from concurrent import futures
import grpc
import research_pb2, research_pb2_grpc

ALL_REPLICAS = {
    "A": "localhost:60301",
    "B": "localhost:60302",
    "C": "localhost:60303",
}

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
        """Last-Write-Wins: only overwrite if the incoming update is
        strictly newer, tie-broken by origin replica name."""
        with self.lock:
            current = self.store.get(topic)
            if current is None or (ts, origin) > (current[1], current[2]):
                self.store[topic] = (content, ts, origin)
                self.log(f"APPLIED '{topic}' = \"{content}\" (ts={ts}, origin={origin})")
                return True
            self.log(f"IGNORED stale update for '{topic}' "
                     f"(incoming ts={ts}/{origin} <= current ts={current[1]}/{current[2]})")
            return False

    def _gossip(self, topic, content, ts, origin):
        """Fire-and-forget replication - runs AFTER the local write
        already succeeded and the client already got its response."""
        for peer_name, addr in self.peers.items():
            try:
                with grpc.insecure_channel(addr) as channel:
                    stub = research_pb2_grpc.ReportReplicaServiceStub(channel)
                    stub.SyncReport(research_pb2.ReportUpdate(
                        topic=topic, content=content,
                        lamport_timestamp=ts, origin_replica=origin))
                    self.log(f"Gossiped '{topic}' -> {peer_name}")
            except grpc.RpcError as e:
                self.log(f"Gossip to {peer_name} failed (will catch up later): {e.code()}")

    def SaveReport(self, request, context):
        ts = self.tick()
        self._apply_if_newer(request.topic, request.content, ts, self.name)
        threading.Thread(
            target=self._gossip,
            args=(request.topic, request.content, ts, self.name),
            daemon=True,
        ).start()
        return research_pb2.ReportAck(accepted=True, replica=self.name, lamport_timestamp=ts)

    def SyncReport(self, request, context):
        self.update_clock(request.lamport_timestamp)
        self._apply_if_newer(request.topic, request.content,
                             request.lamport_timestamp, request.origin_replica)
        return research_pb2.ReportAck(accepted=True, replica=self.name, lamport_timestamp=self.clock)

    def GetReport(self, request, context):
        with self.lock:
            entry = self.store.get(request.topic)
            if entry is None:
                return research_pb2.ReportState(topic=request.topic, content="", lamport_timestamp=0, origin_replica="")
            content, ts, origin = entry
            return research_pb2.ReportState(topic=request.topic, content=content,
                                            lamport_timestamp=ts, origin_replica=origin)


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
    if len(sys.argv) < 3:
        print("Usage: python replica_node.py <NAME> <PORT>")
        sys.exit(1)
    serve(sys.argv[1], int(sys.argv[2]))
