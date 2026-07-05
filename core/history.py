"""Research history persistence to PostgreSQL."""
import logging
from sqlalchemy.orm import Session
from database.schema import Research

logger = logging.getLogger(__name__)


def save_to_history(db: Session, state, topic: str, llm_used: str = "gemini") -> int:
    """Save research to PostgreSQL with duplicate detection.
    
    Returns the research ID.
    """
    # Check for exact duplicate (same topic and draft)
    existing = db.query(Research).filter(
        Research.topic == topic,
        Research.draft == state.draft
    ).first()

    if existing:
        logger.info(f"Duplicate detected for topic '{topic}', skipping save")
        return existing.id

    research = Research(
        topic=topic,
        goals=state.goals,
        draft=state.draft,
        findings=state.findings,
        sources=getattr(state, 'sources', []),
        citations=state.citations,
        review=getattr(state, 'review', None),
        llm_used=llm_used,
        depth=getattr(state, 'depth', 'Medium')
    )
    db.add(research)
    db.commit()
    logger.info(f"Saved research #{research.id}: {topic}")
    return research.id


def update_history(db: Session, research_id: int, draft: str, review: str = None) -> bool:
    """Update an existing research record (e.g., after editing/review)."""
    research = db.query(Research).filter(Research.id == research_id).first()
    if not research:
        return False

    research.draft = draft
    if review:
        research.review = review
    db.commit()
    logger.info(f"Updated research #{research_id}")
    return True


def load_history(db: Session, limit: int = 10):
    """Load recent research records, ordered by most recent first."""
    return db.query(Research).order_by(Research.timestamp.desc()).limit(limit).all()