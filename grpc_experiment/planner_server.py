import grpc
from concurrent import futures
import sys
import os

import research_pb2
import research_pb2_grpc

# Append parent directory to path so we can import from the main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import get_llm_client
from core.state import AgentState
from agents.planner import PlannerAgent
from config import settings

class PlannerServiceServicer(research_pb2_grpc.PlannerServiceServicer):
    def GeneratePlan(self, request, context):
        print(f"[SERVER] Received request for topic: '{request.topic}', depth: '{request.depth}'")
        try:
            # Enforce mock mode for consistent testing without needing API keys
            settings.USE_MOCK = True
            
            client = get_llm_client()
            state = AgentState(topic=request.topic, goals=request.goals, depth=request.depth)
            
            print("[SERVER] Running Planner Agent...")
            planner = PlannerAgent(client)
            state = planner.run(state)
            
            print(f"[SERVER] Successfully generated {len(state.plan)} questions.")
            return research_pb2.PlanResponse(
                questions=state.plan,
                message="Plan generated successfully via gRPC!"
            )
        except Exception as e:
            print(f"[SERVER] Error: {str(e)}")
            return research_pb2.PlanResponse(
                questions=[],
                message=f"Error generating plan: {str(e)}"
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    research_pb2_grpc.add_PlannerServiceServicer_to_server(PlannerServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Planner Service Started on Port 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
