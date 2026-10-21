import grpc
from concurrent import futures
import sys
import os

import research_pb2
import research_pb2_grpc
from lamport_clock import LamportClock

# Append parent directory to path so we can import from the main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import get_llm_client
from core.state import AgentState
from agents.planner import PlannerAgent
from config import settings

class PlannerServiceServicer(research_pb2_grpc.PlannerServiceServicer):
    def __init__(self):
        self.clock = LamportClock()

    def GeneratePlan(self, request, context):
        # Update server clock based on the incoming request's clock
        self.clock.receive_event(request.lamport_clock)
        print(f"\n========== RECEIVED REQUEST ==========")
        print(f"Topic          : {request.topic}")
        print(f"Lamport Clock  : {self.clock.time}")
        
        try:
            settings.USE_MOCK = True
            client = get_llm_client()
            state = AgentState(topic=request.topic, goals=request.goals, depth=request.depth)
            
            planner = PlannerAgent(client)
            state = planner.run(state)
            
            # Increment clock for the send event
            send_time = self.clock.send_event()
            
            print(f"Sending response with Lamport Clock: {send_time}")
            print("======================================\n")
            
            return research_pb2.PlanResponse(
                questions=state.plan,
                message="Plan generated successfully via gRPC with Lamport Clocks!",
                lamport_clock=send_time
            )
        except Exception as e:
            send_time = self.clock.send_event()
            return research_pb2.PlanResponse(
                questions=[],
                message=f"Error generating plan: {str(e)}",
                lamport_clock=send_time
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    research_pb2_grpc.add_PlannerServiceServicer_to_server(PlannerServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Lamport Planner Service Started on Port 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
