import grpc
import research_pb2
import research_pb2_grpc
from lamport_clock import LamportClock
import time

def run():
    clock = LamportClock()
    
    print("[CLIENT] Connecting to Lamport Planner Service...")
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = research_pb2_grpc.PlannerServiceStub(channel)
        
        print("\n========== SENDING REQUEST 1 ==========")
        # Increment clock before sending
        send_time = clock.send_event()
        print(f"Sending Request for topic 'IPC'")
        print(f"Lamport Clock : {send_time}")
        
        response = stub.GeneratePlan(research_pb2.PlanRequest(
            topic="Inter-Process Communication",
            goals="Learn basics",
            depth="Quick",
            lamport_clock=send_time
        ))
        
        # Update clock upon receiving response
        receive_time = clock.receive_event(response.lamport_clock)
        print("\n========== RECEIVED RESPONSE 1 ==========")
        print(f"Lamport Clock : {receive_time}")
        print(f"Message       : {response.message}")
        print(f"Questions     : {len(response.questions)} generated")
        
        time.sleep(1) # Simulate some local work
        
        print("\n========== SENDING REQUEST 2 ==========")
        # Increment clock before sending next request
        send_time_2 = clock.send_event()
        print(f"Sending Request for topic 'Distributed File Systems'")
        print(f"Lamport Clock : {send_time_2}")
        
        response_2 = stub.GeneratePlan(research_pb2.PlanRequest(
            topic="Distributed File Systems",
            goals="Understand HDFS",
            depth="Medium",
            lamport_clock=send_time_2
        ))
        
        # Update clock upon receiving response
        receive_time_2 = clock.receive_event(response_2.lamport_clock)
        print("\n========== RECEIVED RESPONSE 2 ==========")
        print(f"Lamport Clock : {receive_time_2}")
        print(f"Message       : {response_2.message}")
        print(f"Questions     : {len(response_2.questions)} generated")
        print("=========================================\n")


if __name__ == '__main__':
    run()
