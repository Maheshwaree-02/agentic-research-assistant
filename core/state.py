"""Agent state management for the research pipeline."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SourceReference(BaseModel):
    """A structured source/citation reference."""
    title: str = "Unknown"
    url: str = ""
    snippet: str = ""
    domain: str = ""
    accessed_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))


class AgentState(BaseModel):
    """Shared state passed between agents in the research pipeline."""
    topic: str
    goals: Optional[str] = None
    depth: str = "Medium"  # Quick, Medium, Deep
    plan: Optional[List[str]] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[Dict[str, str]] = Field(default_factory=list)
    draft: Optional[str] = None
    citations: List[str] = Field(default_factory=list)
    review: Optional[str] = None  # Reviewer feedback (separate from citations)
    metadata: Dict[str, Any] = Field(default_factory=lambda: {
        "started_at": datetime.now().isoformat(),
        "model_used": "",
        "duration_seconds": 0
    })