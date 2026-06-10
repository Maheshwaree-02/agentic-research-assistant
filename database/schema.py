from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Research(Base):
    __tablename__ = "researches"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    topic = Column(String(500), nullable=False)
    goals = Column(Text)
    draft = Column(Text)
    findings = Column(JSON)
    citations = Column(JSON)
    llm_used = Column(String(50))

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True)
    research_id = Column(Integer)
    question = Column(String(500))
    content = Column(Text)
    sources = Column(JSON)