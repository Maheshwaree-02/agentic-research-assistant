import grpc
import research_pb2
import research_pb2_grpc

def run():
    print("[CLIENT] Attempting to connect to Planner Service on localhost:50051...")
    
    # Open a gRPC channel
    with grpc.insecure_channel('localhost:50051') as channel:
        # Create a stub (client)
        stub = research_pb2_grpc.PlannerServiceStub(channel)
        
        print("[CLIENT] Sending PlanRequest for topic: 'Distributed Computing Concepts'")
        
        # Make the RPC call
        response = stub.GeneratePlan(research_pb2.PlanRequest(
            topic="Distributed Computing Concepts",
            goals="Understand RPC, CAP theorem, and consistency models",
            depth="Medium"
        ))
    
    print("\n" + "="*50)
    print("           RECEIVED RESPONSE FROM SERVER")
    print("="*50)
    print(f"Status Message: {response.message}\n")
    print("Generated Research Questions:")
    for i, q in enumerate(response.questions, 1):
        print(f" {i}. {q}")
    print("="*50)

if __name__ == '__main__':
    run()
