from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

from enum import Enum

class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class Model(str, Enum):
    GPT4 = "gpt-4"
    GPT35 = "gpt-3.5-turbo"
    CLAUDE = "claude-3-sonnet-20240229"

class APIKey(Base):
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    user_id = Column(String(255), nullable=True)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class QAPair(Base):
    __tablename__ = 'qa_pairs'
    
    id = Column(Integer, primary_key=True)
    webpage_url = Column(String(2048), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)