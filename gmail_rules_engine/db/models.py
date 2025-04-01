from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, 
    DateTime, ForeignKey, create_engine, func, Index
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(255), unique=True, nullable=False)
    thread_id = Column(String(255), nullable=False)
    from_address = Column(Text, nullable=False)
    to_address = Column(Text, nullable=False)
    subject = Column(Text)
    body = Column(Text)
    received_date = Column(DateTime(timezone=True), nullable=False)
    is_read = Column(Boolean, default=False)
    labels = Column(ARRAY(String))
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    rule_executions = relationship("RuleExecution", back_populates="email")

class RuleExecution(Base):
    __tablename__ = "rule_executions"
    
    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    rule_id = Column(String(255), nullable=False)
    executed_at = Column(DateTime(timezone=True), default=func.now())
    actions_taken = Column(JSONB, nullable=False)
    
    email = relationship("Email", back_populates="rule_executions")