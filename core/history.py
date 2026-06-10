from sqlalchemy.orm import Session
from database.schema import Research
from datetime import datetime

def save_to_history(db: Session, state, topic: str, llm_used: str = "gemini"):
    """Save research to PostgreSQL"""
    research = Research(
        topic=topic,
        goals=state.goals,
        draft=state.draft,
        findings=state.findings,
        citations=state.citations,
        llm_used=llm_used
    )
    db.add(research)
    db.commit()
    return research.id

def load_history(db: Session, limit: int = 10):
    """Load recent researches"""
    return db.query(Research).order_by(Research.timestamp.desc()).limit(limit).all()