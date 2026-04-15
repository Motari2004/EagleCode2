from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, Index, Date as SQLDate
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import os

# Database URL
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Create engine and session
if DATABASE_URL:
    clean_url = DATABASE_URL.split('?')[0]
    ASYNC_DATABASE_URL = clean_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        connect_args={"ssl": True}
    )
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    Base = declarative_base()
else:
    engine = None
    AsyncSessionLocal = None
    Base = declarative_base()

# ========== DEFINE ALL MODELS ==========

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

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    preview_html = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    user_id = Column(String, default="default")
    project_type = Column(String, nullable=True)
    file_count = Column(Integer, default=0)
    size_bytes = Column(Integer, default=0)
    is_public = Column(Boolean, default=False)
    version = Column(Integer, default=1)

class ProjectFile(Base):
    __tablename__ = "project_files"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, nullable=False, index=True)
    file_path = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    file_type = Column(String, nullable=True)
    size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_project_file_path', 'project_id', 'file_path', unique=True),
    )

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    key = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

class Template(Base):
    __tablename__ = "templates"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False, index=True)
    files = Column(Text, nullable=False)
    preview_html = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    user_id = Column(String, default="default")
    usage_count = Column(Integer, default=0)

# ========== HELPER FUNCTIONS ==========

async def init_db():
    """Initialize database tables"""
    if engine is None:
        print("⚠️ Database not configured")
        return
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ All tables verified/created successfully!")
            
            # List all tables
            from sqlalchemy import text
            result = await conn.execute(
                text("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)
            )
            tables = result.fetchall()
            if tables:
                print("\n📚 Existing tables in database:")
                for table in tables:
                    print(f"  - {table[0]}")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        raise