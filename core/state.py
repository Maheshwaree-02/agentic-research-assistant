from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class AgentState(BaseModel):
    topic: str
    goals: Optional[str] = None
    plan: Optional[List[str]] = None          # Changed to List[str] for simplicity
    findings: List[Dict] = []
    draft: Optional[str] = None
    citations: List[str] = []