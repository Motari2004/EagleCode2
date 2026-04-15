from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, Index, Date as SQLDate
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

class UserCredits(Base):
    __tablename__ = "user_credits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, unique=True, index=True)
    plan = Column(String, default="free")
    daily_credits_used = Column(Integer, default=0)
    daily_reset_date = Column(SQLDate, nullable=False)
    monthly_credits_used = Column(Integer, default=0)
    monthly_reset_date = Column(SQLDate, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)