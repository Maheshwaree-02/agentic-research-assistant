"""Database models for ResearchPilot AI."""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class Research(Base):
    """Main research record storing complete research sessions."""
    __tablename__ = "researches"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    topic = Column(String(500), nullable=False, index=True)
    goals = Column(Text)
    draft = Column(Text)
    findings = Column(JSON)
    sources = Column(JSON)  # Structured source references
    citations = Column(JSON)
    review = Column(Text)  # Reviewer feedback
    llm_used = Column(String(50))
    depth = Column(String(20), default="Medium")

    __table_args__ = (
        Index('ix_researches_timestamp', timestamp.desc()),
    )


class Finding(Base):
    """Individual research finding linked to a research session."""
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True)
    research_id = Column(Integer, ForeignKey('researches.id', ondelete='CASCADE'))
    question = Column(String(500))
    content = Column(Text)
    sources = Column(JSON)