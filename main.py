import json
import os
import re
import io
import jwt  # noqa
import asyncio
from html2image import Html2Image
from pathlib import Path

from fastapi.staticfiles import StaticFiles

from fastapi import Depends

from bson import ObjectId


import asyncio
import random
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass


import motor.motor_asyncio

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form

from routes.auth import router as auth_router, init_oauth

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastapi import FastAPI, Depends, HTTPException, status



from starlette.middleware.sessions import SessionMiddleware

from typing import Dict, Any, List, Set
# Add these with your other imports
import cloudinary
import cloudinary.uploader
from contextlib import asynccontextmanager

from sqlalchemy import Date  # ← Add this import

import shutil
from datetime import datetime, date

# Add these imports at the top if not already there

import uuid


from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, Index, select, desc, func, delete, text






import uvicorn
from fastapi import FastAPI, WebSocket, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import random  # ADD THIS
from dotenv import load_dotenv




import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Text, Integer, DateTime, select, desc, func, delete
from datetime import datetime
import uuid
import json



import requests
from bs4 import BeautifulSoup
import base64
from io import BytesIO
from PIL import Image
import hashlib
from typing import Optional
import httpx  
import os
from pathlib import Path  # ADD THIS
from typing import Dict, List

import tempfile
import zipfile







# ========== UPDATE YOUR AVAILABLE_MODELS ==========
# These are the actual model names from your list
AVAILABLE_MODELS = {
    "flash_lite_latest": "gemini-flash-lite-latest", # Latest flash lite
    "flash_lite_25": "gemini-2.5-flash-lite",    # Gemini 2.5 Flash Lite
    "flash_25": "gemini-2.5-flash",              # Your primary
    "flash_latest": "gemini-flash-latest",       # Latest flash version
}

# Model usage tracking
model_usage = {model: {"success": 0, "fail": 0, "last_fail": None} for model in AVAILABLE_MODELS.values()}












import json
import os
import re
import io
import jwt
import asyncio
from html2image import Html2Image
from pathlib import Path

from fastapi.staticfiles import StaticFiles
from fastapi import Depends
from bson import ObjectId
import random
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass

import motor.motor_asyncio
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from routes.auth import router as auth_router, init_oauth
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware
from typing import Dict, Any, List, Set

import cloudinary
import cloudinary.uploader
from contextlib import asynccontextmanager
from sqlalchemy import Date
import shutil
from datetime import datetime, date
import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, Index, select, desc, func, delete, text

import uvicorn
from fastapi import FastAPI, WebSocket, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from dotenv import load_dotenv

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
import json

import requests
from bs4 import BeautifulSoup
import base64
from io import BytesIO
from PIL import Image
import hashlib
from typing import Optional
import httpx
import tempfile
import zipfile

load_dotenv()

# ========== UPDATE YOUR AVAILABLE_MODELS ==========
AVAILABLE_MODELS = {
    "flash_lite_latest": "gemini-flash-lite-latest",
    "flash_lite_25": "gemini-2.5-flash-lite",
    "flash_25": "gemini-2.5-flash",
    "flash_latest": "gemini-flash-latest",
}

model_usage = {model: {"success": 0, "fail": 0, "last_fail": None} for model in AVAILABLE_MODELS.values()}

# ========== SMART LOAD BALANCER ==========

@dataclass
class KeyStats:
    success_count: int = 0
    fail_count: int = 0
    rate_limit_count: int = 0
    last_used: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    success_rate: float = 0.5
    weight: float = 1.0
    requests_this_minute: int = 0
    rate_limit_reset: datetime = None
    
    def __post_init__(self):
        if self.rate_limit_reset is None:
            self.rate_limit_reset = datetime.now()

class SmartLoadBalancer:
    """Intelligent load balancer for multiple API keys with weighted random selection"""
    
    def __init__(self):
        self.api_keys = []
        key_index = 1
        while True:
            api_key = os.environ.get(f"GEMINI_API_KEY_{key_index}", "")
            if not api_key:
                break
            self.api_keys.append(api_key)
            key_index += 1
        
        if not self.api_keys:
            single_key = os.environ.get("GEMINI_API_KEY", "")
            if single_key:
                self.api_keys = [single_key]
                print("⚠️ Using single GEMINI_API_KEY (no numbered keys found)")
        
        if not self.api_keys:
            raise ValueError("No API keys configured! Set GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.")
        
        self.models = [
            os.environ.get("MODEL_PRIMARY", "gemini-2.5-flash-lite"),
            os.environ.get("MODEL_SECONDARY", "gemini-flash-lite-latest"), 
            
        ]
        
        self.key_stats: Dict[int, KeyStats] = {}
        for i in range(len(self.api_keys)):
            self.key_stats[i] = KeyStats()
        
        self.model_failures = defaultdict(lambda: {"count": 0, "last_fail": None})
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        self._update_weights()
        
        print(f"\n{'='*60}")
        print(f"🚀 SMART LOAD BALANCER INITIALIZED")
        print(f"{'='*60}")
        print(f"📊 Total API Keys Loaded: {len(self.api_keys)}")
        print(f"🤖 Models per key: {self.models}")
        print(f"{'='*60}\n")
    
    
    
    
    
    
    
    
    
    
    def _update_weights(self):
        """Update weights for all keys based on success rate"""
        total_weight = 0
        
        for i, stats in self.key_stats.items():
            # Check if key is on cooldown
            if stats.cooldown_until and datetime.now() < stats.cooldown_until:
                stats.weight = 0
                continue
            
            # Calculate success rate
            total_attempts = stats.success_count + stats.fail_count
            if total_attempts > 0:
                stats.success_rate = stats.success_count / total_attempts
                # Boost new keys slightly to give them a chance
                if total_attempts < 10:
                    stats.success_rate = max(stats.success_rate, 0.3)
            else:
                stats.success_rate = 0.5  # Neutral for untested keys
            
            # ✅ Ensure minimum weight even for failing keys
            stats.weight = max(0.05, stats.success_rate)  # Minimum 0.05 weight
            total_weight += stats.weight
        
        # ✅ Log warning if total weight is too low
        if total_weight < 0.1:
            print(f"⚠️ Warning: Total weight is very low ({total_weight:.4f}), resetting all weights")
            for i in self.key_stats:
                self.key_stats[i].weight = 0.5
                self.key_stats[i].cooldown_until = None
                total_weight = len(self.key_stats) * 0.5
    
    
    
    
    
    
    
    def _select_key(self) -> int:
        """Select a key using weighted random selection"""
        # Build list of available keys (not on cooldown)
        available_keys = []
        weights = []
        
        for i, stats in self.key_stats.items():
            # Skip keys on cooldown
            if stats.cooldown_until and datetime.now() < stats.cooldown_until:
                continue
            available_keys.append(i)
            weights.append(stats.weight)
        
        # ✅ FIX: If no keys available, pick the one with earliest cooldown
        if not available_keys:
            print("⚠️ No available keys, picking key with earliest cooldown")
            earliest_key = min(self.key_stats.items(), key=lambda x: x[1].cooldown_until or datetime.min)
            return earliest_key[0]
        
        # ✅ FIX: If total weight is zero, use equal weights
        total_weight = sum(weights)
        if total_weight <= 0:
            print("⚠️ Total weight is zero, using equal distribution")
            return random.choice(available_keys)
        
        # Weighted random selection
        return random.choices(available_keys, weights=weights, k=1)[0]
    
    
    
    
    
    
    def _check_rate_limit(self, key_index: int) -> bool:
        stats = self.key_stats[key_index]
        now = datetime.now()
        
        if now - stats.rate_limit_reset > timedelta(minutes=1):
            stats.requests_this_minute = 0
            stats.rate_limit_reset = now
        
        if stats.requests_this_minute >= 60:
            return False
        
        stats.requests_this_minute += 1
        return True
    
    def _record_success(self, key_index: int, model: str, response_length: int = 0):
        stats = self.key_stats[key_index]
        stats.success_count += 1
        stats.last_used = datetime.now()
        
        self.total_requests += 1
        self.successful_requests += 1
        self._update_weights()
        
        print(f"✅ Key {key_index + 1} | Model: {model} | Success | Rate: {stats.success_rate:.1%}")
    
    def _record_failure(self, key_index: int, model: str, error_msg: str):
        stats = self.key_stats[key_index]
        stats.fail_count += 1
        stats.last_used = datetime.now()
        
        self.total_requests += 1
        self.failed_requests += 1
        
        model_key = f"{key_index}_{model}"
        self.model_failures[model_key]["count"] += 1
        self.model_failures[model_key]["last_fail"] = datetime.now()
        
        consecutive_failures = stats.fail_count - stats.success_count
        if consecutive_failures >= 3:
            cooldown_seconds = min(30, 5 * (consecutive_failures - 2))
            stats.cooldown_until = datetime.now() + timedelta(seconds=cooldown_seconds)
            print(f"⚠️ Key {key_index + 1} on cooldown for {cooldown_seconds}s")
        
        if "429" in error_msg or "quota" in error_msg.lower():
            stats.rate_limit_count += 1
            stats.cooldown_until = datetime.now() + timedelta(seconds=10)
            print(f"🚫 Key {key_index + 1} rate limited, cooldown 10s")
        
        print(f"❌ Key {key_index + 1} | Model: {model} | Failed: {error_msg[:80]}")
        self._update_weights()
    
    
    
    
    def reset_all_keys(self):
        """Reset all keys when they are all exhausted"""
        print("🔄 Resetting all API keys (removing cooldowns)")
        for i in self.key_stats:
            self.key_stats[i].cooldown_until = None
            self.key_stats[i].weight = 0.5
            self.key_stats[i].requests_this_minute = 0
        self._update_weights()    
    
    
    
    
    
    async def generate_stream(self, prompt: str, config: dict):
        """Stream generation with smart load balancing"""
        last_error = None
        
        # ✅ ADD THIS CHECK AT THE START
        all_on_cooldown = all(
            stats.cooldown_until and datetime.now() < stats.cooldown_until 
            for stats in self.key_stats.values()
        )
        if all_on_cooldown:
            print("⚠️ All keys on cooldown, resetting...")
            self.reset_all_keys()
        
        for attempt in range(3):
            key_index = self._select_key()
            api_key = self.api_keys[key_index]
            
            if not self._check_rate_limit(key_index):
                continue
            
            for model in self.models:
                try:
                    print(f"📡 Streaming | Key {key_index + 1} | Model: {model}")
                    
                    client = genai.Client(api_key=api_key)
                    
                    response = client.models.generate_content_stream(
                        model=model,
                        contents=prompt,
                        config=config
                    )
                    
                    # Use regular for loop (NOT async for)
                    first_chunk = None
                    for chunk in response:
                        if first_chunk is None:
                            first_chunk = chunk
                            print(f"✅ Model {model} working")
                        yield chunk
                    
                    if first_chunk:
                        self._record_success(key_index, model)
                        return
                        
                except Exception as e:
                    error_msg = str(e)
                    self._record_failure(key_index, model, error_msg)
                    last_error = e
                    
                    if "429" in error_msg or "quota" in error_msg.lower():
                        break
                    
                    continue
        
        raise Exception(f"All streaming attempts failed. Last error: {last_error}")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    async def generate_content(self, prompt: str, config: dict) -> str:
        """Generate content using smart load balancing"""
        last_error = None
        
        # ✅ ADD THIS CHECK AT THE START
        all_on_cooldown = all(
            stats.cooldown_until and datetime.now() < stats.cooldown_until 
            for stats in self.key_stats.values()
        )
        if all_on_cooldown:
            print("⚠️ All keys on cooldown, resetting...")
            self.reset_all_keys()
        
        for attempt in range(3):
            key_index = self._select_key()
            api_key = self.api_keys[key_index]
            
            if not self._check_rate_limit(key_index):
                print(f"⏭️ Key {key_index + 1} rate limited, selecting another...")
                continue
            
            for model in self.models:
                try:
                    print(f"🎯 Attempt {attempt + 1} | Key {key_index + 1} | Model: {model}")
                    
                    client = genai.Client(api_key=api_key)
                    
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config
                    )
                    
                    self._record_success(key_index, model, len(response.text))
                    return response.text
                    
                except Exception as e:
                    error_msg = str(e)
                    self._record_failure(key_index, model, error_msg)
                    last_error = e
                    
                    if "429" in error_msg or "quota" in error_msg.lower():
                        break
                    
                    continue
        
        raise Exception(f"All API keys exhausted. Last error: {last_error}")
    
    
    
    
    
    
    
    
    def get_stats(self) -> dict:
        stats = {
            "total_keys": len(self.api_keys),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / max(1, self.total_requests),
            "keys": {}
        }
        
        for i, key_stats in self.key_stats.items():
            stats["keys"][f"key_{i + 1}"] = {
                "success_count": key_stats.success_count,
                "fail_count": key_stats.fail_count,
                "success_rate": round(key_stats.success_rate, 3),
                "weight": round(key_stats.weight, 3),
                "on_cooldown": key_stats.cooldown_until and datetime.now() < key_stats.cooldown_until,
                "cooldown_until": key_stats.cooldown_until.isoformat() if key_stats.cooldown_until else None,
                "requests_this_minute": key_stats.requests_this_minute,
                "rate_limit_count": key_stats.rate_limit_count
            }
        
        return stats

# Initialize the smart load balancer
smart_balancer = SmartLoadBalancer()

class GeminiModelRouter:
    """Wrapper for the smart load balancer"""
    
    def __init__(self, balancer: SmartLoadBalancer):
        self.balancer = balancer
    
    async def generate_content(self, prompt: str, config: dict) -> str:
        return await self.balancer.generate_content(prompt, config)
    
    async def generate_stream(self, prompt: str, config: dict):
        async for chunk in self.balancer.generate_stream(prompt, config):
            yield chunk
    
    def get_stats(self) -> dict:
        return self.balancer.get_stats()

    
    

# Initialize the router with the smart balancer
model_router = GeminiModelRouter(smart_balancer)































# ============================================
# ========== ENVIRONMENT DETECTION ==========
# ============================================

# Detect if running in Docker/Render
IS_DOCKER = os.environ.get("RENDER") == "true" or os.path.exists("/.dockerenv")

# Use /tmp for temporary files in Docker/Render
if IS_DOCKER:
    THUMBNAIL_DIR = Path("/tmp/thumbnails")
    PREVIEWS_DIR = Path("/tmp/previews")
    TEMP_DIR = Path("/tmp/temp_thumbnails")
else:
    THUMBNAIL_DIR = Path("thumbnails")
    PREVIEWS_DIR = Path("previews")
    TEMP_DIR = Path("temp_thumbnails")

# Create directories
THUMBNAIL_DIR.mkdir(exist_ok=True, parents=True)
PREVIEWS_DIR.mkdir(exist_ok=True, parents=True)
TEMP_DIR.mkdir(exist_ok=True, parents=True)

print(f"📁 Environment: {'DOCKER/RENDER' if IS_DOCKER else 'LOCAL'}")
print(f"📁 Thumbnails dir: {THUMBNAIL_DIR}")
print(f"📁 Previews dir: {PREVIEWS_DIR}")
print(f"📁 Temp dir: {TEMP_DIR}")




load_dotenv()











# ========== CONFIGURATION ==========
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this")
SESSION_SECRET = os.getenv("SESSION_SECRET", "session-secret-key-change-this-too")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")













# Load from environment variable
cloudinary_url = os.environ.get("CLOUDINARY_URL", "")

if cloudinary_url:
    # Parse the URL
    match = re.search(r'cloudinary://([^:]+):([^@]+)@(.+)', cloudinary_url)
    if match:
        api_key = match.group(1)
        api_secret = match.group(2)
        cloud_name = match.group(3)
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        print(f"✅ Cloudinary configured from .env: {cloud_name}")
    else:
        print("❌ Failed to parse CLOUDINARY_URL")
else:
    print("⚠️ CLOUDINARY_URL not found in environment")







# ========== IMAGE UPLOAD TO CLOUDINARY ==========
async def upload_images_to_cloudinary(files: Dict[str, Any]) -> Dict[str, str]:
    """Upload all binary images to Cloudinary and return URL mapping"""
    image_urls = {}
    
    for file_path, content in list(files.items()):
        # Check if this is a binary image
        if isinstance(content, str) and content.startswith("__binary_base64__"):
            try:
                # Extract base64 data
                base64_data = content.replace("__binary_base64__", "")
                
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    f"data:image/jpeg;base64,{base64_data}",
                    folder="scorpio_projects",
                    public_id=file_path.replace('/', '_').replace('.', '_'),
                    overwrite=True
                )
                
                image_urls[file_path] = upload_result['secure_url']
                print(f"☁️ Uploaded to Cloudinary: {file_path}")
                
                # Replace the binary content with the URL
                files[file_path] = upload_result['secure_url']
                
            except Exception as e:
                print(f"❌ Failed to upload {file_path}: {e}")
    
    return image_urls





# Get DATABASE_URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# For local development, fallback to SQLite
if not DATABASE_URL:
    DATABASE_URL = "sqlite+aiosqlite:///./eaglecode.db"
    print(f"⚠️ No DATABASE_URL found, using SQLite: {DATABASE_URL}")
else:
    # Remove sslmode from URL (asyncpg doesn't support it as a query param)
    if "sslmode" in DATABASE_URL:
        # Remove the sslmode parameter
        import re
        DATABASE_URL = re.sub(r'\?sslmode=[^&]+', '', DATABASE_URL)
        DATABASE_URL = re.sub(r'&sslmode=[^&]+', '', DATABASE_URL)
        print(f"🔗 Removed sslmode from connection string")
    
    # Convert to asyncpg format for Neon PostgreSQL
    if "postgresql://" in DATABASE_URL and "+asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    print(f"🔗 Using Neon PostgreSQL database")



try:
    # Create engine with proper SSL configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        # For Neon PostgreSQL, SSL is handled automatically
        connect_args={
            "server_settings": {
                "application_name": "eaglecode_backend",
            }
        } if "postgresql" in DATABASE_URL else {}
    )
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    Base = declarative_base()
    
    print("✅ PostgreSQL engine configured successfully!")
    
    # ========== DEFINE ALL TABLES (METADATA ONLY - NO LARGE FILES) ==========
    
    # Projects table (metadata only - NO preview_html content)
    class Project(Base):
        __tablename__ = "projects"
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        name = Column(String, nullable=False, index=True)
        prompt = Column(Text, nullable=False)
        timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)
        user_id = Column(String, nullable=False, index=True)
        project_type = Column(String, nullable=True, index=True)
        file_count = Column(Integer, default=0)
        size_bytes = Column(Integer, default=0)
        is_public = Column(Boolean, default=False)
        version = Column(Integer, default=1)
        
        # ✅ Store ONLY URLs (large files go to Cloudinary)
        preview_url = Column(String(500), nullable=True)   # Cloudinary URL for HTML preview
        thumbnail_url = Column(String(500), nullable=True) # Cloudinary URL for thumbnail
        files_url = Column(String(500), nullable=True)     # Cloudinary URL for ZIP file

    # Project Files table (metadata only - NO file content)
    class ProjectFile(Base):
        __tablename__ = "project_files"
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        project_id = Column(String, nullable=False, index=True)
        file_path = Column(String, nullable=False)
        file_type = Column(String, nullable=True, index=True)
        size_bytes = Column(Integer, default=0)
        cloudinary_url = Column(String(500), nullable=True)  # URL to file on Cloudinary
        created_at = Column(DateTime, nullable=False, default=datetime.now)
        updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
        
        __table_args__ = (
            Index('idx_project_file_path', 'project_id', 'file_path', unique=True),
        )
    
    # Users table
    class User(Base):
        __tablename__ = "users"
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        email = Column(String, unique=True, nullable=False, index=True)
        username = Column(String, unique=True, nullable=False, index=True)
        password_hash = Column(String, nullable=False)
        avatar_url = Column(String, nullable=True)
        created_at = Column(DateTime, nullable=False, default=datetime.now)
        updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Sessions table
    class Session(Base):
        __tablename__ = "sessions"
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        user_id = Column(String, nullable=False, index=True)
        token = Column(String, unique=True, nullable=False, index=True)
        expires_at = Column(DateTime, nullable=False, index=True)
        created_at = Column(DateTime, nullable=False, default=datetime.now)
        ip_address = Column(String, nullable=True)
        user_agent = Column(String, nullable=True)
    
    # API Keys table
    class ApiKey(Base):
        __tablename__ = "api_keys"
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        user_id = Column(String, nullable=False, index=True)
        name = Column(String, nullable=False)
        key = Column(String, unique=True, nullable=False, index=True)
        created_at = Column(DateTime, nullable=False, default=datetime.now)
        last_used_at = Column(DateTime, nullable=True)
        expires_at = Column(DateTime, nullable=True)
        is_active = Column(Boolean, default=True, index=True)
    
    # User Credits table
    class UserCredits(Base):
        __tablename__ = "user_credits"
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(String, nullable=False, unique=True, index=True)
        plan = Column(String, default="free", index=True)
        daily_credits_used = Column(Integer, default=0)
        daily_reset_date = Column(Date, nullable=False, index=True)
        monthly_credits_used = Column(Integer, default=0)
        monthly_reset_date = Column(Date, nullable=False, index=True)
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Templates table (small files only)
    class Template(Base):
        __tablename__ = "templates"
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        name = Column(String, nullable=False, index=True)
        description = Column(Text, nullable=True)
        category = Column(String, nullable=False, index=True)
        files = Column(Text, nullable=False)  # JSON string (small)
        preview_html = Column(Text, nullable=True)  # Small preview HTML
        icon = Column(String, nullable=True)
        created_at = Column(DateTime, nullable=False, default=datetime.now)
        user_id = Column(String, default="default", index=True)
        usage_count = Column(Integer, default=0, index=True)
    
    # Upgrade Requests table
    class UpgradeRequest(Base):
        __tablename__ = "upgrade_requests"
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        user_id = Column(String, nullable=False, index=True)
        user_email = Column(String, nullable=False, index=True)
        user_name = Column(String, nullable=True)
        requested_plan = Column(String, nullable=False, index=True)
        message = Column(Text, nullable=True)
        status = Column(String, default="pending", index=True)
        admin_notes = Column(Text, nullable=True)
        payment_screenshot_url = Column(String(500), nullable=True)  # ✅ Add this line
        email_sent = Column(Boolean, default=False)  # ✅ NEW: Track if email was sent
        email_sent_at = Column(DateTime, nullable=True)  # ✅ NEW: When email was sent
        created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)
        updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    async def init_db():
        """Initialize database tables"""
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                print("✅ All tables verified/created successfully!")
                
                # For PostgreSQL, list tables
                if "postgresql" in DATABASE_URL:
                    result = await conn.execute(
                        text("""
                            SELECT tablename 
                            FROM pg_tables 
                            WHERE schemaname = 'public'
                            ORDER BY tablename
                        """)
                    )
                else:
                    # For SQLite
                    result = await conn.execute(
                        text("""
                            SELECT name FROM sqlite_master 
                            WHERE type='table' 
                            ORDER BY name
                        """)
                    )
                
                tables = result.fetchall()
                if tables:
                    print("\n📚 Existing tables in database:")
                    for table in tables:
                        print(f"  - {table[0]}")
                else:
                    print("\n📚 No tables found, they will be created as needed")
                        
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            raise
    
    print("✅ Database configured successfully!")
    
except Exception as e:
    print(f"❌ Failed to configure database: {e}")
    engine = None
    AsyncSessionLocal = None
    Base = None
    Project = None
    ProjectFile = None
    User = None
    Session = None
    ApiKey = None
    Template = None
    UserCredits = None
    UpgradeRequest = None
    async def init_db():
        print("⚠️ Database not available")










# ========== SECURITY SETUP ==========
security = HTTPBearer()







async def get_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    db = client["eaglecode"]
    try:
        yield db
    finally:
        client.close()







# ========== ADMIN AUTH FUNCTION (ADD THIS HERE) ==========
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Check if the current user is an admin"""
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, os.getenv("JWT_SECRET", "secret"), algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        # Get database connection
        db = await anext(get_db())
        
        # Check if user exists and is admin
        from bson import ObjectId
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user or user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )








# ========== CREATE DEPLOYMENT FILES (TEMPORARY, DOESN'T MODIFY ORIGINAL) ==========
def create_deployment_files(original_files: Dict[str, Any], image_urls: Dict[str, str]) -> Dict[str, Any]:
    """Create TEMPORARY deployment files with Cloudinary URLs - original files unchanged"""
    
    deployment_files = {}
    
    for file_path, content in original_files.items():
        # Skip preview_html and metadata
        if file_path == "preview_html" or file_path == "__image_urls__":
            continue
        
        # Skip binary images entirely (they're on Cloudinary now)
        if isinstance(content, str) and content.startswith("__binary_base64__"):
            continue
        
        # For text files, replace image paths with Cloudinary URLs
        if isinstance(content, str):
            updated_content = content
            for local_path, cloudinary_url in image_urls.items():
                # Replace /images/image_1.jpg with Cloudinary URL
                public_path = "/" + local_path.replace("public/", "")
                if public_path in updated_content:
                    updated_content = updated_content.replace(public_path, cloudinary_url)
                    print(f"  🔄 {file_path}: {public_path} -> {cloudinary_url[:60]}...")
            deployment_files[file_path] = updated_content
        else:
            deployment_files[file_path] = content
    
    print(f"📦 Created {len(deployment_files)} deployment files (original files unchanged)")
    return deployment_files













def extract_brand_name(files: dict) -> str:
    """Extract brand name from Navigation.tsx"""
    nav_content = files.get("components/Navigation.tsx", "")
    
    if not nav_content:
        return None
    
    # Pattern for: <Link ...> <Icon /> Brand Name </Link>
    match = re.search(r'<Link[^>]*href=["\']/["\'][^>]*>.*?>(.*?)</Link>', nav_content, re.DOTALL)
    if match:
        content = match.group(1)
        # Remove the icon/SVG part
        content = re.sub(r'<[^>]+>', '', content)  # Remove any HTML tags
        content = content.strip()
        # Brand name should be the last part after the icon
        words = content.split()
        if words:
            # Take the last 1-3 words as brand name
            brand = ' '.join(words[-3:])
            if brand and len(brand) > 1 and len(brand) < 50:
                print(f"🏷️ Extracted brand name: {brand}")
                return brand
    
    return None


















# ========== UPDATE IMAGE REFERENCES IN CODE ==========
async def update_image_references_in_code(files: Dict[str, Any], image_urls: Dict[str, str]) -> Dict[str, Any]:
    """Update image references in HTML/CSS/JS/TSX files to use Cloudinary URLs"""
    
    updated_count = 0
    
    for file_path, content in files.items():
        if not isinstance(content, str):
            continue
        
        # Skip binary files
        if content.startswith("__binary_base64__"):
            continue
        
        # Skip preview_html (handled separately)
        if file_path == "preview_html":
            continue
        
        original_content = content
        
        # Replace local image paths with Cloudinary URLs
        for local_path, cloudinary_url in image_urls.items():
            # Get the public path (e.g., "public/images/image_1.jpg" -> "/images/image_1.jpg")
            public_path = "/" + local_path.replace("public/", "")
            
            # Replace in content (both src and href attributes)
            if public_path in content:
                content = content.replace(public_path, cloudinary_url)
                print(f"  🔄 Replaced {public_path} in {file_path}")
                updated_count += 1
            
            # Also replace without leading slash
            alt_path = local_path.replace("public/", "")
            if alt_path in content:
                content = content.replace(alt_path, cloudinary_url)
                print(f"  🔄 Replaced {alt_path} in {file_path}")
        
        if content != original_content:
            files[file_path] = content
    
    print(f"📝 Updated {updated_count} image references in code files")
    return files





















# ========== NAME TRACKING SYSTEM ==========
class NameTracker:
    """Track used project names to prevent duplicates across all sessions"""
    
    def __init__(self, storage_file="used_names.json"):
        self.storage_file = storage_file
        self.used_names = set()
        self.name_history = []
        self.load_names()
    
    def load_names(self):
        """Load used names from JSON file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.used_names = set(data.get("used_names", []))
                    self.name_history = data.get("history", [])
                print(f"📚 Loaded {len(self.used_names)} used names from {self.storage_file}")
            else:
                print(f"📚 No existing name tracking file, starting fresh")
        except Exception as e:
            print(f"⚠️ Error loading names: {e}")
            self.used_names = set()
            self.name_history = []
    
    def save_names(self):
        """Save used names to JSON file"""
        try:
            data = {
                "used_names": list(self.used_names),
                "history": self.name_history[-100:],
                "total_count": len(self.used_names),
                "last_updated": datetime.now().isoformat()
            }
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved {len(self.used_names)} used names to {self.storage_file}")
        except Exception as e:
            print(f"⚠️ Error saving names: {e}")
    
    def is_name_used(self, name: str) -> bool:
        """Check if a name has been used before"""
        return name.lower() in self.used_names
    
    def add_name(self, name: str, project_type: str = "", user_prompt: str = ""):
        """Add a name to the tracking system"""
        name_lower = name.lower()
        if name_lower not in self.used_names:
            self.used_names.add(name_lower)
            self.name_history.append({
                "name": name,
                "project_type": project_type,
                "user_prompt": user_prompt[:100],
                "timestamp": datetime.now().isoformat()
            })
            self.save_names()
            print(f"✨ Added new name to tracker: {name}")
            return True
        return False
    
    def generate_unique_name(self, project_type: str = "school", user_prompt: str = "") -> str:
        """Generate a truly unique name that hasn't been used before"""
        
        # First, check if user specified a name in the prompt
        name_patterns = [
            r'called\s+["\']([^"\']+)["\']',
            r'named\s+["\']([^"\']+)["\']',
            r'titled\s+["\']([^"\']+)["\']',
            r'name\s+is\s+["\']([^"\']+)["\']',
            r'called\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'named\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_prompt, re.IGNORECASE)
            if match:
                custom_name = match.group(1).strip()
                if len(custom_name) < 40 and not custom_name.lower() in ['website', 'site', 'app', 'project']:
                    if not self.is_name_used(custom_name):
                        print(f"📝 Using user-specified name: {custom_name}")
                        self.add_name(custom_name, project_type, user_prompt)
                        return custom_name
                    else:
                        print(f"⚠️ User-specified name '{custom_name}' already used, generating new one")
        
        # Expanded word banks
        adjectives = [
            "Horizon", "Starlight", "Evergreen", "Radiant", "Luminous", "Noble", "Victor", "Summit",
            "Crest", "Peak", "Valley", "River", "Lake", "Mountain", "Ocean", "Bay", "Harbor", "Haven",
            "Refuge", "Sanctuary", "Oasis", "Grove", "Meadow", "Field", "Garden", "Park", "Square",
            "Plaza", "Court", "Hall", "House", "Manor", "Estate", "Lodge", "Inn", "Crystal", "Serene",
            "Vibrant", "Heritage", "Legacy", "Pioneer", "Urban", "Modern", "Elite", "Artisan",
            "Rustic", "Industrial", "Coastal", "Aurora", "Ember", "Whisper", "Shadow", "Phoenix",
            "Eclipse", "Nova", "Comet", "Orion", "Vega", "Celestial", "Mystic", "Enchanted", "Golden",
            "Silver", "Bronze", "Iron", "Steel", "Maple", "Oak", "Willow", "Cedar", "Pine", "Birch",
            "Aspen", "Holly", "Ivy", "Rose", "Lily", "Iris", "Violet", "Crimson", "Scarlet", "Amber",
            "Jade", "Ruby", "Sapphire", "Emerald", "Diamond", "Pearl", "Onyx", "Opal", "Topaz",
            "Azure", "Cerulean", "Indigo", "Magenta", "Coral", "Ivory", "Ebony", "Platinum"
        ]
        
        nouns = [
            "Valley", "River", "Mountain", "Ocean", "Bay", "Peak", "Summit", "Ridge", "Hill", "Meadow",
            "Forest", "Lake", "Harbor", "Coast", "Heights", "Gardens", "Park", "Square", "Point", "View",
            "Forge", "Works", "Collective", "Republic", "Garage", "Studio", "Atelier", "Workshop", "Lab",
            "Hub", "Center", "Loft", "Foundry", "Mill", "Factory", "Warehouse", "Tower", "Spire",
            "Citadel", "Fortress", "Castle", "Palace", "Manor", "Villa", "Cottage", "Cabin", "Lodge",
            "Retreat", "Sanctuary", "Haven", "Oasis", "Paradise", "Garden", "Orchard", "Vineyard",
            "Grove", "Woods", "Falls", "Cascade", "Rapids", "Stream", "Creek", "Brook", "Pond"
        ]
        
        business_types = {
            "school": ["Academy", "School", "Institute", "Center", "Hub", "Learning", "College Prep", "University", "Campus"],
            "coffee": ["Roastery", "Coffee Co.", "Brew", "Cafe", "Beanery", "Coffee House", "Roast", "Roasters"],
            "hotel": ["Resort", "Hotel", "Inn", "Lodge", "Suites", "Retreat", "Getaway", "Spa", "Villas"],
            "gym": ["Fitness", "Gym", "Training Center", "Athletic Club", "Strength", "Performance", "Athletics"],
            "restaurant": ["Bistro", "Kitchen", "Dining", "Restaurant", "Eatery", "Tavern", "Grill", "Table"],
            "portfolio": ["Studio", "Creative", "Design", "Portfolio", "Agency", "Collective", "Lab"],
            "ecommerce": ["Market", "Store", "Shop", "Goods", "Emporium", "Marketplace", "Boutique"]
        }
        
        # Detect project type from user prompt
        prompt_lower = user_prompt.lower()
        detected_type = project_type.lower()
        
        if "school" in prompt_lower or "academy" in prompt_lower or "education" in prompt_lower:
            detected_type = "school"
        elif "coffee" in prompt_lower or "roastery" in prompt_lower or "brew" in prompt_lower:
            detected_type = "coffee"
        elif "hotel" in prompt_lower or "resort" in prompt_lower or "inn" in prompt_lower:
            detected_type = "hotel"
        elif "gym" in prompt_lower or "fitness" in prompt_lower or "workout" in prompt_lower:
            detected_type = "gym"
        elif "restaurant" in prompt_lower or "bistro" in prompt_lower or "cafe" in prompt_lower:
            detected_type = "restaurant"
        elif "portfolio" in prompt_lower or "creative" in prompt_lower:
            detected_type = "portfolio"
        elif "shop" in prompt_lower or "store" in prompt_lower or "ecommerce" in prompt_lower:
            detected_type = "ecommerce"
        
        types = business_types.get(detected_type, business_types["school"])
        
        # Try to generate a unique name
        max_attempts = 100
        for attempt in range(max_attempts):
            structure = random.choice([1, 2, 3])
            
            if structure == 1:
                adj = random.choice(adjectives)
                biz_type = random.choice(types)
                name = f"{adj} {biz_type}"
            elif structure == 2:
                adj = random.choice(adjectives)
                noun = random.choice(nouns)
                name = f"{adj} {noun}"
            else:
                adj = random.choice(adjectives)
                noun = random.choice(nouns)
                biz_type = random.choice(types)
                name = f"{adj} {noun} {biz_type}"
            
            if not self.is_name_used(name) and len(name) < 45:
                self.add_name(name, detected_type, user_prompt)
                print(f"✨ Generated unique name: {name}")
                return name
        
        # Ultimate fallback
        fallback = f"{random.choice(adjectives)} {random.choice(types)} {datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.add_name(fallback, detected_type, user_prompt)
        return fallback
    
    def get_stats(self):
        """Get statistics about name usage"""
        return {
            "total_unique_names": len(self.used_names),
            "history_count": len(self.name_history),
            "recent_names": self.name_history[-10:]
        }

# Initialize the name tracker
name_tracker = NameTracker()







active_project_connections = []

























@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if DATABASE_URL:
        await init_db()
        print("🚀 Neon database ready")
    yield
    # Shutdown
    if DATABASE_URL:
        await engine.dispose()
        print("👋 Database connection closed")





# Update your app initialization:
app = FastAPI(title="Scorpio Architecture Engine", lifespan=lifespan)









# Mount the directory
app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")
# ========================================










# Add SessionMiddleware FIRST
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "session-secret-key-change-this"))



# Initialize OAuth and pass to router
init_oauth(app)

# Include router
app.include_router(auth_router)




# Enable CORS - Production ready
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://eaglecode.vercel.app",  # Your Vercel frontend URL
        "http://localhost:3000",                    # Local development
        "https://eaglecode2-2.onrender.com",          # Your backend itself
        
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)







# Image cache for storing downloaded images to avoid duplicate downloads
IMAGE_CACHE = {}



























async def search_free_images(query: str, count: int = 2, previous_terms: List[str] = None, search_type: str = "general") -> List[Dict]:
    """
    Search for free-to-use images using Pexels API with varied search terms.
    Returns maximum 2 images for faster performance and smaller project size.
    
    search_type: "general", "person", "portrait", "team"
    """
    previous_terms = previous_terms or []
    
    # Generate varied search terms based on query AND search_type
    search_terms = generate_varied_search_terms(query, previous_terms, search_type)
    
    print(f"🔍 Generated search terms for {search_type}: {search_terms[:3]}")
    
    # Try Pexels API first
    api_key = os.environ.get("PEXELS_API_KEY")
    all_results = []
    used_terms = []
    
    for search_term in search_terms[:4]:  # Try up to 4 different terms
        if len(all_results) >= count:
            break
            
        if api_key:
            try:
                headers = {"Authorization": api_key}
                random_page = random.randint(1, 2)
                
                # Build params based on search_type
                params = {
                    "query": search_term, 
                    "per_page": count, 
                    "page": random_page
                }
                
                # Add orientation for person searches
                if search_type in ["person", "portrait", "team"]:
                    params["orientation"] = "portrait"
                    params["size"] = "large"
                    print(f"👤 Person search mode - using portrait orientation")
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.pexels.com/v1/search",
                        headers=headers,
                        params=params,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for photo in data.get("photos", []):
                            img_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large")
                            
                            if len(all_results) >= count:
                                break
                            
                            # For person searches, verify photo contains people
                            if search_type in ["person", "portrait", "team"]:
                                # Check if photo likely contains people
                                alt_text = photo.get("alt", "").lower()
                                photographer = photo.get("photographer", "").lower()
                                
                                people_keywords = ["person", "people", "man", "woman", "face", "portrait", "trainer", "coach", "athlete"]
                                has_people = any(keyword in alt_text or keyword in photographer for keyword in people_keywords)
                                
                                if not has_people and search_type == "person":
                                    print(f"  ⏭️ Skipping non-person photo for '{search_term}'")
                                    continue
                            
                            all_results.append({
                                "url": img_url,
                                "source": "Pexels",
                                "attribution": f"Photo by {photo.get('photographer', 'Unknown')} on Pexels",
                                "license": "Free to use under Pexels License",
                                "photographer_url": photo.get("photographer_url"),
                                "alt": photo.get("alt", search_term),
                                "search_term": search_term,
                                "type": search_type
                            })
                            used_terms.append(search_term)
                        
                        if all_results:
                            print(f"✅ Found {len(all_results)} images via Pexels API for {search_type}")
                                    
            except Exception as e:
                print(f"⚠️ Pexels API error for '{search_term}': {e}")
                continue
    
    if all_results:
        random.shuffle(all_results)
        print(f"✅ Total {len(all_results[:count])} {search_type} images found")
        return all_results[:count]
    
    print(f"🔍 Falling back to web scraping for '{query}'")
    fallback_results = await search_free_images_fallback(query, count)
    
    if not fallback_results:
        print(f"⚠️ No images found for '{query}', will use styled gradient cards instead")
        return []
    
    return fallback_results[:count]


def generate_varied_search_terms(query: str, previous_terms: List[str] = None, search_type: str = "general") -> List[str]:
    """
    Generate varied search terms based on project type and search_type.
    Returns fewer terms (max 6) for faster searching.
    """
    previous_terms = previous_terms or []
    query_lower = query.lower()
    
    # Word banks for variety
    adjectives = ["modern", "beautiful", "stunning", "elegant", "vibrant", "cozy", 
                  "luxury", "rustic", "minimal", "colorful", "dramatic", "peaceful",
                  "dynamic", "fresh", "warm", "cool", "bright"]
    
    # Person-specific adjectives
    person_adjectives = ["professional", "friendly", "confident", "smiling", "fit", 
                         "energetic", "experienced", "expert", "certified", "passionate"]
    
    # Project type specific keywords
    type_keywords = {
        "hotel": ["lobby", "pool", "spa", "restaurant", "suite", "terrace"],
        "coffee": ["beans", "barista", "counter", "pastry", "espresso", "latte"],
        "school": ["classroom", "library", "cafeteria", "playground", "campus"],
        "gym": ["weights", "treadmill", "yoga", "training", "fitness"],
        "restaurant": ["dining", "kitchen", "bar", "table", "food", "chef"],
        "portfolio": ["workspace", "studio", "design", "creative", "office"],
        "ecommerce": ["product", "display", "packaging", "store", "shop"],
        "tech": ["dashboard", "interface", "coding", "software", "modern"],
        "saas": ["dashboard", "analytics", "platform", "interface", "cloud"],
        # Person/people specific
        "trainers": ["personal trainer", "fitness coach", "gym instructor", "trainer portrait"],
        "coaches": ["sports coach", "team coach", "trainer portrait", "professional coach"],
        "team": ["team photo", "group portrait", "staff", "employees together"],
        "staff": ["professional portrait", "employee headshot", "team member", "worker"]
    }
    
    # Detect if we need person images
    needs_people = search_type in ["person", "portrait", "team"]
    
    if needs_people:
        # Person-specific search terms
        keywords = ["trainer", "coach", "instructor", "fitness expert", "personal trainer", "athlete"]
        adj_list = person_adjectives
    else:
        # Detect project type for general images
        detected_type = "general"
        for ptype in type_keywords.keys():
            if ptype in query_lower:
                detected_type = ptype
                break
        keywords = type_keywords.get(detected_type, ["design", "space", "interior", "exterior", "modern"])
        adj_list = adjectives
    
    search_terms = []
    
    if needs_people:
        # Method for person searches
        roles = ["trainer", "coach", "instructor", "fitness expert", "personal trainer"]
        for i in range(3):
            adj = random.choice(adj_list)
            role = random.choice(roles)
            term = f"{adj} {role} portrait"
            if term not in search_terms:
                search_terms.append(term)
        
        # Add specific person terms
        person_terms = ["professional headshot", "smiling coach", "trainer at work", "fitness portrait"]
        for term in person_terms[:2]:
            if term not in search_terms:
                search_terms.append(term)
    else:
        # Method 1: Adjective + Keyword
        for i in range(3):
            adj = random.choice(adj_list)
            kw = random.choice(keywords)
            term = f"{adj} {kw}"
            if term not in search_terms:
                search_terms.append(term)
        
        # Method 2: Keyword + Style
        styles = ["photography", "background", "stock photo"]
        for i in range(2):
            kw = random.choice(keywords)
            style = random.choice(styles)
            term = f"{kw} {style}"
            if term not in search_terms:
                search_terms.append(term)
        
        # Method 3: Original query
        if query not in search_terms:
            search_terms.append(query)
    
    # Remove used terms
    if previous_terms:
        search_terms = [t for t in search_terms if t not in previous_terms]
    
    # Ensure we have at least one term
    if not search_terms:
        if needs_people:
            search_terms = ["professional trainer portrait", "fitness coach", "smiling instructor"]
        else:
            search_terms = [query, "modern design", "beautiful background"]
    
    return search_terms[:6]

























async def search_free_images_fallback(query: str, count: int = 3) -> List[Dict]:
    """
    Fallback method using web scraping when API is unavailable
    """
    sources = [
        {"name": "Unsplash", "url": f"https://unsplash.com/s/photos/{query.replace(' ', '-')}"},
        {"name": "Pexels", "url": f"https://www.pexels.com/search/{query.replace(' ', '%20')}/"},
        {"name": "Pixabay", "url": f"https://pixabay.com/images/search/{query.replace(' ', '%20')}/"}
    ]

    results = []

    for source in sources:
        try:
            response = requests.get(
                source["url"],
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=10
            )
            soup = BeautifulSoup(response.text, 'html.parser')

            if source["name"] == "Unsplash":
                images = soup.find_all('img', {'srcset': True})[:count]
                for img in images:
                    src = img['srcset'].split('?')[0].split(' ')[0]
                    if src.startswith('http') and 'plus.unsplash.com' not in src:
                        results.append({
                            "url": src,
                            "source": source["name"],
                            "attribution": f"Photo by Unsplash",
                            "license": "Free to use under Unsplash License"
                        })
            elif source["name"] == "Pexels":
                images = soup.find_all('img', {'src': True})[:count]
                for img in images:
                    if 'pexels-photo' in img.get('src', ''):
                        results.append({
                            "url": img['src'].split('?')[0],
                            "source": source["name"],
                            "attribution": f"Photo by Pexels",
                            "license": "Free to use under Pexels License"
                        })
            elif source["name"] == "Pixabay":
                images = soup.find_all('img', {'data-lazy': True})[:count]
                for img in images:
                    src = img.get('data-lazy', '').split('?')[0]
                    if src.startswith('http'):
                        results.append({
                            "url": src,
                            "source": source["name"],
                            "attribution": f"Image by Pixabay",
                            "license": "Free for commercial use under Pixabay License"
                        })

            if len(results) >= count:
                break
        except Exception as e:
            print(f"Error searching {source['name']}: {e}")
            continue

    return results[:count]















async def get_image_as_base64(url: str) -> str:
    """
    Download an image and return it as a base64 encoded string
    Uses caching to avoid duplicate downloads
    """
    # Create a unique key for the URL
    url_key = hashlib.md5(url.encode()).hexdigest()

    # Check cache first
    if url_key in IMAGE_CACHE:
        return IMAGE_CACHE[url_key]

    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        # Convert to base64
        img = Image.open(BytesIO(response.content))

        # Resize if too large
        if max(img.size) > 2000:
            ratio = 2000 / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # Convert RGBA to RGB for JPEG compatibility
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        buffered = BytesIO()
        # CHANGE: Use JPEG format with quality setting
        img.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Cache the result
        IMAGE_CACHE[url_key] = img_str
        return img_str
    except Exception as e:
        print(f"Error downloading image {url}: {e}")
        return ""







def generate_placeholder_image(width: int = 800, height: int = 600, text: str = "") -> str:
    """
    Generate a simple SVG placeholder image
    """
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <rect width="100%" height="100%" fill="#f0f0f0"/>
        <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#999" font-size="20">
            {text or f"{width}x{height}"}
        </text>
        <rect x="0" y="0" width="{width}" height="30" fill="#ddd"/>
        <text x="20" y="20" fill="#666" font-size="14">Image Placeholder</text>
    </svg>"""

    # Convert SVG to base64
    svg_bytes = svg.encode('utf-8')
    return f"data:image/svg+xml;base64,{base64.b64encode(svg_bytes).decode('utf-8')}"




















async def generate_preview_internal(files: Dict[str, Any], project_name: str) -> Dict[str, Any]:
    """Generate fully interactive HTML preview using AI"""
    try:
        print(f"🤖 AI generating full equivalent HTML preview for: {project_name}")

        # ========== COLLECT NAVIGATION ==========
        nav_content = files.get("components/Navigation.tsx", "")
        if not nav_content:
            for fp, content in files.items():
                if "Navigation" in fp and fp.endswith((".tsx", ".jsx")):
                    nav_content = content
                    break

        # Extract brand and navigation links
        brand_name = project_name
        nav_links = []
        
        if nav_content:
            brand_match = re.search(r'<Link[^>]*href="/"[^>]*>.*?<[^>]+>([^<]+)</', nav_content, re.DOTALL)
            if brand_match:
                brand_name = brand_match.group(1).strip()
            
            link_pattern = r'<Link\s+href="/([^"]+)"[^>]*>([^<]+)</Link>'
            nav_links = [(href, text.strip()) for href, text in re.findall(link_pattern, nav_content) 
                        if href != "/" and text.strip() and text.strip() != brand_name]
        
        print(f"📍 Navigation: {brand_name} -> {nav_links}")

        # ========== PROCESS PAGES AND EXPAND MAP LOOPS ==========
        page_contents = {}
        
        def expand_map_loop(content: str) -> str:
            """Convert JSX .map() loops to static HTML"""
            import re
            
            pattern = r'\{\[([^\]]+)\]\s*\.map\(\(?([^)]+)\)?\s*=>\s*\(([\s\S]*?)\)\s*\)\}'
            
            def replace_map(match):
                array_expr = match.group(1)
                var_name = match.group(2)
                template = match.group(3)
                
                items = [x.strip() for x in array_expr.split(',') if x.strip()]
                if not items:
                    return match.group(0)
                
                result = ""
                for idx, item in enumerate(items):
                    item_html = template
                    item_num = int(item) if item.isdigit() else idx + 1
                    
                    item_html = item_html.replace(f'{{{var_name}}}', str(item_num))
                    item_html = item_html.replace(f'{{ {var_name} }}', str(item_num))
                    item_html = item_html.replace('{i}', str(item_num))
                    item_html = item_html.replace('{idx}', str(idx + 1))
                    item_html = item_html.replace('{index}', str(idx + 1))
                    item_html = re.sub(r'\{[^}]+\}', '', item_html)
                    item_html = item_html.replace('className=', 'class=')
                    item_html = re.sub(r'\s+key=["\'][^"\']*["\']', '', item_html)
                    item_html = re.sub(r'\s+key=\{[\s\S]*?\}', '', item_html)
                    
                    result += item_html
                
                return result
            
            while re.search(pattern, content):
                content = re.sub(pattern, replace_map, content)
            
            return content
        
        for file_path, content in files.items():
            if file_path.endswith(("page.tsx", "page.jsx")):
                route = file_path.replace("app/", "").replace("/page.tsx", "").replace("/page.jsx", "").strip("/")
                route_name = route or "home"
                
                clean = content
                clean = re.sub(r'import\s+.*?from\s+["\'][^"\']+["\'];?\s*', '', clean, flags=re.DOTALL)
                clean = re.sub(r'export\s+default\s+function\s+\w+\s*\([^)]*\)\s*{?', '', clean)
                clean = re.sub(r'export\s+default\s+const\s+\w+\s*=\s*\(\)\s*=>\s*{?', '', clean)
                
                match = re.search(r'return\s*\(\s*([\s\S]*?)\s*\)\s*;', clean, re.DOTALL)
                if not match:
                    match = re.search(r'\(\s*<[\w\s\S]+?>\s*\)', clean, re.DOTALL)
                
                if match:
                    jsx = match.group(1) if match.lastindex else match.group(0)
                    jsx = expand_map_loop(jsx)
                    jsx = re.sub(r'^<div\s+className="container\s+mx-auto[^>]*>\s*', '', jsx)
                    jsx = re.sub(r'\s*</div>\s*$', '', jsx)
                    jsx = re.sub(r'\{[^}]+\}', '', jsx)
                    jsx = jsx.replace('className=', 'class=')
                    
                    page_contents[route_name] = jsx[:4000]
                    print(f"📄 {route_name}: {len(jsx)} chars")
                else:
                    page_contents[route_name] = clean[:3000]
                    print(f"⚠️ Could not extract content from {route_name}")

        # Ensure home page exists
        if "home" not in page_contents:
            page_contents["home"] = f'<div class="text-center py-20"><h1 class="text-6xl font-bold gradient-text">{brand_name}</h1><p class="text-gray-400 mt-4 text-lg">Welcome to our digital space.</p></div>'

        # Add missing navigation pages
        for href, label in nav_links:
            if href not in page_contents:
                page_contents[href] = f'<div class="text-center py-20"><h1 class="text-5xl font-bold gradient-text">{label}</h1><p class="text-gray-400 mt-4">Explore our {label.lower()} collection.</p></div>'

        # Global CSS
        global_css = files.get("app/globals.css", "")[:2000]




















        # Available images
        available_images = [f for f in files.keys() if f.startswith("public/images/")]
        image_paths = [f"/{f.replace('public/', '')}" for f in available_images]

































        # Build image instruction - STRICT
        image_instruction = ""
        if image_paths:
            image_instruction = f"""
🚨 CRITICAL - IMAGE REQUIREMENT 🚨
You MUST use ONLY these exact image paths. DO NOT use Unsplash, Pexels, or any external URLs.

AVAILABLE IMAGES (use these EXACT paths):
{image_paths}

REQUIREMENTS:
- Use src="/images/image_1.jpg" for the main hero image
- Use src="/images/image_2.jpg" for secondary images
- DO NOT generate any other image URLs
- DO NOT use images.unsplash.com or any external domains
-

Example of CORRECT usage:
<img src="/images/image_1.jpg" alt="Hero" class="w-full h-96 object-cover rounded-xl" />

Example of WRONG usage (NEVER do this):
<img src="https://images.unsplash.com/..." />
"""
            















        # ========== LET AI GENERATE PREVIEW ==========
        prompt = f"""You are an expert frontend developer. Create a STUNNING, MODERN, FULLY INTERACTIVE standalone HTML preview.

Project Name: {brand_name}

NAVIGATION LINKS: {json.dumps(nav_links, indent=2)}

PAGE CONTENTS (use EXACTLY these):
{json.dumps(page_contents, indent=2)}

{image_instruction}

DESIGN REQUIREMENTS:
- **NORMAL SCROLLING NAVIGATION BAR** - The navbar scrolls away with the page (NOT sticky, NOT fixed)
- Regular navigation bar at the top (position: relative, NOT fixed)
- Brand name on left (clickable, goes to home)
- Navigation links on right
- Home page visible by default
- Smooth page transitions
- Dark theme with purple-pink gradients
- Mobile responsive with hamburger menu




🚨 FOOTER (REQUIRED ON EVERY PAGE):
- Footer.tsx component MUST be imported and used on ALL pages
- Footer appears at the bottom of every page
- Contains: Quick links, Contact info, Social media, Copyright
- Same footer across all pages (consistent)

PAGE STRUCTURE:
- Home page visible by default
- Smooth page transitions between routes
- Dark theme with purple-pink gradients throughout








🚨🚨🚨 CRITICAL - NO INVENTED CONTENT 🚨🚨🚨
The HTML preview is for TESTING ONLY. The actual Vercel deployment will use the Next.js files.
DO NOT add invented taglines, fake brand names, or marketing text like:
- "Sanctuary Design"
- "Crafting high-end digital experiences"
- "neon-infused aesthetics"
- "precision design"
- Any text NOT present in the PAGE CONTENTS above



The home page content MUST come ONLY from the PAGE CONTENTS provided.
If the user didn't specify a tagline, DO NOT invent one.






Return ONLY complete HTML. No explanations."""

        response_text = await model_router.generate_content(
            prompt=prompt,
            config={"temperature": 0.15, "max_output_tokens": 48000}
        )

        preview_html = clean_html_response(response_text)

        if not preview_html.lower().startswith("<!doctype"):
            preview_html = "<!DOCTYPE html>\n" + preview_html

        # ========== INJECT BASE64 IMAGES ==========
        print("🖼️ Injecting images into preview...")
        
        for file_key, content in files.items():
            if not file_key.startswith("public/images/") or not isinstance(content, str):
                continue
            if not content.startswith("__binary_base64__"):
                continue
            
            public_path = "/" + file_key[len("public/"):]
            raw_b64 = content[len("__binary_base64__"):]
            data_uri = f"data:image/jpeg;base64,{raw_b64}"
            
            count = 0
            preview_html, cnt = re.subn(f'src="{public_path}"', f'src="{data_uri}"', preview_html)
            count += cnt
            preview_html, cnt = re.subn(f"src='{public_path}'", f'src="{data_uri}"', preview_html)
            count += cnt
            preview_html, cnt = re.subn(public_path, data_uri, preview_html)
            count += cnt
            
            if count > 0:
                print(f"  ✅ Injected {public_path} ({count} references)")
            else:
                print(f"  ⚠️ No references found for {public_path}")










        # ========== NO SPACING INJECTION NEEDED - Navbar is NOT fixed ==========
        # The navbar scrolls normally with the page, so no padding-top required
        
        print(f"✅ Preview generated! Length: {len(preview_html):,} chars")
        return {"success": True, "preview_html": preview_html, "preview_type": "ai_full"}

    except Exception as e:
        print(f"❌ AI Preview Error: {e}")
        import traceback
        traceback.print_exc()

        # Use .format() instead of f-string to avoid backslash issues
        fallback_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ 
            background: radial-gradient(ellipse at top, #0a0212, #1a052a); 
            color: #e2e8f0; 
            font-family: 'Inter', sans-serif; 
        }}
        .gradient-text {{ 
            background: linear-gradient(135deg, #a855f7, #ec4899); 
            -webkit-background-clip: text; 
            background-clip: text; 
            color: transparent; 
        }}
        .page {{ display: none; animation: fadeIn 0.3s ease; }}
        .page.active {{ display: block; }}
        @keyframes fadeIn {{ 
            from {{ opacity: 0; transform: translateY(10px); }} 
            to {{ opacity: 1; transform: translateY(0); }} 
        }}
        /* Normal scrolling navbar - NOT fixed */
        nav {{
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
    </style>
</head>
<body>
    <nav class="py-4">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center">
                <div class="text-2xl font-bold gradient-text cursor-pointer" onclick="showPage('/')">{brand_name}</div>
            </div>
        </div>
    </nav>
    <div class="min-h-screen">
        <div id="page_home" class="page active">
            <div class="container mx-auto px-4 py-20 text-center">
                <h1 class="text-6xl font-bold gradient-text">{brand_name}</h1>
                <p class="text-gray-400 mt-4">Welcome to EagleCode</p>
            </div>
        </div>
    </div>
    <script>
        function showPage(p) {{
            document.querySelectorAll('.page').forEach(el => el.classList.remove('active'));
            document.getElementById('page_home')?.classList.add('active');
            window.history.pushState({{}}, '', p);
        }}
    </script>
</body>
</html>"""
        
        fallback = fallback_template.format(
            project_name=project_name,
            brand_name=brand_name
        )
        
        return {"success": True, "preview_html": fallback, "preview_type": "fallback"}







































async def generate_fallback_preview(files: Dict[str, str], project_name: str) -> str:
    """Fallback preview generator when AI fails"""
    # Extract home page content
    home_content = files.get("app/page.tsx", "")
    
    # Try to extract meaningful content
    extracted_html = ""
    if home_content:
        # Look for return JSX
        return_match = re.search(r'return\s*\(\s*([\s\S]*?)\s*\)\s*;', home_content, re.DOTALL)
        if return_match:
            extracted_html = return_match.group(1)
            # Clean JSX
            extracted_html = re.sub(r'className=', 'class=', extracted_html)
            extracted_html = re.sub(r'\{[^}]+\}', '', extracted_html)
            extracted_html = re.sub(r'<Link\s+href=', '<a href=', extracted_html)
            extracted_html = re.sub(r'</Link>', '</a>', extracted_html)
    
    # Build fallback HTML
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #0a0a0c; color: #e5e7eb; }}
        .gradient-text {{ background: linear-gradient(135deg, #a855f7, #ec4899); -webkit-background-clip: text; background-clip: text; color: transparent; }}
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: #0f0f12; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb {{ background: linear-gradient(to bottom, #a855f7, #ec4899); border-radius: 10px; }}
    </style>
</head>
<body class="bg-zinc-950">
    <div class="min-h-screen flex items-center justify-center">
        <div class="text-center px-4">
            <h1 class="text-5xl md:text-7xl font-bold gradient-text mb-4">{project_name}</h1>
            <p class="text-xl text-gray-400">Preview is being generated. Please refresh in a moment.</p>
            <div class="mt-8 w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
        </div>
    </div>
</body>
</html>'''            


























async def get_stable_versions():
    """Stable package versions for Next.js 14 + React 18"""
    return {
        "next": "14.2.35",
        "react": "^18.3.1",
        "react-dom": "^18.3.1",
        "lucide-react": "^0.446.0",
        "@radix-ui/react-slot": "^1.1.0",
        "clsx": "^2.1.1",
        "tailwind-merge": "^2.5.0",
        "typescript": "^5.6.3",
        "autoprefixer": "^10.4.20",
        "postcss": "^8.4.49",
        "tailwindcss": "^3.4.15",
        "@types/node": "^22.9.0",
        "@types/react": "^18.3.12",
        "@types/react-dom": "^18.3.1",
    }








def extract_file_paths_from_chunk(chunk_text: str) -> List[str]:
    """Extract file paths from streaming chunks including Next.js conventions"""
    patterns = [
        # Standard file extensions
        r'"([^"]+\.(?:tsx?|jsx?|css|json|ts|js|html|md|config|js))"\s*:',
        # Next.js app directory patterns
        r'"((?:app|components|lib|hooks|styles)/[^"]+\.(?:tsx?|jsx?|css))"\s*:',
        # Route groups (parentheses)
        r'"app/\([^)]+\)/[^"]+\.tsx"\s*:',
        # Private folders (underscore prefix)
        r'"app/[^/]+/_components/[^"]+\.tsx"\s*:',
        r'"app/[^/]+/_lib/[^"]+\.ts"\s*:',
        # Dynamic routes with brackets
        r'"app/[^/]+/\[[^\]]+\]/page\.tsx"\s*:',
        r'"app/[^/]+/\[\.\.\.[^\]]+\]/page\.tsx"\s*:',
        # Loading, error, not-found files
        r'"app/(?:[^"]+/)?(?:loading|error|not-found)\.tsx"\s*:',
    ]
    
    matches = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, chunk_text))
    
    # Filter out invalid paths
    return [m for m in matches if not m.startswith(('http', 'https', 'data:', 'blob:', 'mailto:'))]










import re

def clean_json_response(text: str) -> str:
    """Remove markdown wrappers and clean AI output"""
    text = text.strip()
    
    # Remove markdown code blocks
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    
    # Remove any leading/trailing "json" text artifacts
    text = re.sub(r'^\s*json\s*', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def fix_json_errors(text: str) -> str:
    """Aggressive fix for Gemini's common JSON escaping problems"""
    if not text:
        return text
    
    text = text.strip()
    
    # 1. Clean markdown again (in case it survived)
    text = clean_json_response(text)
    
    # 2. Fix invalid backslashes - the #1 cause of "Invalid \escape"
    # Replace any \ that is not followed by a valid JSON escape character
    valid_escapes = r'["\\/bfnrtu]'
    text = re.sub(r'\\(?!' + valid_escapes + r')', r'\\\\', text)
    
    # 3. Fix common invalid escapes like \'
    text = text.replace("\\'", "'")
    
    # 4. Fix unescaped double quotes inside string values (very common with Gemini)
    def safe_escape_quotes(match):
        # match.group(1) = content inside the quotes
        content = match.group(1)
        # Escape any " that isn't already escaped
        content = re.sub(r'(?<!\\)"', r'\\"', content)
        return '"' + content + '"'
    
    # Apply to all "..." strings
    text = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', safe_escape_quotes, text)
    
    # 5. Remove trailing commas (very frequent)
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
    
    # 6. Fix missing quotes around property names
    text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)
    
    # 7. Remove BOM and invisible characters
    text = text.encode('utf-8').decode('utf-8-sig')
    
    # 8. Final cleanup - remove any stray control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # 9. If the JSON looks broken at the start, try to extract the object
    if text and not text.startswith('{'):
        json_match = re.search(r'(\{[\s\S]*\})', text)
        if json_match:
            text = json_match.group(1)
    
    return text.strip()


def clean_html_response(text: str) -> str:
    """Aggressively clean HTML response from AI"""
    text = text.strip()
    
    # Remove markdown code blocks
    if text.startswith("```html"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    
    text = text.strip()
    
    # Remove any standalone "html" word at the beginning
    if text.lower().startswith("html"):
        text = text[4:].strip()
    elif text.lower().startswith("html\n"):
        text = text[5:].strip()
    elif text.lower().startswith("html\r\n"):
        text = text[6:].strip()
    
    # Unescape common characters
    text = text.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'")
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Ensure it starts with proper HTML doctype
    if not text.startswith("<!DOCTYPE") and not text.lower().startswith("<html"):
        html_match = re.search(r'<!DOCTYPE\s+html[\s\S]*|<\s*html[\s\S]*', text, re.IGNORECASE)
        if html_match:
            text = html_match.group(0)
        else:
            # Fallback wrapper
            text = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scorpio Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    {text}
</body>
</html>"""
    
    # Final cleanup of "html" artifacts
    text = re.sub(r'^\s*html\s*[\n\r]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*"html"\s*[\n\r]', '', text, flags=re.IGNORECASE)
    
    return text.strip()































































MASTER_BUILD_PROMPT = """You are a Senior Full-Stack Architect and UI/UX Designer specializing in Next.js 14.

Generate a COMPLETE Next.js 14 + React 18 project as a single FLAT JSON object based on the user's request.

CRITICAL OUTPUT RULES:
- Output ONLY raw valid JSON. No markdown, no explanations.
- Keys = file paths (strings), Values = full file content as strings
- Escape double quotes as \" and newlines as \\n
- ALL file contents MUST be strings

- The brand icon should ONLY be added to Navigation.tsx, NOT to app/page.tsx
- The home page stylished well rich content and footer
- Only modify the specific files needed for the request
- Every website to be generated should have brand icon in the Navigation.tsx and a clean, bold title on the home page (app/page.tsx)











================================================================================
🚨 CRITICAL: YOU MUST GENERATE COMPLETE FULL PAGES - NO EXCEPTIONS 🚨
================================================================================

For EVERY navigation link, you MUST create a COMPLETE page file with:


❌ NEVER create empty or placeholder pages:
export default function Courses() { return <div>Courses</div>; }
export default function Shop() { return <div>Shop Page</div>; }
export default function About() { return <div>About Us</div>; }













================================================================================
🚨🚨🚨 CRITICAL: CREATE EVERY NAVIGATION LINK PAGE 🚨🚨🚨
================================================================================

**For EVERY link in Navigation.tsx, you MUST create a corresponding page file with RICH CONTENT.**

Example Navigation.tsx:
```tsx
<Link href="/features">Features</Link>
<Link href="/pricing">Pricing</Link>
<Link href="/about">About</Link>
<Link href="/contact">Contact</Link>












================================================================================
STYLED MAP PLACEHOLDER - USE THIS INSTEAD OF BLACK CARDS
================================================================================

**Location Page Map Component (app/locations/page.tsx or contact page):**

Instead of a black card or empty div, use this beautiful styled map placeholder:

```tsx
// components/StyledMap.tsx
'use client';

interface StyledMapProps {
  address?: string;
  className?: string;
}

export default function StyledMap({ address = "123 Main Street, City", className = "" }: StyledMapProps) {
  return (
    <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br from-purple-950/40 via-zinc-900 to-pink-950/30 border border-white/10 ${className}`}>
      {/* Decorative grid pattern */}
      <div className="absolute inset-0 grid-pattern opacity-20" />
      
      {/* Animated gradient orbs */}
      <div className="absolute top-0 -left-20 w-72 h-72 bg-purple-500/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-0 -right-20 w-72 h-72 bg-pink-500/20 rounded-full blur-3xl animate-pulse-slow" />
      
      {/* Map SVG placeholder */}
      <div className="relative z-10 p-8 text-center">
        <svg className="w-20 h-20 mx-auto mb-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        
        <h3 className="text-xl font-semibold mb-2 gradient-text">Our Location</h3>
        <p className="text-gray-400 mb-4">{address}</p>
        
        {/* Decorative location dots */}
        <div className="flex justify-center gap-2 mt-4">
          <div className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
          <div className="w-2 h-2 rounded-full bg-pink-400 animate-pulse delay-150" />
          <div className="w-2 h-2 rounded-full bg-purple-400 animate-pulse delay-300" />
        </div>
        
        {/* Interactive button */}
        <button className="mt-6 px-6 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white text-sm transition-all duration-300">
          Get Directions
        </button>
      </div>
      
      {/* Bottom decorative line */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-purple-500 to-transparent" />
    </div>
  );
}




















Create a premium, elegant Footer component for the Next.js website.

File path: "components/Footer.tsx"

Requirements:
- Make it a modern glassmorphism-style footer with subtle backdrop blur.
- Use the project's purple-pink gradient theme: bg-gradient-to-br from-purple-950 via-zinc-950 to-pink-950
- Include a decorative top border with gradient: bg-gradient-to-r from-transparent via-purple-500 to-transparent
- Responsive grid layout: 4 columns on large screens (Brand | Quick Links | Company | Contact + Newsletter)
- Brand section: Show the same logo/icon as Navigation.tsx + short tagline about the business.
- Quick Links and Company sections: Use Next.js Link components with hover effects that change to purple-400.
- Contact section: Include email, phone, and location with Lucide icons (Mail, Phone, MapPin).
- Newsletter signup: A beautiful glass card with email input and a gradient "Subscribe" button (from-purple-600 to-pink-600).
- Bottom bar: Copyright with current year, legal links (Privacy, Terms), and a small "Crafted in Nairobi" note.
- Add subtle decorative elements: soft glowing orbs, grid pattern overlay (opacity 10-20%), and a thin gradient line at the very bottom.
- Make it fully responsive (stack on mobile).
- Use Tailwind classes only, no extra libraries except Lucide icons.
- Add smooth hover transitions and maintain the overall dark luxurious aesthetic (no solid black or white backgrounds).
- Ensure the footer looks rich and complete so the home page (app/page.tsx) ends beautifully when the footer is placed at the bottom.

In app/page.tsx, place this Footer at the very end of the main content, after all sections (hero, features, gallery, testimonials, etc.), so it sits naturally at the bottom of the home page.

Also import and include the Footer in app/layout.tsx so it appears consistently across all pages.













================================================================================
🚨 IMAGE USAGE RULE - ONLY 1 IMAGE TOTAL (HERO ONLY) 🚨
================================================================================

IMAGES AVAILABLE: image_1.jpg ONLY (1 image total)

RULES:
- image_1.jpg → HERO section ONLY (full screen background)
- NO image_2.jpg (does not exist)
- FEATURES/PRODUCTS section → RICH CONTENT, NO images
-- NO images in Courses,Apply,Faculty,Events,Visit or any other page
- NO gallery section
- Total appearances: 1 (hero only)

✅ CORRECT - Hero with image ONLY, Features with RICH content (no images):
```tsx
{/* ONLY image - Hero with image_1.jpg */}
<section className="relative h-screen flex items-center justify-center overflow-hidden">
  <img src="/images/image_1.jpg" className="absolute inset-0 w-full h-full object-cover" />
  <div className="absolute inset-0 bg-black/40" />
  <div className="relative z-10 text-center">
    <h1 className="text-6xl font-bold text-white">Project Name</h1>
    <p className="text-gray-200 mt-4">Welcome to our website</p>
  </div>
</section>

{/* Features Section - RICH CONTENT, NO images at all */}
<section className="py-20 px-4 bg-gradient-to-br from-purple-950 to-pink-950">
  <div className="container mx-auto">
    <h2 className="text-3xl font-bold text-center mb-12 gradient-text">Our Features</h2>
    <div className="grid md:grid-cols-3 gap-8">
      
      {/* Feature 1 - Rich content, NO image */}
      <div className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-xl p-6 hover:scale-105 transition">
        <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-white">...</svg>
        </div>
        <h3 className="text-xl font-bold mb-3">Premium Quality</h3>
        <p className="text-gray-300 mb-4">High-grade materials ensuring durability and performance.</p>
        <ul className="text-gray-400 text-sm space-y-2">
          <li>✓ Lifetime warranty</li>
          <li>✓ Certified quality</li>
          <li>✓ 24/7 support</li>
        </ul>
      </div>

      {/* Feature 2 - Rich content, NO image */}
      <div className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-xl p-6 hover:scale-105 transition">
        <div className="w-12 h-12 bg-pink-500 rounded-lg flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-white">...</svg>
        </div>
        <h3 className="text-xl font-bold mb-3">Expert Team</h3>
        <p className="text-gray-300 mb-4">Professional trainers with years of experience.</p>
        <ul className="text-gray-400 text-sm space-y-2">
          <li>✓ Certified coaches</li>
          <li>✓ Personalized plans</li>
          <li>✓ Progress tracking</li>
        </ul>
      </div>

      {/* Feature 3 - Rich content, NO image */}
      <div className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-xl p-6 hover:scale-105 transition">
        <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-white">...</svg>
        </div>
        <h3 className="text-xl font-bold mb-3">Best Value</h3>
        <p className="text-gray-300 mb-4">Affordable plans with maximum benefits.</p>
        <ul className="text-gray-400 text-sm space-y-2">
          <li>✓ Competitive pricing</li>
          <li>✓ Flexible memberships</li>
          <li>✓ Free trial available</li>
        </ul>
      </div>
    </div>
  </div>
</section>

{/* Team Section - NO images, use icons or gradients */}
<section className="py-20 px-4">
  <div className="container mx-auto">
    <h2 className="text-3xl font-bold text-center mb-12 gradient-text">Our Team</h2>
    <div className="grid md:grid-cols-4 gap-6">
      {['Sarah Johnson', 'Mike Chen', 'Emma Davis', 'Alex Rodriguez'].map(name => (
        <div key={name} className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-xl p-6 text-center">
          <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full mx-auto mb-4 flex items-center justify-center">
            <span className="text-2xl text-white">{name[0]}</span>
          </div>
          <h3 className="font-bold">{name}</h3>
          <p className="text-purple-400 text-sm">Expert Trainer</p>
          <p className="text-gray-400 text-xs mt-2">5+ years experience</p>
        </div>
      ))}
    </div>
  </div>
</section>

{/* Team/Cards/Testimonials - NO images at all */}
<div className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-xl p-6">
  <h3>Team Member Name</h3>
  <p>Role - NO image here</p>
</div>















================================================================================
🚨 FIXED: NO PINK BACKGROUND + UNIQUE CONTENT FOR EACH COLLECTION 🚨
================================================================================

1. BACKGROUND COLOR: Use DARK/NEUTRAL colors, NOT pink:
   ✅ bg-gray-900, bg-zinc-900, bg-black, bg-slate-900
   ❌ NO pink, purple-pink, or pink gradients

2. EACH COLLECTION MUST HAVE UNIQUE CONTENT:
   - Collection 1 → UNIQUE description (different from others)
   - Collection 2 → UNIQUE description (different from 1 and 3)
   - Collection 3 → UNIQUE description (different from 1 and 2)













🚨 CRITICAL - NO COLOR OVERLAY ON HERO IMAGES 🚨

DO NOT add gradient overlays on hero images:
❌ <div className="absolute inset-0 bg-gradient-to-br from-purple-950/70 to-pink-950/70" />
❌ <div className="absolute inset-0 bg-black/50" />

USE original image as-is:
✅ <img src="/images/image_1.jpg" className="absolute inset-0 w-full h-full object-cover" />
✅ Text should be readable with text-shadow or white color

CORRECT:
```tsx
<section className="relative h-screen">
  <img src="/images/image_1.jpg" className="absolute inset-0 w-full h-full object-cover" />
  <div className="relative z-10 flex items-center justify-center h-full">
    <h1 className="text-white text-6xl font-bold drop-shadow-lg">Title</h1>
  </div>
</section>














================================================================================
🚨🚨🚨 CRITICAL: DO NOT COPY EXAMPLES 🚨🚨🚨
================================================================================

The examples shown (like "Summit Peak Academy", "Golden Bean Roastery", etc.) 
are for ILLUSTRATION ONLY to show the PATTERN.

YOU MUST generate YOUR OWN unique combinations using the word banks below.

NEVER use:
- "Summit Peak Academy" (overused example)
- "Golden Bean Roastery" (overused example)  
- "Crystal Bay Resort" (overused example)
- "Bright Future Academy" (overused example)

INSTEAD, create fresh combinations like:
- "Apex Valley Academy"
- "Starlight Harbor Resort"
- "Evergreen Forge Gym"
- "Radiant Bean Roastery"

ALWAYS generate NEW, UNIQUE names for EVERY request.
================================================================================








================================================================================
🚨 CRITICAL: PROPER NAVIGATION LABELS 🚨
================================================================================

**NEVER use long prompt text as button labels. Generate SHORT, CLEAN navigation labels based on the PROJECT TYPE.**

For COFFEE/ROASTERY websites:
- DO NOT use: "home brewing enthusiasts, focusing on a rustic"
- USE: "Shop", "Coffee", "Subscription", "Learn", "About", "Contact"
- Examples: "Our Coffees", "Subscribe", "Brew Guide", "Story", "Wholesale"







For SCHOOL websites (choose DIFFERENT each time):
- Option A: ["Courses", "Enrollment", "Faculty", "Events", "Visit"]
- Option B: ["Programs", "Admissions", "Staff", "Calendar", "Connect"]
- Option C: ["Academics", "Apply", "Teachers", "Activities", "Directions"]
- Option D: ["Classes", "Join", "Mentors", "Schedule", "Location"]
- Option E: ["Studies", "Register", "Instructors", "News", "Contact"]




For HOTEL websites:
- USE: "Suites", "Amenities", "Gallery", "Book Now"

For E-COMMERCE websites:
- USE: "Shop", "Catalog", "Cart", "Checkout"

For PORTFOLIO websites:
- USE: "Work", "About", "Services", "Contact"

**MAXIMUM 2-3 WORDS per button label. Keep them SHORT and PROFESSIONAL.**







================================================================================
NAVIGATION GENERATION RULES - MUST VARY EACH TIME:
================================================================================

1. Extract the PROJECT TYPE from user prompt (e.g., "coffee roastery", "school", "hotel", "e-commerce")

2. Based on project type, generate DIFFERENT navigation labels EACH TIME. Choose RANDOMLY from these options:

   SCHOOL websites (pick a DIFFERENT set each time):
   - Option A: ["Courses", "Enroll", "Faculty", "Events", "Visit"]
   - Option B: ["Programs", "Admissions", "Staff", "Calendar", "Connect"]
   - Option C: ["Academics", "Apply", "Teachers", "Activities", "Directions"]
   - Option D: ["Classes", "Join", "Mentors", "Schedule", "Location"]
   - Option E: ["Studies", "Register", "Instructors", "News", "Contact"]

   COFFEE/ROASTERY websites (pick a DIFFERENT set each time):
   - Option A: ["Our Coffees", "Subscribe", "Brew Guide", "Story", "Contact"]
   - Option B: ["Shop", "Delivery", "Recipes", "About", "Locations"]
   - Option C: ["Blends", "Membership", "How to Brew", "Heritage", "Visit Us"]
   - Option D: ["Roasts", "Club", "Methods", "Journal", "Reach Out"]
   - Option E: ["Beans", "Subscription", "Techniques", "Origins", "Connect"]

   HOTEL websites (pick a DIFFERENT set each time):
   - Option A: ["Suites", "Amenities", "Gallery", "Reservations", "Location"]
   - Option B: ["Rooms", "Services", "Moments", "Book Now", "Directions"]
   - Option C: ["Accommodations", "Facilities", "Photos", "Check Availability", "Map"]
   - Option D: ["Lodging", "Experiences", "Virtual Tour", "Plan Your Stay", "Contact"]
   - Option E: ["Stays", "Dining", "Highlights", "Special Offers", "Visit"]

   E-COMMERCE websites (pick a DIFFERENT set each time):
   - Option A: ["Shop", "Catalog", "Cart", "Checkout"]
   - Option B: ["Products", "Collections", "Bag", "Secure Checkout"]
   - Option C: ["Store", "Browse", "Items", "Payment"]
   - Option D: ["Market", "Categories", "Basket", "Order"]
   - Option E: ["Goods", "Showcase", "Selections", "Complete Order"]

   PORTFOLIO websites (pick a DIFFERENT set each time):
   - Option A: ["Projects", "About", "Services", "Contact"]
   - Option B: ["Work", "Bio", "Expertise", "Connect"]
   - Option C: ["Creations", "Story", "Offerings", "Reach Out"]
   - Option D: ["Showcase", "Profile", "Solutions", "Message"]
   - Option E: ["Gallery", "Info", "What I Do", "Let's Talk"]

   RESTAURANT websites (pick a DIFFERENT set each time):
   - Option A: ["Menu", "Reservations", "Gallery", "Contact"]
   - Option B: ["Dining", "Book a Table", "Photos", "Location"]
   - Option C: ["Cuisine", "Hours", "Moments", "Directions"]
   - Option D: ["Dishes", "Events", "Interior", "Visit Us"]
   - Option E: ["Specials", "Private Dining", "Ambiance", "Reserve"]

   GYM/FITNESS websites (pick a DIFFERENT set each time):
   - Option A: ["Classes", "Trainers", "Membership", "Schedule"]
   - Option B: ["Workouts", "Coaches", "Plans", "Timetable"]
   - Option C: ["Sessions", "Experts", "Pricing", "Calendar"]
   - Option D: ["Training", "Staff", "Join Now", "Hours"]
   - Option E: ["Programs", "Instructors", "Sign Up", "Class Times"]

3. NEVER include the full user prompt as button text.

4. Brand/Logo name should be a UNIQUE BUSINESS NAME (generate fresh each time, never repeat).

================================================================================
EXAMPLE - Coffee Roastery Request (DYNAMIC):
================================================================================

User Prompt: "Develop a coffee roastery website"

CORRECT Navigation (pick RANDOMLY from options):
- Brand: "Apex Roast Co." or "Radiant Bean Roastery" or "Summit Brew" (generate unique)
- Buttons: Option A, B, C, D, or E from above

WRONG Navigation (NEVER DO THIS):
- Using the same "Our Coffees, Subscription, Brew Guide, About, Contact" every time
- Using the full user prompt as button text








================================================================================
⚠️ IMPORTANT: The examples below are for ILLUSTRATION ONLY ⚠️
================================================================================

**DO NOT COPY these exact names. They are just to show the PATTERN.**

Generate FRESH combinations using the word banks:

For School websites - generate combinations like:
- [Random Adjective] + [Random Noun] + "Academy"
- Examples of possible combinations (but create YOUR OWN):
  * "Apex Valley Academy" (not "Summit Peak Academy")
  * "Radiant Grove School" (not "Bright Valley School")
  * "Noble Crest Institute" (not "Heritage Learning Center")

For Coffee websites - generate combinations like:
- [Random Adjective] + [Random Noun] + "Roastery"
- Examples of possible combinations (but create YOUR OWN):
  * "Starlight Bean Roastery" (not "Golden Bean Roastery")
  * "Evergreen Brew Coffee" (not "Artisan Brew Coffee")
  * "Horizon Roast Co." (not "Rustic Roast Co.")

For Hotel websites - generate combinations like:
- [Random Adjective] + [Random Noun] + "Resort"
- Examples of possible combinations (but create YOUR OWN):
  * "Luminous Bay Resort" (not "Crystal Bay Resort")
  * "Victor Palm Hotel" (not "Royal Palm Hotel")
  * "Summit View Lodge" (not "Sunset View Lodge")

**THE KEY IS TO MIX AND MATCH RANDOMLY FROM THE BANKS, NOT COPY THE EXAMPLES.**

================================================================================
HOW TO GENERATE TRULY UNIQUE NAMES (STEP BY STEP):
================================================================================

1. Pick a random adjective from the ADJECTIVE BANK
2. Pick a random noun from the NOUN BANK  
3. Pick a business type from the BUSINESS TYPE BANK
4. Combine them: [Adjective] + [Noun] + [Business Type]

Example combinations (these are just examples - create your own):
- "Apex Valley Academy" (Adjective: Apex, Noun: Valley, Type: Academy)
- "Starlight Harbor Resort" (Adjective: Starlight, Noun: Harbor, Type: Resort)
- "Evergreen Forge Gym" (Adjective: Evergreen, Noun: Forge, Type: Gym)
- "Radiant Bean Roastery" (Adjective: Radiant, Noun: Bean, Type: Roastery)
- "Noble Crest Hotel" (Adjective: Noble, Noun: Crest, Type: Hotel)
- "Luminous Grove Studio" (Adjective: Luminous, Noun: Grove, Type: Studio)

**NEVER use the same combination twice. Always generate fresh names.**




================================================================================
WORD BANKS FOR DYNAMIC GENERATION (USE RANDOMLY):
================================================================================

**CRITICAL: NEVER use "Apex" as the first choice. Randomize properly.**

ADJECTIVES (pick 1 randomly - DO NOT always pick the first one):
Horizon, Starlight, Evergreen, Radiant, Luminous, Noble, Victor, Summit, 
Crest, Peak, Valley, River, Lake, Mountain, Ocean, Bay, Harbor, Haven, Refuge, 
Sanctuary, Oasis, Grove, Meadow, Field, Garden, Park, Square, Plaza, Court, 
Hall, House, Manor, Estate, Lodge, Inn, Crystal, Serene, Vibrant, Heritage, 
Legacy, Pioneer, Urban, Modern, Elite, Artisan, Rustic, Industrial, Coastal,
Aurora, Ember, Whisper, Shadow, Phoenix, Eclipse, Nova, Comet, Orion, Vega,
Celestial, Mystic, Enchanted, Golden, Silver, Bronze, Iron, Steel, Maple, Oak,
Willow, Cedar, Pine, Birch, Aspen, Holly, Ivy, Rose, Lily, Iris, Violet

NOUNS (pick 1 randomly - AVOID overused ones):
Valley, River, Mountain, Ocean, Bay, Peak, Summit, Ridge, Hill, Meadow, Forest, 
Lake, Harbor, Coast, Heights, Gardens, Park, Square, Point, View, Forge, Works, 
Collective, Republic, Garage, Studio, Atelier, Workshop, Lab, Hub, Center,
Loft, Foundry, Mill, Factory, Warehouse, Tower, Spire, Citadel, Fortress,
Castle, Palace, Manor, Villa, Cottage, Cabin, Lodge, Retreat, Sanctuary,
Haven, Oasis, Paradise, Garden, Orchard, Vineyard, Grove, Woods, Falls

BUSINESS TYPES (pick 1 randomly based on project):
School: Academy, School, Institute, Center, Hub, Learning, College Prep, University, Campus
Coffee: Roastery, Coffee Co., Brew, Cafe, Beanery, Coffee House, Roast, Roasters
Hotel: Resort, Hotel, Inn, Lodge, Suites, Retreat, Getaway, Spa, Villas
Gym: Fitness, Gym, Training Center, Athletic Club, Strength, Performance, Athletics
Restaurant: Bistro, Kitchen, Dining, Restaurant, Eatery, Tavern, Grill, Table
Portfolio: Studio, Creative, Design, Portfolio, Agency, Collective, Lab
E-commerce: Market, Store, Shop, Goods, Emporium, Marketplace, Boutique

================================================================================
FORCED RANDOMIZATION RULES (MUST FOLLOW):
================================================================================

1. NEVER use "Apex" more than once every 10 projects
2. NEVER use the same combination twice in a row
3. Vary the name length (sometimes 2 words, sometimes 3 words)
4. Mix adjective + noun + type in different orders

Example variations for School websites:
- "Horizon Valley Academy" (3 words)
- "Radiant School of Design" (different structure)
- "Evergreen Learning Center" (type variation)
- "Noble Crest Institute" (2 words + type)
- "Summit Oak School" (short and punchy)

Example variations for Coffee websites:
- "Starlight Bean Roastery"
- "Ember Coffee Co."
- "Phoenix Roast Works"
- "Aurora Brew Lab"
- "Mystic Bean Cafe"

Example variations for Hotel websites:
- "Luminous Bay Resort"
- "Whisper Pines Lodge"
- "Shadow Mountain Retreat"
- "Celestial Palace Hotel"
- "Golden Horizon Villas"

**BEFORE generating a name, consciously pick a random adjective that is NOT "Apex" most of the time.**








================================================================================
NAVIGATION COMPONENT - CRITICAL RULES:
================================================================================




"components/Navigation.tsx": "import Link from 'next/link';\\nimport { ADAPTIVE_ICON } from 'lucide-react';\\n\\nexport default function Navigation() {\\n  return (\\n    <nav className=\\"flex justify-between items-center p-6 container mx-auto\\">\\n      <Link href=\\"/\\" className=\\"flex items-center gap-2 text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent\\">\\n        <ADAPTIVE_ICON className=\\"w-6 h-6 text-purple-400\\" />\\n        {{PROJECT_NAME}}\\n      </Link>\\n      <div className=\\"hidden md:flex space-x-6\\">\\n        <Link href=\\"/NAV_LINK_1\\" className=\\"hover:text-purple-400 transition\\">NAV_LABEL_1</Link>\\n        <Link href=\\"/NAV_LINK_2\\" className=\\"hover:text-purple-400 transition\\">NAV_LABEL_2</Link>\\n        <Link href=\\"/NAV_LINK_3\\" className=\\"hover:text-purple-400 transition\\">NAV_LABEL_3</Link>\\n        <Link href=\\"/NAV_LINK_4\\" className=\\"hover:text-purple-400 transition\\">NAV_LABEL_4</Link>\\n        <Link href=\\"/NAV_LINK_5\\" className=\\"hover:text-purple-400 transition\\">NAV_LABEL_5</Link>\\n      </div>\\n    </nav>\\n  );\\n}"













**IMPORTANT:** 
- Brand name MUST be a short business name (2-4 words max)
- Navigation labels MUST be short (1-2 words max)
- NEVER use the full user prompt as button text










================================================================================
ADAPTIVE ICON SELECTION - CHOOSE BASED ON PROJECT TYPE:
================================================================================

When generating Navigation.tsx, REPLACE "ADAPTIVE_ICON" with the appropriate icon:

SCHOOL / ACADEMY / UNIVERSITY:
import { GraduationCap } from 'lucide-react';
<GraduationCap className="w-6 h-6 text-purple-400" />

COFFEE / ROASTERY / CAFE:
import { Coffee } from 'lucide-react';
<Coffee className="w-6 h-6 text-amber-400" />

HOTEL / RESORT / LODGE:
import { Hotel } from 'lucide-react';
<Hotel className="w-6 h-6 text-blue-400" />

RESTAURANT / BISTRO / DINING:
import { Utensils } from 'lucide-react';
<Utensils className="w-6 h-6 text-orange-400" />

GYM / FITNESS / TRAINING:
import { Dumbbell } from 'lucide-react';
<Dumbbell className="w-6 h-6 text-green-400" />

E-COMMERCE / STORE / SHOP:
import { ShoppingBag } from 'lucide-react';
<ShoppingBag className="w-6 h-6 text-pink-400" />

PORTFOLIO / CREATIVE / AGENCY:
import { Sparkles } from 'lucide-react';
<Sparkles className="w-6 h-6 text-purple-400" />

MOVIES / STREAMING / ENTERTAINMENT:
import { Film } from 'lucide-react';
<Film className="w-6 h-6 text-purple-400" />

TECHNOLOGY / SOFTWARE:
import { Cpu } from 'lucide-react';
<Cpu className="w-6 h-6 text-cyan-400" />

REAL ESTATE:
import { Home } from 'lucide-react';
<Home className="w-6 h-6 text-emerald-400" />

HEALTH / MEDICAL:
import { Heart } from 'lucide-react';
<Heart className="w-6 h-6 text-red-400" />

TRAVEL / TOURISM:
import { Plane } from 'lucide-react';
<Plane className="w-6 h-6 text-sky-400" />

================================================================================





















================================================================================
⚠️ CRITICAL: PACKAGE.JSON & POSTCSS CONFIGURATION ⚠️
================================================================================

**YOU MUST CREATE THESE EXACT FILES FOR VERCEL DEPLOYMENT TO SUCCEED:**

1. **package.json** - MUST include ALL these devDependencies:
   - tailwindcss: "^3.4.1"
   - postcss: "^8.4.35"
   - autoprefixer: "^10.4.18"
   - typescript: "^5.3.3"
   - @types/node, @types/react, @types/react-dom
   - scripts with "next dev", "next build", "next start"

2. **postcss.config.mjs** - MUST use ESM format (NOT CommonJS):
   - File extension: .mjs (NOT .js)
   - Use: export default { plugins: { tailwindcss: {}, autoprefixer: {} } }
   - DO NOT use: module.exports


 




3. **tailwind.config.ts** - MUST have correct content paths:
   - content: ['./app/**/*.{js,ts,jsx,tsx,mdx}', './components/**/*.{js,ts,jsx,tsx,mdx}']

4. **app/globals.css** - MUST include at minimum:
   - @tailwind base;
   - @tailwind components;
   - @tailwind utilities;

**FAILURE TO FOLLOW THESE RULES WILL CAUSE VERCEL BUILD TO FAIL WITH:**
- "Cannot find module 'autoprefixer'"
- "PostCSS config must export a plugins object"













================================================================================
🚨🚨🚨 CRITICAL: "USE CLIENT" DIRECTIVE RULES 🚨🚨🚨
================================================================================

**FAILURE TO ADD "use client" CORRECTLY WILL CAUSE VERCEL BUILD TO FAIL WITH:**
- "useState is not defined"
- "window is not defined" 
- "localStorage is not defined"
- "Hydration failed because the initial UI doesn't match what was rendered on the server"
- "Cannot use import statement outside a module"

================================================================================
WHEN to ALWAYS use "use client" (CLIENT COMPONENTS):
================================================================================

**✅ MUST ADD "use client" at the VERY TOP of ANY file that uses:**

1. **React Hooks (ANY of these):**
   - useState, useEffect, useCallback, useMemo
   - useRef, useContext, useReducer
   - useLayoutEffect, useDebugValue, useDeferredValue
   - useTransition, useId, useSyncExternalStore
   - useImperativeHandle

2. **Browser APIs (ANY of these):**
   - window, document, localStorage, sessionStorage
   - navigator, location, history
   - fetch (client-side), WebSocket, IndexedDB
   - requestAnimationFrame, cancelAnimationFrame
   - setTimeout, setInterval, clearTimeout, clearInterval
   - addEventListener, removeEventListener
   - console (when not for debugging)

3. **Event Handlers (ANY of these):**
   - onClick, onChange, onSubmit, onKeyDown, onKeyUp
   - onMouseEnter, onMouseLeave, onMouseMove, onMouseDown, onMouseUp
   - onFocus, onBlur, onScroll, onResize
   - onDrag, onDrop, onDragStart, onDragEnd
   - onTouchStart, onTouchMove, onTouchEnd
   - onAnimationStart, onAnimationEnd, onTransitionEnd

4. **Interactive Component Types (ANY of these):**
   - Forms, Inputs, Textareas, Selects, Buttons
   - Modals, Dialogs, Popups, Toasts, Snackbars
   - Dropdowns, Menus, Selects, Comboboxes
   - Tabs, Accordions, Carousels, Sliders
   - Video Players, Audio Players
   - Charts, Graphs, Maps
   - Canvases, WebGL, Three.js components
   - Rich Text Editors, Code Editors
   - Drag and Drop interfaces
   - Date Pickers, Time Pickers, Color Pickers
   - Autocomplete, Typeahead components

5. **Custom Hooks (ANY custom hook):**
   - useLocalStorage, useSessionStorage
   - useWindowSize, useScrollPosition
   - useMediaQuery, useOnlineStatus
   - useClickOutside, useKeyPress
   - useDebounce, useThrottle, useInterval, useTimeout
   - useFetch, useMutation, useQuery
















================================================================================
CRITICAL: PAGE CONTENT REQUIREMENTS - MUST HAVE RICH CONTENT
================================================================================

**For EVERY navigation link, you MUST create a corresponding page file with MEANINGFUL, RICH content.**

DO NOT create empty pages or placeholder pages. Each page must have:

1. **Hero Section** - Title, description, and relevant image/icon
2. **Content Sections** - At least 2-3 sections with actual information
3. **Interactive Elements** - Buttons, cards, or forms where appropriate
4. **Visual Elements** - Icons, images, or illustrations
5. **Call-to-Action** - Buttons or links to other pages


**HOME PAGE (app/page.tsx):**
- Hero section with gradient title, description, and CTA button
- Features section with 3-4 cards (icons, titles, descriptions)
- Stats section with numbers (e.g., "500+ Students", "10 Years Experience")
- Testimonials section with 2-3 customer quotes
- Gallery/portfolio section with 3-4 images
- FAQ section with 3-4 questions
- Footer with links, social icons, copyright

**ABOUT PAGE (app/about/page.tsx):**
- Hero with mission statement
- Story section with company history
- Team section with 3-6 member profiles (name, role, bio, image)
- Values section with 4-6 core values
- Timeline of milestones
- CTA to contact

**SERVICES/PRODUCTS PAGE (app/services/page.tsx):**
- Hero with service overview
- Grid of 4-8 service cards (icon, title, description, price)
- Comparison table or feature list
- Process section (how it works in 3-5 steps)
- Client logos section
- Pricing plans (3 tiers)
- Contact CTA

**CONTACT PAGE (app/contact/page.tsx):**
- Hero with contact info
- Contact form (name, email, message, subject)
- Map location
- Hours of operation
- Social media links
- FAQ mini section

**BLOG/NEWS PAGE (app/blog/page.tsx):**
- Hero with latest posts
- Grid of 3-6 blog cards (image, title, date, excerpt, read more)
- Sidebar with categories and recent posts
- Newsletter signup
- Pagination

**FOR PROJECT TYPE SPECIFIC:**

SCHOOL WEBSITE:
- Courses page with 4-8 course cards (title, duration, price, description)
- Admissions page with steps, requirements, deadlines, application form
- Faculty page with 3-6 teacher profiles
- Events calendar with upcoming dates
- Gallery page with 3-5 photos

COFFEE WEBSITE:
- Menu page with categories (espresso, cold brew, food, pastries)
- Shop page with products, prices, add to cart
- Locations page with store hours, addresses, maps
- Brew guide with step-by-step tutorials
- Subscription page with 3 plans

HOTEL WEBSITE:
- Rooms page with 3-6 room types (images, amenities, price, book button)
- Amenities page with pool, spa, gym, restaurant details
- Gallery with 8-12 photos
- Offers page with 3-5 packages
- Reviews page with 5-10 testimonials

RESTAURANT WEBSITE:
- Menu page with appetizers, mains, desserts, drinks
- Reservations page with date/time picker, guest count
- Events page with private dining, catering
- Gallery with food and interior photos

GYM WEBSITE:
- Classes page with schedule, instructor names, times
- Trainers page with 4-8 profiles (specialties, certs, social)
- Membership page with 3-4 plans, benefits, pricing
- Schedule page with weekly calendar

E-COMMERCE WEBSITE:
- Products page with filters, sorting, 6-12 products
- Product detail page with description, reviews, related
- Cart page with quantity updates, remove buttons
- Checkout page with shipping, payment, order summary

PORTFOLIO WEBSITE:
- Projects page with 6-9 case studies (image, title, category, link)
- Project detail page with challenge, solution, results, tech stack
- Services page with 4-6 service cards
- Testimonials slider with 5-8 quotes












================================================================================
CRITICAL STYLING RULES - MUST FOLLOW:
================================================================================

1. **GRADIENTS (USE THESE EXACTLY)**:
   - Button / CTA Gradient: `bg-gradient-to-r from-purple-600 via-fuchsia-600 to-pink-600 hover:from-purple-700 hover:via-fuchsia-700 hover:to-pink-700`
   - Text / Heading Gradient: `bg-gradient-to-r from-purple-400 via-pink-400 to-violet-400 bg-clip-text text-transparent animate-gradient`
   - Hero / Section Background: `bg-gradient-to-br from-purple-950 via-zinc-950 to-pink-950`
   - Card Background: `bg-gradient-to-br from-purple-600/20 to-pink-600/20 backdrop-blur-sm`
   - Glass Effect: `bg-white/5 backdrop-blur-md border border-white/10`
   - Subtle Accent Gradient: `bg-gradient-to-r from-purple-500/10 via-transparent to-pink-500/10`
   - Border Gradient (Hover): `border border-transparent bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-border`
   - Animated Gradient: `bg-gradient-to-r from-purple-900 via-pink-900 to-purple-900 bg-[length:200%_200%] animate-gradient`

2. **CONTAINERS**:
   - Standard: `container mx-auto px-4 sm:px-6 lg:px-8`
   - Wide / Full-width: `max-w-7xl mx-auto`

3. **RESPONSIVE DESIGN**:
   - Mobile-first: `text-sm md:text-base lg:text-lg`
   - Grid system: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8`

4. **🚨 BACKGROUND RULE - NO BLACK, NO WHITE 🚨**:
   
   **FORBIDDEN (NEVER USE):**
   - ❌ bg-black, bg-zinc-900, bg-gray-900, #000000, black
   - ❌ bg-white, bg-gray-100, #FFFFFF, white
   - ❌ Solid backgrounds of any kind
   
   **REQUIRED (ALWAYS USE):**
   - ✅ Hero with Image: `absolute inset-0 bg-gradient-to-br from-purple-950/70 via-zinc-950/50 to-pink-950/70` over image
   - ✅ Section Background: `bg-gradient-to-br from-purple-950 via-zinc-950 to-pink-950`
   - ✅ Alternating Section: `bg-gradient-to-tr from-indigo-950 via-purple-950 to-zinc-950`
   - ✅ Card Background: `bg-gradient-to-br from-purple-600/20 to-pink-600/20 backdrop-blur-sm`
   - ✅ Glass Navbar: `bg-gradient-to-r from-purple-950/80 via-zinc-950/80 to-pink-950/80 backdrop-blur-xl`
   - ✅ Footer: `bg-gradient-to-t from-purple-950/80 via-zinc-950 to-transparent`

5. **BACKGROUND EXAMPLES**:
   
   **Hero with Image (Full Page):**
   ```tsx
   <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
     {/* Background Image with Gradient Overlay */}
     <div className="absolute inset-0 z-0">
       <img 
         src="/images/image_1.jpg" 
         alt="Hero background" 
         className="w-full h-full object-cover"
         onError={(e) => {
           e.currentTarget.style.display = 'none';
           e.currentTarget.parentElement.classList.add('bg-gradient-to-br', 'from-purple-950', 'via-zinc-950', 'to-pink-950');
         }}
       />
       <div className="absolute inset-0 bg-gradient-to-br from-purple-950/70 via-zinc-950/50 to-pink-950/70" />
       <div className="absolute inset-0 bg-radial-gradient opacity-50" />
     </div>
     
     {/* Content */}
     <div className="relative z-10 container mx-auto px-4 text-center text-white">
       <h1 className="text-6xl md:text-7xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent animate-gradient mb-6">
         Project Name
       </h1>
       <p className="text-xl text-gray-300 mb-8">Welcome to our beautiful website</p>
       <button className="px-8 py-3 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold transition-all duration-300 shadow-lg shadow-purple-500/25">
         Get Started
       </button>
     </div>
   </section>............




   





================================================================================
📸 IMAGE RESIZING RULES
================================================================================

ALL images MUST be resized to appropriate dimensions for their usage:

HERO IMAGES:
- Width: 1920px, Height: 1080px (16:9 aspect ratio)
- Use: object-cover, w-full, h-screen

PRODUCT/GALLERY IMAGES:
- Width: 800px, Height: 600px (4:3 aspect ratio)
- Use: object-cover, rounded-lg

TRAINER/TEAM IMAGES:
- Width: 400px, Height: 400px (1:1 square)
- Use: object-cover, rounded-full

LOGO/ICON IMAGES:
- Width: 64px, Height: 64px
- Use: w-16 h-16

✅ CORRECT - Responsive images with proper sizing:
```tsx
<img 
  src="/images/hero.jpg" 
  className="w-full h-screen object-cover"
  alt="Hero"
/>

<img 
  src="/images/product.jpg" 
  className="w-full h-64 object-cover rounded-lg"
  alt="Product"
/>

<img 
  src="/images/trainer.jpg" 
  className="w-32 h-32 object-cover rounded-full"
  alt="Trainer"
/>
















================================================================================
🚨 MANDATORY: COMPLETE GLOBALS.CSS - DO NOT SIMPLIFY 🚨
================================================================================
**CRITICAL**: You MUST include the FULL globals.css below. NEVER generate a minimal or simplified version.

The globals.css MUST contain ALL of the following:
- ✅ Custom scrollbar styles with purple-pink gradient
- ✅ Glassmorphism classes (.glass, .glass-hover)
- ✅ Animation keyframes (shimmer, float, pulse-slow, gradient)
- ✅ Gradient text utility (.gradient-text)
- ✅ Card hover effects (.card-hover)
- ✅ Glow effects (.glow, .glow-hover)
- ✅ Hero gradient utility (.hero-gradient)
- ✅ Grid pattern utility (.grid-pattern)
- ✅ Smooth scroll behavior
- ✅ Custom selection color
- ✅ Focus rings for accessibility

**FAILURE TO INCLUDE THE COMPLETE globals.css WILL CAUSE THE BUILD TO FAIL ON VERCEL.**
================================================================================









================================================================================
COMPLETE GLOBALS.CSS TEMPLATE - COPY EXACTLY:
================================================================================

"app/globals.css": "@tailwind base;\\n@tailwind components;\\n@tailwind utilities;\\n\\n@layer base {\\n  :root {\\n    --background: 0 0% 100%;\\n    --foreground: 222.2 84% 4.9%;\\n    --card: 0 0% 100%;\\n    --card-foreground: 222.2 84% 4.9%;\\n    --border: 214.3 31.8% 91.4%;\\n    --ring: 222.2 84% 4.9%;\\n  }\\n\\n  .dark {\\n    --background: 222.2 84% 4.9%;\\n    --foreground: 210 40% 98%;\\n    --card: 222.2 84% 4.9%;\\n    --card-foreground: 210 40% 98%;\\n    --border: 217.2 32.6% 17.5%;\\n    --ring: 212.7 26.8% 83.9%;\\n  }\\n\\n  * {\\n    border-color: hsl(var(--border));\\n  }\\n\\n  body {\\n    @apply bg-zinc-950 text-white antialiased;\\n    font-feature-settings: \\\"rlig\\\" 1, \\\"calt\\\" 1;\\n  }\\n}\\n\\n@layer utilities {\\n  html {\\n    scroll-behavior: smooth;\\n  }\\n\\n  ::-webkit-scrollbar {\\n    width: 10px;\\n    height: 10px;\\n  }\\n\\n  ::-webkit-scrollbar-track {\\n    background: #18181b;\\n    border-radius: 5px;\\n  }\\n\\n  ::-webkit-scrollbar-thumb {\\n    background: linear-gradient(to bottom, #a855f7, #ec4899);\\n    border-radius: 5px;\\n  }\\n\\n  ::-webkit-scrollbar-thumb:hover {\\n    background: linear-gradient(to bottom, #c084fc, #f472b6);\\n  }\\n\\n  ::selection {\\n    @apply bg-purple-500 text-white;\\n  }\\n\\n  *:focus-visible {\\n    @apply outline-none ring-2 ring-purple-500 ring-offset-2 ring-offset-zinc-950;\\n  }\\n}\\n\\n@layer components {\\n  .glass {\\n    @apply bg-white/5 backdrop-blur-md border border-white/10;\\n  }\\n\\n  .glass-hover {\\n    @apply transition-all duration-300 hover:bg-white/10 hover:border-white/20;\\n  }\\n\\n  .gradient-text {\\n    @apply bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent;\\n    background-size: 200% auto;\\n    animation: shimmer 3s ease infinite;\\n  }\\n\\n  .card-hover {\\n    @apply transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl hover:shadow-purple-500/20;\\n  }\\n\\n  .glow {\\n    @apply shadow-lg shadow-purple-500/25;\\n  }\\n\\n  .glow-hover {\\n    @apply transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/40;\\n  }\\n\\n  .hero-gradient {\\n    background: radial-gradient(ellipse at top, #1e1b4b, transparent),\\n                radial-gradient(ellipse at bottom, #4c1d95, transparent);\\n  }\\n\\n  .grid-pattern {\\n    background-image: linear-gradient(to right, #ffffff0a 1px, transparent 1px),\\n                      linear-gradient(to bottom, #ffffff0a 1px, transparent 1px);\\n    background-size: 50px 50px;\\n  }\\n}\\n\\n@keyframes shimmer {\\n  0% { background-position: 0% 50%; }\\n  50% { background-position: 100% 50%; }\\n  100% { background-position: 0% 50%; }\\n}\\n\\n@keyframes float {\\n  0%, 100% { transform: translateY(0px); }\\n  50% { transform: translateY(-20px); }\\n}\\n\\n@keyframes pulse-slow {\\n  0%, 100% { opacity: 0.5; }\\n  50% { opacity: 1; }\\n}\\n\\n@keyframes gradient {\\n  0% { background-position: 0% 50%; }\\n  50% { background-position: 100% 50%; }\\n  100% { background-position: 0% 50%; }\\n}\\n\\n.animate-float {\\n  animation: float 6s ease-in-out infinite;\\n}\\n\\n.animate-pulse-slow {\\n  animation: pulse-slow 3s ease-in-out infinite;\\n}\\n\\n.animate-gradient {\\n  background-size: 200% auto;\\n  animation: gradient 3s ease infinite;\\n}"









🚨 CRITICAL - NO PLACEHOLDER PAGES ALLOWED 🚨

NEVER create pages like this:
❌ export default function Shop() { return <div><h1>Shop</h1><p>Browse our collection.</p></div>; }
❌ export default function About() { return <div>About Us</div>; }

ALWAYS create COMPLETE pages with:
✅ Minimum 3-4 sections (hero, grid, features, CTA)
✅ Real content (product names, prices, images)
✅ Interactive elements (buttons, forms, cards)
✅ Proper styling with Tailwind classes

CORRECT Shop page example:
```tsx
export default function Shop() {
  const products = [
    { id: 1, name: "Premium Wireless Headphones", price: 199, image: "/images/product1.jpg" },
    { id: 2, name: "Smart Watch Pro", price: 299, image: "/images/product2.jpg" },
    { id: 3, name: "Ultra HD Camera", price: 499, image: "/images/product3.jpg" }
  ];
  
  return (
    <div className="min-h-screen bg-gray-900">
      <section className="bg-gradient-to-r from-purple-600 to-pink-600 py-20">
        <h1 className="text-4xl font-bold text-center text-white">Shop Our Collection</h1>
      </section>
      
      <section className="container mx-auto px-4 py-12">
        <div className="grid md:grid-cols-3 gap-8">
          {products.map(p => (
            <div key={p.id} className="bg-gray-800 rounded-xl p-4">
              <img src={p.image} className="w-full h-48 object-cover rounded-lg" />
              <h3 className="text-xl font-bold mt-4">{p.name}</h3>
              <p className="text-purple-400">${p.price}</p>
              <button className="mt-4 w-full bg-purple-600 py-2 rounded-lg">Add to Cart</button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}



NEVER create placeholder/empty pages. Each page MUST have:
- Real data (arrays of products, services, team members)
- Proper UI components (cards, grids, forms)
- No "Coming Soon" or placeholder text
- Complete functionality (buttons, forms, interactive elements)









================================================================================
GRADIENT USAGE EXAMPLES:
================================================================================

**Hero Title:**
<h1 className="text-6xl md:text-7xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent animate-gradient">
  Your Title Here
</h1>

**Primary Button:**
<button className="px-6 py-3 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold transition-all duration-300 shadow-lg shadow-purple-500/25">
  Get Started
</button>

**Card with Gradient Border:**
<div className="relative rounded-xl p-6 bg-zinc-900/50 backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300">
  <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 opacity-0 hover:opacity-100 transition-opacity duration-300" />
  Card Content
</div>

**Section Background:**
<section className="relative overflow-hidden bg-gradient-to-b from-purple-950/20 via-zinc-950 to-zinc-950">
  <div className="absolute inset-0 grid-pattern opacity-20" />
  Section Content
</section>



























================================================================================
IMPORT RULES - NO PATH ALIASES (@/*):
================================================================================

**CRITICAL: NEVER use @/ path aliases. Use ONLY relative imports.**

Correct imports:
- In app/layout.tsx: import Navigation from '../components/Navigation'
- In app/page.tsx: import Button from '../components/ui/Button'
- In components/: import { cn } from '../lib/utils'

Wrong imports (NEVER use):
- import Navigation from '@/components/Navigation'
- import Button from '@/components/ui/Button'
- import { cn } from '@/lib/utils'








================================================================================
NAVIGATION & PAGE SYNC RULE - CRITICAL:
================================================================================

**When generating Navigation.tsx with links, you MUST create corresponding page files for EVERY link.**

Example Navigation links:
- <Link href="/showcase"> → MUST create: app/showcase/page.tsx
- <Link href="/solutions"> → MUST create: app/solutions/page.tsx  
- <Link href="/journal"> → MUST create: app/journal/page.tsx
- <Link href="/connect"> → MUST create: app/connect/page.tsx

**EXCEPTION:** Only exclude external links (href starting with http:// or https://)

**Page Content Requirements:**
Each page MUST have unique, creative content based on its name and the project type.









================================================================================
DYNAMIC CONTENT GENERATION - CREATE UNIQUE PAGES FOR EACH REQUEST:
================================================================================

**CRITICAL: DO NOT use generic names like "Products" or "Programs" every time.**
**Generate UNIQUE, CREATIVE names based on the specific project:**

For SCHOOL websites:
- Instead of "Programs" → Use: "Academics", "Courses", "Learning Paths", "Curriculum", "Majors", "Studies"
- Instead of "Admissions" → Use: "Apply", "Join Us", "Enrollment", "Be a Student", "Get Started"
- Instead of "Faculty" → Use: "Our Teachers", "Staff", "Mentors", "Instructors", "Academic Team"
- Instead of "Events" → Use: "Calendar", "Activities", "Announcements", "School Life", "News & Events"
- Instead of "Contact" → Use: "Visit Us", "Get in Touch", "Reach Out", "Connect"

For HOTEL websites:
- Instead of "Rooms" → Use: "Suites", "Accommodations", "Stays", "Lodging", "Guest Rooms"
- Instead of "Amenities" → Use: "Facilities", "Services", "Features", "Experiences", "What We Offer"
- Instead of "Gallery" → Use: "Photos", "Moments", "Visual Tour", "Our Space", "Media"
- Instead of "Contact" → Use: "Reservations", "Book Now", "Inquire", "Plan Your Stay"

For E-COMMERCE websites:
- Instead of "Products" → Use: "Shop", "Store", "Collection", "Catalog", "Browse", "Discover"
- Instead of "Cart" → Use: "Bag", "Basket", "Items", "Your Selections"
- Instead of "Checkout" → Use: "Secure Checkout", "Complete Order", "Payment", "Finalize"

For PORTFOLIO websites:
- Instead of "Work" → Use: "Projects", "Creations", "Showcase", "Portfolio", "Case Studies"
- Instead of "Services" → Use: "What I Do", "Expertise", "Offerings", "Solutions"
- Instead of "Blog" → Use: "Insights", "Articles", "Thoughts", "Journal", "Updates"

For RESTAURANT websites:
- Instead of "Menu" → Use: "Dining", "Cuisine", "Dishes", "Offerings", "Food & Drink"
- Instead of "Reservations" → Use: "Book a Table", "Dine with Us", "Reserve", "Plan Your Visit"
- Instead of "Events" → Use: "Private Dining", "Celebrations", "Special Occasions", "Gatherings"

For GYM/FITNESS websites:
- Instead of "Classes" → Use: "Workouts", "Sessions", "Training", "Programs", "Fitness Plans"
- Instead of "Trainers" → Use: "Coaches", "Instructors", "Trainers", "Fitness Experts"
- Instead of "Membership" → Use: "Plans", "Pricing", "Join Now", "Become a Member"













================================================================================
REQUIRED CORE FILES - ALWAYS CREATE:
================================================================================

app/
  layout.tsx                # Root layout with dark theme (USE RELATIVE IMPORTS)
  page.tsx                  # Dynamic home page with hero, features, testimonials
  globals.css               # Premium styles with animations, gradients, scrollbar


app/(marketing)/            # Route group for marketing pages
  page.tsx                  # Landing page
  layout.tsx                # Marketing layout (optional)

app/(dashboard)/            # Route group for protected pages
  layout.tsx                # Dashboard layout with sidebar
  page.tsx                  # Dashboard home

app/api/                    # API routes (if needed)
  hello/route.ts            # Example API endpoint

app/blog/                   # Blog section
  page.tsx                  # Blog listing with pagination
  [slug]/page.tsx           # Dynamic blog post page

components/
  Navigation.tsx            # Dynamic navigation with creative labels
  Footer.tsx                # Footer with links, social icons, copyright
  Hero.tsx                  # Hero section component
  Features.tsx              # Features grid component
  Testimonials.tsx          # Testimonials slider/component
  CTA.tsx                   # Call to action component
  Newsletter.tsx            # Newsletter signup form
  

  
components/ui/
  Button.tsx                # Reusable button with variants (primary, outline, ghost)
  Card.tsx                  # Card component with hover effects
  Input.tsx                 # Form input component
  Modal.tsx                 # Modal dialog component
  Dropdown.tsx              # Dropdown menu component
  Tabs.tsx                  # Tabs component
  Accordion.tsx             # Accordion/FAQ component
  


components/layout/
  Header.tsx                # Header wrapper
  Container.tsx             # Responsive container
  Section.tsx               # Section with padding and background

lib/
  utils.ts                  # cn utility function for Tailwind merging
  constants.ts              # Site constants (name, description, links)
  metadata.ts               # SEO metadata helper
  api.ts                    # API client functions (optional)

hooks/
  useScroll.ts              # Scroll position hook
  useMediaQuery.ts          # Responsive breakpoint hook
  useLocalStorage.ts        # Local storage hook
  useDebounce.ts            # Debounce hook

types/
  index.ts                  # TypeScript interfaces and types

styles/
  globals.css               # Global styles (main file)
  components.css            # Component-specific styles (optional)

public/
  images/                   # All image assets
    og-image.png            # Open Graph image for social sharing
    favicon.ico             # Browser favicon
    logo.svg                # Site logo
  fonts/                    # Custom fonts (if any)

================================================================================
ADDITIONAL FILES FOR SPECIFIC PROJECT TYPES:
================================================================================

SCHOOL WEBSITE:
app/courses/page.tsx        # Course listing with filters
app/courses/[id]/page.tsx   # Course detail page
app/admissions/page.tsx     # Admissions process and form
app/faculty/page.tsx        # Teacher/Staff profiles
app/events/page.tsx         # Events calendar
components/CourseCard.tsx   # Course card component
components/EventCard.tsx    # Event card component

COFFEE WEBSITE:
app/menu/page.tsx           # Menu with categories
app/shop/page.tsx           # Product listing
app/locations/page.tsx      # Store locations with map
app/subscription/page.tsx   # Subscription plans
components/ProductCard.tsx  # Product card
components/Cart.tsx         # Shopping cart

HOTEL WEBSITE:
app/rooms/page.tsx          # Room types listing
app/rooms/[id]/page.tsx     # Room detail with booking
app/amenities/page.tsx      # Hotel amenities
app/gallery/page.tsx        # Photo gallery
app/offers/page.tsx         # Special offers/packages
components/BookingForm.tsx  # Room booking form
components/RoomCard.tsx      # Room card component

RESTAURANT WEBSITE:
app/menu/page.tsx           # Food and drink menu
app/reservations/page.tsx   # Table booking form
app/events/page.tsx         # Private dining events
components/MenuItem.tsx     # Menu item component
components/ReservationForm.tsx # Booking form

GYM WEBSITE:
app/classes/page.tsx        # Class schedule
app/trainers/page.tsx       # Trainer profiles
app/membership/page.tsx     # Pricing plans
app/schedule/page.tsx       # Weekly class timetable
components/ClassCard.tsx    # Class card
components/TrainerCard.tsx  # Trainer profile card

E-COMMERCE WEBSITE:
app/products/page.tsx       # Product listing with filters
app/products/[id]/page.tsx  # Product detail
app/cart/page.tsx           # Shopping cart
app/checkout/page.tsx       # Checkout flow
app/account/page.tsx        # User account
components/ProductCard.tsx  # Product card
components/CartItem.tsx     # Cart item component

PORTFOLIO WEBSITE:
app/projects/page.tsx       # Project gallery
app/projects/[slug]/page.tsx # Project case study
app/services/page.tsx       # Services offered
components/ProjectCard.tsx  # Project card
components/SkillBadge.tsx   # Skill/technology badges




================================================================================
VERCEL DEPLOYMENT REQUIRED FILES (ALWAYS CREATE):
================================================================================

package.json                 # Dependencies and scripts (MUST have build/dev/start)
package-lock.json            # Lock file (optional, AI can skip)
next.config.js               # Next.js configuration (images domains, etc.)
postcss.config.mjs           # PostCSS config with tailwindcss and autoprefixer (MUST be .mjs)
tailwind.config.ts           # Tailwind config with content paths
tsconfig.json                # TypeScript config (NO path aliases @/*)
next-env.d.ts                # Next.js TypeScript references
.gitignore                   # Ignore node_modules, .next, .env
.env.example                 # Example environment variables


================================================================================
CRITICAL RULES:
================================================================================

1. EVERY navigation link MUST have a corresponding page file
2. EVERY page MUST have AT LEAST 3 content sections
3. EVERY page MUST use images from /public/images/
4. ALL imports MUST be relative (NO @/* path aliases)
5. ALL client components MUST have "use client" directive at top
6. EVERY array .map() MUST have unique content for each item
7. ALL pages MUST be responsive (mobile-first design)
8. EVERY component MUST have proper TypeScript types








================================================================================
🚨🚨🚨 CRITICAL: GENERATE UNIQUE CONTENT FOR EACH ARRAY ITEM 🚨🚨🚨
================================================================================

When you use array mapping like {[1, 2, 3].map(...)}, you MUST generate DIFFERENT content for EACH item.

NEVER repeat the same text for all items. ALWAYS vary:

1. **Titles**: Use different names (e.g., "Project Alpha", "Project Beta", "Project Gamma")
2. **Descriptions**: Write unique descriptions for each item (different features, different benefits)
3. **Images**: Use different image paths (/images/image_1.jpg, /images/image_2.jpg, /images/image_3.jpg)
4. **Tags/Skills**: Use different technology stacks for each item

Example - GOOD (different content for each):
```jsx
{[1, 2, 3].map((i) => {
  const items = [
    { title: "EagleCode AI", desc: "AI-powered development platform", img: "/images/image_1.jpg", tags: ["Next.js", "AI"] },
    { title: "Portfolio Pro", desc: "High-end developer portfolio", img: "/images/image_2.jpg", tags: ["React", "Tailwind"] },
    { title: "E-Commerce Store", desc: "Full-featured online store", img: "/images/image_3.jpg", tags: ["Stripe", "PostgreSQL"] }
  ];
  const item = items[i-1];
  return (
    <div>
      <img src={item.img} alt={item.title} />
      <h3>{item.title}</h3>
      <p>{item.desc}</p>
      <div>{item.tags.map(tag => <span>{tag}</span>)}</div>
    </div>
  );
})}













================================================================================
🚨🚨🚨 CRITICAL: NAVIGATION LINKS REQUIRE CORRESPONDING PAGES 🚨🚨🚨
================================================================================

**For EVERY link in Navigation.tsx, you MUST create a corresponding page file.**

If Navigation.tsx has:
<Link href="/classes">Classes</Link>
<Link href="/trainers">Trainers</Link>
<Link href="/membership">Membership</Link>

Then you MUST create:
- app/classes/page.tsx
- app/trainers/page.tsx
- app/membership/page.tsx

**FAILURE TO CREATE THESE PAGES WILL CAUSE 404 ERRORS!**












Each page MUST have MEANINGFUL content based on its name:

For "/classes" page (Gym website):
- Hero section about classes
- Grid of class cards (Yoga, HIIT, Strength, Pilates, etc.)
- Class schedule or timetable
- Instructor names and times

For "/trainers" page:
- Trainer profiles with images, names, specialties
- Bio descriptions
- Social links or certifications

For "/membership" page:
- Pricing plans (Basic, Pro, Premium)
- Feature comparison table
- Sign up CTA buttons

For "/contact" page:
- Contact form (name, email, message)
- Location map or address
- Hours of operation
- Phone/email information

**you mustt create unique, rich content for each page.







**NEVER create empty or placeholder pages. Each page must have rich, meaningful content.**

================================================================================
EXAMPLE - CORRECT IMPLEMENTATION:
================================================================================

Navigation.tsx links:
- /classes → app/classes/page.tsx (rich content with class grid and schedule)
- /trainers → app/trainers/page.tsx (trainer profiles with images and bios)
- /membership → app/membership/page.tsx (pricing plans and benefits)
- /contact → app/contact/page.tsx (contact form and information)

================================================================================
EXAMPLE - WRONG (NEVER DO THIS):
================================================================================

❌ Creating empty pages:
app/classes/page.tsx = "export default function Classes() { return <div>Classes</div>; }"

❌ Missing pages for navigation links
❌ Using the same content for all pages
❌ Pages without images, cards, or interactive elements

















  
================================================================================
CSS CONFIGURATION FILES:
================================================================================

"postcss.config.mjs": "export default {\\n  plugins: {\\n    tailwindcss: {},\\n    autoprefixer: {},\\n  },\\n}"






















================================================================================
ROOT LAYOUT - WITH RELATIVE IMPORTS:
================================================================================




"app/layout.tsx": "import type { Metadata } from 'next';\\nimport './globals.css';\\nimport Navigation from '../components/Navigation';\\n\\nexport const metadata: Metadata = {\\n  title: {\\n    template: '%s | {{PROJECT_NAME}}',\\n    default: '{{PROJECT_NAME}}',\\n  },\\n  description: '[UNIQUE_DESCRIPTION_FROM_REQUEST]',\\n};\\n\\nexport default function RootLayout({\\n  children,\\n}: {\\n  children: React.ReactNode;\\n}) {\\n  return (\\n    <html lang=\\"en\\" className=\\"dark\\">\\n      <body className=\\"bg-zinc-950 text-white antialiased\\">\\n        <Navigation />\\n        <main className=\\"min-h-screen\\">{children}</main>\\n      </body>\\n    </html>\\n  );\\n}"



================================================================================
ERROR PAGE - WITH USE CLIENT:
================================================================================

"app/error.tsx": "\"use client\";\\n\\nimport { useEffect } from 'react';\\n\\nexport default function Error({\\n  error,\\n  reset,\\n}: {\\n  error: Error & { digest?: string };\\n  reset: () => void;\\n}) {\\n  useEffect(() => {\\n    console.error(error);\\n  }, [error]);\\n\\n  return (\\n    <div className=\\"min-h-screen flex items-center justify-center\\">\\n      <div className=\\"text-center space-y-4\\">\\n        <h2 className=\\"text-2xl font-bold text-red-500\\">Something went wrong!</h2>\\n        <p className=\\"text-gray-400\\">{error.message || 'An unexpected error occurred'}</p>\\n        <button\\n          onClick={reset}\\n          className=\\"px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors\\"\\n        >\\n          Try again\\n        </button>\\n      </div>\\n    </div>\\n  );\\n}"

================================================================================
LOADING PAGE:
================================================================================

"app/loading.tsx": "export default function Loading() {\\n  return (\\n    <div className=\\"min-h-screen flex items-center justify-center\\">\\n      <div className=\\"animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent\\"></div>\\n    </div>\\n  );\\n}"

================================================================================
NOT FOUND PAGE:
================================================================================

"app/not-found.tsx": "import Link from 'next/link';\\n\\nexport default function NotFound() {\\n  return (\\n    <div className=\\"min-h-screen flex items-center justify-center\\">\\n      <div className=\\"text-center space-y-4\\">\\n        <h1 className=\\"text-6xl font-bold text-purple-500\\">404</h1>\\n        <h2 className=\\"text-2xl font-semibold\\">Page Not Found</h2>\\n        <p className=\\"text-gray-400\\">The page you're looking for doesn't exist.</p>\\n        <Link\\n          href=\\"/\\"\\n          className=\\"inline-block px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors\\"\\n        >\\n          Return Home\\n        </Link>\\n      </div>\\n    </div>\\n  );\\n}"

================================================================================
BUTTON COMPONENT - WITH RELATIVE IMPORTS:
================================================================================

"components/ui/Button.tsx": "\"use client\";\\n\\nimport { cn } from '../../lib/utils';\\nimport { Slot } from '@radix-ui/react-slot';\\nimport { forwardRef } from 'react';\\n\\ninterface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {\\n  variant?: 'default' | 'primary' | 'outline' | 'ghost';\\n  size?: 'sm' | 'default' | 'lg';\\n  isLoading?: boolean;\\n  fullWidth?: boolean;\\n  asChild?: boolean;\\n}\\n\\nconst Button = forwardRef<HTMLButtonElement, ButtonProps>(\\n  ({ \\n    className, \\n    variant = 'default', \\n    size = 'default',\\n    isLoading = false,\\n    fullWidth = false,\\n    asChild = false,\\n    children, \\n    disabled,\\n    ...props \\n  }, ref) => {\\n    const variants = {\\n      default: 'bg-purple-600 text-white hover:bg-purple-700 shadow-lg shadow-purple-600/25',\\n      primary: 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-600/25',\\n      outline: 'border border-white/20 bg-transparent hover:bg-white/10 text-white',\\n      ghost: 'hover:bg-white/10 text-gray-300 hover:text-white',\\n    };\\n    \\n    const sizes = {\\n      sm: 'h-8 px-3 text-xs rounded-lg',\\n      default: 'h-10 px-4 py-2 text-sm rounded-lg',\\n      lg: 'h-12 px-6 text-base rounded-lg',\\n    };\\n    \\n    const Comp = asChild ? Slot : 'button';\\n    \\n    return (\\n      <Comp\\n        ref={ref}\\n        className={cn(\\n          \\"inline-flex items-center justify-center gap-2 font-medium transition-all duration-200\\",\\n          \\"disabled:opacity-50 disabled:cursor-not-allowed\\",\\n          \\"focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-zinc-950\\",\\n          \\"active:scale-95\\",\\n          variants[variant],\\n          sizes[size],\\n          fullWidth && \\"w-full\\",\\n          className\\n        )}\\n        disabled={disabled || isLoading}\\n        {...props}\\n      >\\n        {isLoading && (\\n          <div className=\\"animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent\\" />\\n        )}\\n        {children}\\n      </Comp>\\n    );\\n  }\\n);\\n\\nButton.displayName = 'Button';\\n\\nexport { Button };"

================================================================================
LIB/UTILS.TS:
================================================================================

"lib/utils.ts": "import { type ClassValue, clsx } from \\"clsx\\";\\nimport { twMerge } from \\"tailwind-merge\\";\\n\\nexport function cn(...inputs: ClassValue[]) {\\n  return twMerge(clsx(inputs));\\n}"

================================================================================
TAILWIND CONFIG:
================================================================================

"tailwind.config.ts": "import type { Config } from 'tailwindcss';\\n\\nconst config: Config = {\\n  darkMode: 'class',\\n  content: [\\n    './pages/**/*.{js,ts,jsx,tsx,mdx}',\\n    './components/**/*.{js,ts,jsx,tsx,mdx}',\\n    './app/**/*.{js,ts,jsx,tsx,mdx}',\\n  ],\\n  theme: {\\n    extend: {\\n      colors: {\\n        border: 'hsl(var(--border))',\\n        background: 'hsl(var(--background))',\\n        foreground: 'hsl(var(--foreground))',\\n      },\\n      animation: {\\n        'gradient': 'gradient 3s ease infinite',\\n        'shimmer': 'shimmer 3s ease infinite',\\n        'float': 'float 6s ease-in-out infinite',\\n        'pulse-slow': 'pulse-slow 3s ease-in-out infinite',\\n      },\\n      keyframes: {\\n        gradient: {\\n          '0%, 100%': { backgroundPosition: '0% 50%' },\\n          '50%': { backgroundPosition: '100% 50%' },\\n        },\\n        shimmer: {\\n          '0%': { backgroundPosition: '0% 50%' },\\n          '50%': { backgroundPosition: '100% 50%' },\\n          '100%': { backgroundPosition: '0% 50%' },\\n        },\\n        float: {\\n          '0%, 100%': { transform: 'translateY(0px)' },\\n          '50%': { transform: 'translateY(-20px)' },\\n        },\\n        'pulse-slow': {\\n          '0%, 100%': { opacity: '0.5' },\\n          '50%': { opacity: '1' },\\n        },\\n      },\\n    },\\n  },\\n  plugins: [],\\n};\\n\\nexport default config;"

================================================================================
TSCONFIG.JSON - NO PATH ALIASES:
================================================================================

"tsconfig.json": "{\\n  \\"compilerOptions\\": {\\n    \\"lib\\": [\\"dom\\", \\"dom.iterable\\", \\"esnext\\"],\\n    \\"allowJs\\": true,\\n    \\"skipLibCheck\\": true,\\n    \\"strict\\": true,\\n    \\"noEmit\\": true,\\n    \\"module\\": \\"esnext\\",\\n    \\"moduleResolution\\": \\"bundler\\",\\n    \\"resolveJsonModule\\": true,\\n    \\"isolatedModules\\": true,\\n    \\"jsx\\": \\"preserve\\",\\n    \\"incremental\\": true,\\n    \\"plugins\\": [{\\"name\\": \\"next\\"}],\\n    \\"esModuleInterop\\": true\\n  },\\n  \\"include\\": [\\"next-env.d.ts\\", \\".next/types/**/*.ts\\", \\"**/*.ts\\", \\"**/*.tsx\\"],\\n  \\"exclude\\": [\\"node_modules\\"]\\n}"






================================================================================
PACKAGE.JSON:
================================================================================




"package.json": "{\\n  \\"name\\": \\"scorpio-app\\",\\n  \\"version\\": \\"0.1.0\\",\\n  \\"private\\": true,\\n  \\"scripts\\": {\\n    \\"dev\\": \\"next dev\\",\\n    \\"build\\": \\"next build\\",\\n    \\"start\\": \\"next start\\"\\n  },\\n  \\"dependencies\\": {\\n    \\"next\\": \\"14.2.35\\",\\n    \\"react\\": \\"^18.3.1\\",\\n    \\"react-dom\\": \\"^18.3.1\\",\\n    \\"lucide-react\\": \\"^0.446.0\\",\\n    \\"@radix-ui/react-slot\\": \\"^1.1.0\\",\\n    \\"clsx\\": \\"^2.1.1\\",\\n    \\"tailwind-merge\\": \\"^2.5.0\\"\\n  },\\n  \\"devDependencies\\": {\\n    \\"@types/node\\": \\"^22.9.0\\",\\n    \\"@types/react\\": \\"^18.3.12\\",\\n    \\"@types/react-dom\\": \\"^18.3.1\\",\\n    \\"autoprefixer\\": \\"^10.4.20\\",\\n    \\"postcss\\": \\"^8.4.49\\",\\n    \\"tailwindcss\\": \\"^3.4.15\\",\\n    \\"typescript\\": \\"^5.6.3\\"\\n  }\\n}"




================================================================================
Now generate the complete project for this request: [USER_PROMPT_HERE]"""



























































@app.websocket("/ws/build")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Flag to track if build is complete
    build_complete = False
    project_files = None  # Store files for status checks

    try:
        versions = await get_stable_versions()

        raw_payload = await websocket.receive_text()
        data = json.loads(raw_payload)
        user_prompt = data.get("prompt", "").strip()
        max_retries = 3
        retry_count = 0

        if not user_prompt:
            await websocket.send_json({"type": "error", "message": "Prompt is required"})
            # Don't close - just keep connection alive
            while True:
                await asyncio.sleep(60)
                try:
                    await websocket.send_json({"type": "heartbeat"})
                except:
                    return
            return

        # Generate unique project name
        project_name = name_tracker.generate_unique_name("school", user_prompt)

        # Send project name to frontend
        await websocket.send_json({
            "type": "project_name",
            "name": project_name
        })

        # ── Always-defined variables (never undefined later) ──
        needs_images = True
        _pl = user_prompt.lower()
        image_data = {}
        image_metadata = {}

















        # ========== SMART THEME DETECTION USING AI ==========
        await websocket.send_json({
            "type": "status",
            "message": "🎯 Analyzing your request for relevant images..."
        })
        
        # Use AI to extract theme and generate search terms
        theme_prompt = f"""Analyze this user request and return ONLY a JSON object with:
1. "theme": one word describing the main visual theme (e.g., wildlife, coastal, mountain, urban, forest, luxury, tech, food, fitness, education)
2. "keywords": 2 specific image search terms (max 3 words each) that would find relevant high-quality photos

User request: "{user_prompt}"

Return ONLY valid JSON like this:
{{"theme": "wildlife", "keywords": ["wild animals in nature", "safari wildlife photography", "animals in natural habitat"]}}"""

        try:
            theme_response = await model_router.generate_content(
                prompt=theme_prompt,
                config={
                    "temperature": 0.1,
                    "max_output_tokens": 200,
                    "response_mime_type": "application/json",
                }
            )
            
            theme_data = json.loads(clean_json_response(theme_response))
            detected_theme = theme_data.get("theme", "")
            search_terms = theme_data.get("keywords", [])
            
            print(f"🎨 AI detected theme: {detected_theme}")
            print(f"🔍 AI generated search terms: {search_terms}")
            
        except Exception as e:
            print(f"⚠️ AI theme detection failed: {e}, using fallback")
            detected_theme = ""
            search_terms = []
        
        # Fallback to project-type based search if AI fails
        if not search_terms:
            # Your existing project-type detection here
            if any(w in _pl for w in ['hotel', 'resort', 'lodge']):
                search_terms = ['luxury hotel interior', 'resort pool', 'hotel room elegant']
            elif any(w in _pl for w in ['coffee', 'cafe', 'roastery']):
                search_terms = ['coffee shop interior', 'barista making coffee', 'coffee beans']
            elif any(w in _pl for w in ['school', 'academy', 'university']):
                search_terms = ['modern campus', 'students studying', 'classroom learning']
            elif any(w in _pl for w in ['wild', 'animal', 'wildlife', 'nature']):
                search_terms = ['wild animals nature', 'wildlife photography', 'animals in wild']
            else:
                search_terms = ['modern architecture', 'professional office', 'abstract background']
        
        print(f"🔍 Final search terms: {search_terms}")























        # ========== START IMAGE SEARCH IN BACKGROUND (NON-BLOCKING) ==========
        image_data = {}
        image_metadata = {}
        used_search_terms = []
        image_task_complete = False
        
        # Create background task for image search
        async def fetch_images_background():
            nonlocal image_data, image_metadata, used_search_terms, image_task_complete
            for i, term in enumerate(search_terms[:2]):  # Only 2 images
                try:
                    await websocket.send_json({
                        "type": "status",
                        "message": f"🔍 Searching for image {i+1}/2 in background..."
                    })
                    images = await search_free_images(term, 1, previous_terms=used_search_terms)
                    if images:
                        img_key = f"image_{i+1}"
                        img_url = images[0]["url"]
                        img_base64 = await get_image_as_base64(img_url)
                        if img_base64:
                            image_data[img_key] = img_base64
                            image_metadata[img_key] = {
                                "term": term,
                                "source": images[0]["source"],
                                "attribution": images[0]["attribution"],
                                "license": images[0]["license"],
                            }
                            used_search_terms.append(term)
                            await websocket.send_json({
                                "type": "status",
                                "message": f"✅ Image {i+1}/2 found (while generating project)"
                            })
                        else:
                            image_data[f"image_{i+1}"] = ""
                            image_metadata[f"image_{i+1}"] = {"term": term, "source": "placeholder", "attribution": "", "license": ""}
                    else:
                        image_data[f"image_{i+1}"] = ""
                        image_metadata[f"image_{i+1}"] = {"term": term, "source": "placeholder", "attribution": "", "license": ""}
                except Exception as e:
                    print(f"Error searching images for {term}: {e}")
                    image_data[f"image_{i+1}"] = ""
                    image_metadata[f"image_{i+1}"] = {"term": term, "source": "placeholder", "attribution": "", "license": ""}
            image_task_complete = True
            print(f"📸 Background image search complete. Found: {len([k for k in image_data if image_data[k]])}/2")
        
        # Start image search in BACKGROUND (does NOT wait)
        background_image_task = asyncio.create_task(fetch_images_background())
        
        # Send status that generation started immediately
        await websocket.send_json({
            "type": "status",
            "message": "🚀 Starting project generation (images loading in background)..."
        })

        # ========== RETRY LOOP ==========
        while retry_count < max_retries:
            print(f"\n{'='*70}")
            print(f"🔄 Attempt {retry_count + 1}/{max_retries}")
            if retry_count > 0:
                print(f"⏳ Retrying due to JSON parse error...")
            print(f"{'='*70}\n")

            full_response = ""
            detected_files: set = set()





















            print(f"\n{'='*70}")
            print(f"🔄 Attempt {retry_count + 1}/{max_retries}")
            if retry_count > 0:
                print(f"⏳ Retrying due to JSON parse error...")
            print(f"{'='*70}\n")

            full_response = ""
            detected_files: set = set()





               # ── Build the full prompt ──
            base_prompt = MASTER_BUILD_PROMPT

            name_instruction = f"""
================================================================================
CRITICAL: USE THIS EXACT PROJECT NAME
================================================================================

The project MUST be named: "{project_name}"

You MUST use this exact name everywhere:
- In the Navigation.tsx brand/logo
- In the layout.tsx metadata title
- In the home page heading
- In any other place that displays the business/project name

DO NOT generate your own name. DO NOT use "Apex", "Summit", or any other name.
Use EXACTLY: {project_name}

================================================================================
"""

            if needs_images and image_data:
                _is_hotel      = any(w in _pl for w in ['hotel', 'resort', 'lodge', 'inn', 'villa', 'retreat', 'spa'])
                _is_coffee     = any(w in _pl for w in ['coffee', 'cafe', 'roastery', 'brew', 'barista'])
                _is_school     = any(w in _pl for w in ['school', 'academy', 'university', 'college', 'education', 'campus'])
                _is_gym        = any(w in _pl for w in ['gym', 'fitness', 'workout', 'training', 'athlete'])
                _is_restaurant = any(w in _pl for w in ['restaurant', 'bistro', 'dining', 'food', 'kitchen'])
                _is_ecommerce  = any(w in _pl for w in ['shop', 'store', 'ecommerce', 'product', 'market'])

                # Only show images that were actually found (max 2)
                image_lines = []
                for key, meta in image_metadata.items():
                    if meta.get('term'):  # Only show images that have content
                        image_lines.append(
                            f"  - {key} → src=\"/images/{key}.jpg\"  (subject: {meta['term']})"
                        )
                image_list_str = "\n".join(image_lines) if image_lines else "No real images available. Use styled gradient cards instead."

                # UPDATED HERO HINTS - ONLY 2 IMAGES MAX
                if _is_hotel:
                    hero_hint = """\
🚨 ONLY 2 IMAGES AVAILABLE - USE THEM WISELY 🚨

FOR THIS HOTEL/RESORT SITE:
- Use image_1.jpg ONLY for the FULL-PAGE hero background
- For ALL room cards, amenities, and other sections → USE STYLED GRADIENT CARDS (NO images needed)

HERO CODE (use image_1.jpg only):
<section className="relative min-h-screen flex items-center justify-center overflow-hidden">
  <img src="/images/image_1.jpg" alt="Hero background" className="absolute inset-0 w-full h-full object-cover" />
  <div className="absolute inset-0 bg-black/55" />
  <div className="relative z-10 text-center text-white px-6">{/* hero content */}</div>
</section>

STYLED CARD FOR ROOMS/AMENITIES (NO image needed):
<div className="group relative bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-xl p-6 backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300">
  <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center mb-4">
    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  </div>
  <h3 className="text-xl font-semibold mb-2">Room/Deluxe Suite</h3>
  <p className="text-gray-400">Luxury amenities with ocean view</p>
</div>

DO NOT request or use image_2.jpg or image_3.jpg for cards."""

                elif _is_coffee:
                    hero_hint = """\
🚨 ONLY 2 IMAGES AVAILABLE - USE THEM WISELY 🚨

FOR THIS COFFEE SITE:
- Use image_1.jpg ONLY for the hero section
- For ALL product/menu cards → USE STYLED GRADIENT CARDS (NO images needed)

HERO CODE (use image_1.jpg only):
<section className="relative h-[90vh] flex items-center overflow-hidden">
  <img src="/images/image_1.jpg" alt="Coffee hero" className="absolute inset-0 w-full h-full object-cover" />
  <div className="absolute inset-0 bg-black/60" />
  <div className="relative z-10 px-8">{/* headline + CTA */}</div>
</section>

STYLED CARD FOR COFFEE ITEMS (NO image needed):
<div className="text-center p-6 rounded-xl bg-gradient-to-br from-amber-950/40 to-orange-950/30 border border-white/10 hover:scale-105 transition-all duration-300">
  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-center">
    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
    </svg>
  </div>
  <h3 className="text-xl font-semibold mb-2">Espresso Blend</h3>
  <p className="text-gray-400">Rich, bold, and aromatic</p>
</div>

DO NOT request or use image_2.jpg for product cards."""

                elif _is_school:
                    hero_hint = """\
🚨 ONLY 2 IMAGES AVAILABLE - USE THEM WISELY 🚨

FOR THIS SCHOOL SITE:
- Use image_1.jpg ONLY for the campus hero
- For ALL course/faculty cards → USE STYLED GRADIENT CARDS (NO images needed)

HERO CODE (use image_1.jpg only):
<section className="relative h-[80vh] flex items-center overflow-hidden">
  <img src="/images/image_1.jpg" alt="Campus hero" className="absolute inset-0 w-full h-full object-cover" />
  <div className="absolute inset-0 bg-indigo-900/50" />
  <div className="relative z-10 container mx-auto px-6">{/* headline + apply button */}</div>
</section>

STYLED CARD FOR COURSES (NO image needed):
<div className="relative overflow-hidden rounded-xl bg-zinc-900/50 border border-white/10 p-6 group hover:border-purple-500/50 transition-all duration-300">
  <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-full blur-2xl" />
  <div className="relative z-10">
    <h3 className="text-lg font-semibold mb-2">Mathematics</h3>
    <p className="text-gray-400 text-sm">Advanced calculus and algebra</p>
  </div>
</div>

DO NOT request or use image_2.jpg for cards."""

                elif _is_gym:
                    hero_hint = """\
🚨 ONLY 2 IMAGES AVAILABLE - USE THEM WISELY 🚨

FOR THIS GYM SITE:
- Use image_1.jpg ONLY for the hero section
- For ALL class/trainer cards → USE STYLED GRADIENT CARDS (NO images needed)

HERO CODE (use image_1.jpg only):
<section className="relative min-h-screen flex items-end overflow-hidden">
  <img src="/images/image_1.jpg" alt="Gym hero" className="absolute inset-0 w-full h-full object-cover" />
  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />
  <div className="relative z-10 container mx-auto px-6 pb-20">{/* headline + join button */}</div>
</section>

STYLED CARD FOR CLASSES (NO image needed):
<div className="group relative bg-gradient-to-br from-green-600/20 to-emerald-600/20 rounded-xl p-6 backdrop-blur-sm border border-white/10 hover:border-green-500/50 transition-all duration-300">
  <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center mb-4">
    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  </div>
  <h3 className="text-xl font-semibold mb-2">HIIT Class</h3>
  <p className="text-gray-400">High intensity interval training</p>
</div>

DO NOT request or use image_2.jpg for cards."""

                elif _is_restaurant:
                    hero_hint = """\
🚨 ONLY 2 IMAGES AVAILABLE - USE THEM WISELY 🚨

FOR THIS RESTAURANT SITE:
- Use image_1.jpg ONLY for the hero ambiance
- For ALL menu items → USE STYLED GRADIENT CARDS (NO images needed)

HERO CODE (use image_1.jpg only):
<section className="relative h-screen flex items-center justify-center overflow-hidden">
  <img src="/images/image_1.jpg" alt="Restaurant hero" className="absolute inset-0 w-full h-full object-cover" />
  <div className="absolute inset-0 bg-black/50" />
  <div className="relative z-10 text-center text-white px-6">{/* name + reserve button */}</div>
</section>

STYLED CARD FOR MENU (NO image needed):
<div className="flex justify-between items-center p-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-300">
  <div>
    <h3 className="font-semibold">Grilled Salmon</h3>
    <p className="text-sm text-gray-400">Fresh Atlantic salmon</p>
  </div>
  <span className="text-purple-400 font-bold">$28</span>
</div>

DO NOT request or use image_2.jpg for menu items."""

                elif _is_ecommerce:
                    hero_hint = """\
🚨 ONLY 2 IMAGES AVAILABLE - USE THEM WISELY 🚨

FOR THIS STORE SITE:
- Use image_1.jpg ONLY for the hero banner
- For ALL product cards → USE STYLED GRADIENT CARDS (NO images needed)

HERO CODE (use image_1.jpg only):
<section className="relative h-[70vh] flex items-center overflow-hidden rounded-2xl mx-4 mt-4">
  <img src="/images/image_1.jpg" alt="Store hero" className="absolute inset-0 w-full h-full object-cover" />
  <div className="absolute inset-0 bg-black/40" />
  <div className="relative z-10 px-10">{/* tagline + shop now button */}</div>
</section>

STYLED CARD FOR PRODUCTS (NO image needed):
<div className="group relative bg-gradient-to-br from-pink-600/20 to-purple-600/20 rounded-xl p-6 backdrop-blur-sm border border-white/10 hover:border-pink-500/50 transition-all duration-300">
  <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-pink-500 to-purple-500 flex items-center justify-center mb-4">
    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
    </svg>
  </div>
  <h3 className="text-xl font-semibold mb-2">Product Name</h3>
  <p className="text-gray-400">$49.99</p>
</div>

DO NOT request or use image_2.jpg for product cards."""

                else:
                    hero_hint = """\
🚨 ONLY 2 IMAGES AVAILABLE 🚨
- Use image_1.jpg for hero background ONLY
- For ALL cards, features, and other sections → USE STYLED GRADIENT CARDS (NO images)
- NEVER request image_2.jpg or image_3.jpg for cards
- Use SVG icons from lucide-react for all visual elements"""

                image_instructions = f"""
================================================================================
IMAGE ASSETS — MAXIMUM 2 IMAGES ONLY
================================================================================

🚨 CRITICAL: You have ONLY {len(image_lines)} real image(s). Use them sparingly.

Available images:
{image_list_str}

{hero_hint}

STYLED CARD TEMPLATES (USE THESE FOR ALL CARDS - NO IMAGES NEEDED):

1. Gradient Background Card:
<div className="group relative bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-xl p-6 backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300">
  <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
  <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center mb-4">
    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  </div>
  <h3 className="text-xl font-semibold mb-2">Feature Title</h3>
  <p className="text-gray-400">Description without needing images</p>
</div>

2. Minimal Glass Card:
<div className="p-6 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-300">
  <h3 className="text-lg font-semibold mb-2">Title</h3>
  <p className="text-gray-400 text-sm">Content here</p>
</div>

3. Animated Border Card:
<div className="relative rounded-xl p-6 bg-zinc-900/50 border border-white/10 hover:border-purple-500/50 transition-all duration-300">
  <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 opacity-0 hover:opacity-100 transition-opacity duration-300" />
  <h3 className="text-xl font-semibold mb-2">Title</h3>
  <p className="text-gray-400">Description</p>
</div>

================================================================================
CRITICAL RULES:
================================================================================
1. ONLY use image_1.jpg (hero background) - NO other real images
2. ALL cards, features, products, rooms, classes MUST use styled gradient cards above
3. Use lucide-react icons for ALL visual elements in cards
4. Reference image_2.jpg 
5. Project must be FAST and SMALL - no unnecessary images
6. Only 3 maximum images a website should contain

================================================================================
"""
                full_prompt = f"{base_prompt}\n\n{name_instruction}\n\n{image_instructions}\n\nUser Request: {user_prompt}"
            else:
                full_prompt = f"{base_prompt}\n\n{name_instruction}\n\nUser Request: {user_prompt}"



























































            # ========== STREAMING GENERATION WITH TIMEOUT ==========
            stream_timeout = 180  # 3 minutes timeout for Render.com free tier
            stream_start_time = asyncio.get_event_loop().time()
            max_stream_retries = 2
            stream_retry_count = 0
            stream_success = False
            
            while not stream_success and stream_retry_count <= max_stream_retries:
                try:
                    if stream_retry_count > 0:
                        print(f"🔄 Streaming retry attempt {stream_retry_count}/{max_stream_retries}")
                        await websocket.send_json({
                            "type": "status",
                            "message": f"Retrying generation (attempt {stream_retry_count}/{max_stream_retries})..."
                        })
                        # Simplify prompt on retry
                        if stream_retry_count == 1:
                            full_prompt = full_prompt[:12000]
                            print(f"📝 Prompt truncated to 12000 chars")
                        elif stream_retry_count == 2:
                            full_prompt = full_prompt[:8000]
                            print(f"📝 Prompt truncated to 8000 chars")
                    
                    print(f"📡 Starting streaming generation (attempt {stream_retry_count + 1})...")
                    print(f"⏱️ Timeout set to {stream_timeout} seconds")

                    # ✅ FIX: Don't await the async generator
                    response_stream = model_router.generate_stream(
                        prompt=full_prompt,
                        config={
                            "response_mime_type": "application/json",
                            "temperature": 0.1 if stream_retry_count == 0 else 0.01,
                        }
                    )

                    chunk_count = 0
                    last_chunk_time = asyncio.get_event_loop().time()
                    
                    # Add timeout per chunk instead
                    async for chunk in response_stream:
                        # Check overall timeout
                        if asyncio.get_event_loop().time() - stream_start_time > stream_timeout:
                            raise asyncio.TimeoutError(f"Streaming exceeded {stream_timeout} seconds")
                        
                        if hasattr(chunk, 'text') and chunk.text:
                            chunk_text = chunk.text
                            full_response += chunk_text
                            chunk_count += 1
                            last_chunk_time = asyncio.get_event_loop().time()
                            
                            # Log progress every 20 chunks
                            if chunk_count % 20 == 0:
                                elapsed = asyncio.get_event_loop().time() - stream_start_time
                                print(f"📊 Received {chunk_count} chunks in {elapsed:.1f}s, total {len(full_response)} chars")

                            new_files = extract_file_paths_from_chunk(chunk_text)
                            for file_path in new_files:
                                if file_path not in detected_files:
                                    detected_files.add(file_path)
                                    await websocket.send_json({"type": "file_generating", "file": file_path})
                                    await asyncio.sleep(0.01)

                            await websocket.send_json({"type": "chunk", "content": chunk_text})
                            await asyncio.sleep(0.005)
                    
                    total_time = asyncio.get_event_loop().time() - stream_start_time
                    print(f"✅ Streaming completed in {total_time:.1f}s, {chunk_count} chunks, {len(full_response)} chars")
                    
                    if len(full_response) < 100:
                        raise Exception(f"Response too short ({len(full_response)} chars)")
                    
                    stream_success = True
                    break
                    
                except asyncio.TimeoutError:
                    elapsed = asyncio.get_event_loop().time() - stream_start_time
                    print(f"❌ Streaming timeout after {elapsed:.1f}s (limit: {stream_timeout}s) - Attempt {stream_retry_count + 1}")
                    stream_retry_count += 1
                    if stream_retry_count > max_stream_retries:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Generation timed out after multiple attempts. Please try a simpler request."
                        })
                        return
                    await asyncio.sleep(2)
                    continue
                    
                except Exception as stream_error:
                    error_msg = str(stream_error)
                    print(f"❌ Streaming failed (attempt {stream_retry_count + 1}): {error_msg[:200]}")
                    
                    # Check for rate limit
                    if "429" in error_msg or "quota" in error_msg.lower():
                        print("⚠️ Rate limit detected, waiting...")
                        await asyncio.sleep(5)
                    
                    stream_retry_count += 1
                    if stream_retry_count > max_stream_retries:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Streaming failed: {error_msg[:100]}"
                        })
                        return
                    await asyncio.sleep(2)
                    continue

            if not stream_success:
                await websocket.send_json({
                    "type": "error",
                    "message": "Failed to generate project. Please try a different prompt."
                })
                return













            # ========== JSON PARSING ==========
            try:
                clean_text = clean_json_response(full_response)

                try:
                    project_files: Dict[str, str] = json.loads(clean_text)
                    print(f"✅ JSON parsed successfully on attempt {retry_count + 1}")
                    
                    # ========== INSERT IMAGE WAITING CODE HERE ==========
                    # After AI generation completes successfully, WAIT for images
                    await websocket.send_json({
                        "type": "status",
                        "message": "⏳ Waiting for images to finish processing..."
                    })
                    
                    # Wait for background images to complete (with timeout)
                    try:
                        await asyncio.wait_for(background_image_task, timeout=15)
                        print(f"✅ Images ready: {len([k for k in image_data if image_data[k]])}/2")
                        await websocket.send_json({
                            "type": "status",
                            "message": f"✅ Images ready! Found {len([k for k in image_data if image_data[k]])}/2 images"
                        })
                    except asyncio.TimeoutError:
                        print("⚠️ Image search timeout, continuing with available images")
                        await websocket.send_json({
                            "type": "status",
                            "message": "⚠️ Image search timeout, using gradient cards for missing images"
                        })
                    except Exception as e:
                        print(f"⚠️ Image task error: {e}")
                    # ========== END OF IMAGE WAITING CODE ==========
                    
                    break  # Exit retry loop
                    
                except json.JSONDecodeError as e1:
                    # ... rest of your error handling


















                    print(f"⚠️ Initial parse failed: {e1}")
                    try:
                        fixed_text = fix_json_errors(clean_text)
                        project_files = json.loads(fixed_text)
                        print(f"✅ JSON fixed and parsed successfully on attempt {retry_count + 1}")
                        break
                    except json.JSONDecodeError as e2:
                        print(f"⚠️ Fixed parse still failed: {e2}")
                        try:
                            print("🛠️ Attempting advanced string repair...")
                            fixed_text2 = re.sub(r'"([^"]*?)(?=\s*[,}])', r'"\1"', clean_text)
                            fixed_text2 = fix_json_errors(fixed_text2)
                            project_files = json.loads(fixed_text2)
                            print(f"✅ JSON recovered using string repair!")
                            break


                        except Exception as repair_error:
                            print(f"❌ Repair failed: {repair_error}")
                            if retry_count == max_retries - 1:
                                print(f"❌ All {max_retries} attempts failed")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "Failed to parse the generated JSON. Gemini returned malformed output."
                                })
                                return
                            retry_count += 1
                            await asyncio.sleep(2 ** retry_count)
                            continue

            except Exception as parse_error:
                print(f"❌ Unexpected parsing error: {parse_error}")
                if retry_count == max_retries - 1:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to parse AI response: {str(parse_error)}"
                    })
                    return
                retry_count += 1
                await asyncio.sleep(2 ** retry_count)
                continue

        # ========== REPLACE NAME PLACEHOLDERS ==========
        for file_path, content in project_files.items():
            if isinstance(content, str):
                content = content.replace("{{PROJECT_NAME}}", project_name)
                content = content.replace("[CREATE_A_BRAND_NAME_BASED_ON_PROJECT_TYPE]", project_name)
                content = content.replace("[GENERATED_BRAND_NAME]", project_name)
                project_files[file_path] = content






















        # ========== PROCESS IMAGES INTO project_files ==========
        # Detect project type for placeholder sizing
        is_hotel = any(w in _pl for w in ['hotel', 'resort', 'lodge', 'inn', 'villa', 'retreat'])

        public_image_paths = {}

        if needs_images and image_data:
            for img_key, img_base64 in image_data.items():
                if not img_base64:
                    continue
                try:
                    raw_b64 = img_base64.split(',')[1] if img_base64.startswith('data:image') else img_base64
                    file_key = f"public/images/{img_key}.jpg"  # Changed from .webp to .jpg
                    project_files[file_key] = f"__binary_base64__{raw_b64}"
                    public_image_paths[img_key] = f"/images/{img_key}.jpg"  # Changed from .webp to .jpg
                    print(f"📦 Added to project files: {file_key}")
                except Exception as e:
                    print(f"⚠️ Failed to process {img_key}: {e}")
                    public_image_paths[img_key] = None
















        # Create placeholder images for any missing slots
        if not public_image_paths:
            print("📝 Creating placeholder images...")
            from PIL import Image as PilImage, ImageDraw
            from io import BytesIO as BytesIOLocal

            colors = ['#8b5cf6', '#ec4899', '#06b6d4', '#f59e0b', '#10b981']
            for i in range(1, 4):
                img_key = f"image_{i}"
                file_key = f"public/images/{img_key}.jpg"  # Changed from .webp to .jpg

                img = PilImage.new(
                    'RGB',  # Keep RGB for JPEG (no alpha channel)
                    (1920 if is_hotel else 800, 1080 if is_hotel else 600),
                    color=colors[(i - 1) % len(colors)]
                )
                draw = ImageDraw.Draw(img)
                text = f"Image {i}"
                try:
                    bbox = draw.textbbox((0, 0), text)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                except Exception:
                    tw, th = 100, 50
                draw.text(((img.width - tw) // 2, (img.height - th) // 2), text, fill='white')

                buf = BytesIOLocal()
                img.save(buf, format="JPEG", quality=85)  # Changed from WEBP to JPEG
                b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                project_files[file_key] = f"__binary_base64__{b64}"
                public_image_paths[img_key] = f"/images/{img_key}.jpg"  # Changed from .webp to .jpg
                print(f"📦 Added placeholder to project files: {file_key}")














        # ========== ADD HELPER FILES ==========
        project_files["image_data.json"] = json.dumps({
            "public_images": public_image_paths,
            "metadata": image_metadata,
        }, indent=2)

        if public_image_paths:
            gallery_items = []
            for key, path in public_image_paths.items():
                if path:
                    term = image_metadata.get(key, {}).get('term', f'Image {key.split("_")[-1]}')
                    gallery_items.append(f'{{ key: "{key}", path: "{path}", term: "{term}" }}')

            project_files["components/ImageGallery.tsx"] = f"""'use client';
const images = [{', '.join(gallery_items)}];
export default function ImageGallery() {{
  return (
    <div className="container mx-auto px-4 py-12">
      <h2 className="text-3xl font-bold text-center mb-8 gradient-text">Gallery</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {{images.map((img) => (
          <div key={{img.key}} className="group relative bg-zinc-900/50 rounded-xl overflow-hidden border border-white/10 hover:border-purple-500/50 transition-all duration-300">
            <div className="aspect-video overflow-hidden">
              <img src={{img.path}} alt={{img.term}} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
            </div>
            <div className="p-4">
              <h3 className="text-lg font-semibold mb-1">{{img.term}}</h3>
            </div>
          </div>
        ))}}
      </div>
    </div>
  );
}}
"""


        if is_hotel and public_image_paths:
             project_files["components/BackgroundImage.tsx"] = """'use client';
interface BackgroundImageProps {
  children: React.ReactNode;
  imageKey?: string;
  height?: string;
}
export default function BackgroundImage({ children, imageKey = 'image_1', height = 'min-h-screen' }: BackgroundImageProps) {
  return (
    <div className={`relative ${height} flex items-center justify-center overflow-hidden`}>
      <img src={`/images/${imageKey}.jpg`} alt="Background" className="absolute inset-0 w-full h-full object-cover" />
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/50 to-black/30" />
      <div className="relative z-10 w-full">{children}</div>
    </div>
  );
}
"""









        # ========== NO CLOUDINARY UPLOAD DURING GENERATION ==========
        # Images stay as binary for preview. Cloudinary upload happens only during deployment.
        # Just create empty image_urls dict
        image_urls = {}
        project_files["__image_urls__"] = image_urls






        
        # ========== SEND ORIGINAL FILES TO FRONTEND (KEEP ORIGINAL PATHS) ==========
        # The files sent to frontend keep original /public/images/ paths
        # Preview HTML uses base64 from binaries
        for file_path, content in project_files.items():
            if file_path.startswith("__"):
                continue  # Skip metadata
                
            # Send file generating status
            if file_path not in detected_files and file_path not in [
                "preview_html", "image_data.json",
                "components/ImageGallery.tsx", "components/BackgroundImage.tsx"
            ]:
                await websocket.send_json({"type": "file_generating", "file": file_path})
                await asyncio.sleep(0.03)

            # Prepare content for sending
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
            elif not isinstance(content, str):
                content = str(content)

            # Clean preview HTML
            if file_path == "preview_html":
                content = clean_html_response(content)

            # Check if binary
            is_binary = isinstance(content, str) and content.startswith("__binary_base64__")

            # Send to frontend
            await websocket.send_json({
                "type": "file_complete",
                "file": file_path,
                "content": content,
                "binary": is_binary,
            })
            await asyncio.sleep(0.08)









# ========== GENERATE AND SEND PREVIEW ==========
        await websocket.send_json({"type": "status", "message": "🎨 Generating preview..."})

        try:
                preview_result = await generate_preview_internal(project_files, user_prompt)
                if preview_result.get("success"):
                        preview_html = preview_result.get("preview_html")
                        original_size = len(preview_html)
                        
                        # ========== SAVE PREVIEW TO FILE ==========
                        # Use global PREVIEWS_DIR (defined at top)
                        previews_dir = PREVIEWS_DIR
                        previews_dir.mkdir(exist_ok=True)
                        
                        preview_filename = f"preview_{uuid.uuid4().hex[:8]}.html"
                        preview_path = previews_dir / preview_filename
                        
                        with open(preview_path, "w", encoding="utf-8") as f:
                                f.write(preview_html)
                        
                        print(f"💾 Preview saved to file: {preview_path}")
                        print(f"📦 Preview size: {original_size:,} chars")
                        
                        # Send preview HTML directly to frontend
                        await websocket.send_json({
                                "type": "preview",
                                "html": preview_html,
                                "preview_type": "ai_full"
                        })
                        
                        print(f"✅ Preview sent")
                        
                else:
                        print(f"⚠️ Preview generation failed: {preview_result.get('error')}")
                        
        except Exception as preview_error:
                print(f"⚠️ Preview error: {preview_error}")
                import traceback
                traceback.print_exc()
                
                
                
                
                # Send fallback preview
                fallback_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-white">
    <div class="container mx-auto px-4 py-20 text-center">
        <h1 class="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            {user_prompt or 'Project'}
        </h1>
        <p class="text-gray-400 mt-4">✨ Project generated successfully! Preview will appear shortly.</p>
        <button onclick="location.reload()" class="mt-8 px-6 py-3 bg-purple-600 rounded-lg hover:bg-purple-700">
            Refresh Preview
        </button>
    </div>
</body>
</html>"""
                
                await websocket.send_json({
                        "type": "preview",
                        "html": fallback_html,
                        "preview_type": "fallback"
                })

        # Send complete message
        await websocket.send_json({"type": "complete"})

    except Exception as e:
        print(f"❌ Build Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
























# ====================== INTELLIGENT AI-DRIVEN EDIT ======================
@app.post("/api/edit-file")
async def edit_file(request: Dict[str, Any]):
    try:
        edit_description: str = request.get("edit_description", "")
        all_files: Dict[str, str] = request.get("all_files", {})
        existing_preview: str = request.get("existing_preview", "")
        force_regenerate: bool = request.get("force_regenerate", True)  # Force regenerate preview
        
        print(f"\n{'='*70}")
        print(f"🔧 EDIT REQUEST RECEIVED")
        print(f"📝 Description: {edit_description}")
        print(f"📁 Available files: {len(all_files)} files")
        print(f"📄 Files: {list(all_files.keys())[:10]}")
        print(f"{'='*70}\n")

        if not edit_description:
            raise HTTPException(status_code=400, detail="Edit description is required")
        
        if not all_files:
            raise HTTPException(status_code=400, detail="No files provided")

        # Filter out preview_html from source files
        source_files = {k: v for k, v in all_files.items() if k != "preview_html"}
        
        # ========== SPECIAL HANDLING FOR NAVIGATION EDITS ==========
        is_navigation_edit = any(
            keyword in edit_description.lower() 
            for keyword in ['nav', 'navigation', 'menu', 'link', 'button', 'navbar', 'header']
        )
        
        # Also check if Navigation.tsx was modified
        navigation_file = source_files.get("components/Navigation.tsx", "")
        original_navigation = all_files.get("components/Navigation.tsx", "")
        
        navigation_changed = navigation_file != original_navigation if navigation_file else False
        
        print(f"🧭 Navigation edit detected: {is_navigation_edit or navigation_changed}")
        
        # Create a summary of source files for AI
        file_summary = []
        for file_path, content in list(source_files.items())[:15]:
            if isinstance(content, str):
                lines = content.split('\n')[:15]
                snippet = '\n'.join(lines)
            else:
                snippet = str(content)[:500]
            file_summary.append(f"File: {file_path}\nFirst lines:\n{snippet}\n")
        
        file_summary_text = "\n---\n".join(file_summary)
        
        # First, let AI analyze which source file(s) to edit
        analysis_prompt = f"""You are an AI code editor. Analyze this edit request and determine which SOURCE FILE(S) need to be modified.

EDIT REQUEST: {edit_description}

AVAILABLE SOURCE FILES (with snippets):
{file_summary_text}

Return ONLY a JSON object with:
{{
  "files_to_edit": ["file1.tsx", "file2.tsx"],
  "explanation": "brief explanation",
  "what_to_change": "what specific element to look for",
  "new_content": "what the new content should be"
}}"""

        print("🤖 Asking AI to analyze which source files to edit...")
        
        try:
            analysis_text = await model_router.generate_content(
                prompt=analysis_prompt,
                config={
                    "temperature": 0.1,
                    "response_mime_type": "application/json",
                }
            )
            
            analysis_text = analysis_text.strip()
            print(f"📊 AI Analysis: {analysis_text[:300]}...")
            
            analysis_text = clean_json_response(analysis_text)
            analysis = json.loads(analysis_text)
            
            # Handle case where analysis is a list instead of dict
            if isinstance(analysis, list):
                print(f"⚠️ AI returned a list, converting to dict")
                if len(analysis) > 0 and isinstance(analysis[0], dict):
                    analysis = analysis[0]
                else:
                    analysis = {
                        "files_to_edit": infer_files_from_request(edit_description, source_files),
                        "explanation": "AI returned list format, using fallback",
                        "what_to_change": "the content",
                        "new_content": edit_description
                    }
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            analysis = {
                "files_to_edit": infer_files_from_request(edit_description, source_files),
                "explanation": "Fallback file inference",
                "what_to_change": "the content",
                "new_content": edit_description
            }
        
        files_to_edit = analysis.get("files_to_edit", [])
        
        # If navigation edit, ensure Navigation.tsx is included
        if (is_navigation_edit or navigation_changed) and "components/Navigation.tsx" not in files_to_edit:
            files_to_edit.insert(0, "components/Navigation.tsx")
            print(f"📌 Adding Navigation.tsx to edit list")
        
        if not files_to_edit:
            files_to_edit = [f for f in source_files.keys() if any(x in f.lower() for x in ['page', 'layout', 'component'])][:2]
            
        if not files_to_edit:
            files_to_edit = list(source_files.keys())[:1]
            
        if not files_to_edit:
            raise HTTPException(status_code=400, detail="No source files available to edit")
        
        print(f"📂 Source files to edit: {files_to_edit}")
        print(f"💡 Explanation: {analysis.get('explanation', 'N/A')}")
        print(f"🎯 What to change: {analysis.get('what_to_change', 'N/A')}")

        # Now edit each identified source file
        edit_results = []
        
        for file_path in files_to_edit:
            current_content = source_files.get(file_path, "")
            if not current_content:
                print(f"⚠️ Source file not found: {file_path}")
                continue
            
            if not isinstance(current_content, str):
                current_content = json.dumps(current_content, indent=2) if isinstance(current_content, dict) else str(current_content)
                
            print(f"\n✏️ Editing source file: {file_path}")
            print(f"📄 Content length: {len(current_content)} chars")
            
            # Special handling for Navigation.tsx
            if file_path == "components/Navigation.tsx":
                edit_prompt = f"""You are editing a Next.js Navigation component.

FILE: {file_path}
EDIT REQUEST: {edit_description}

CURRENT CODE:
{current_content}

CRITICAL RULES FOR NAVIGATION:
1. Keep the SAME structure (flex justify-between items-center p-6 container mx-auto)
2. Keep the SAME icon (Dumbbell or similar based on project type)
3. Update ONLY the navigation links or brand name as requested
4. Maintain ALL Tailwind CSS classes
5. Preserve the responsive design (hidden md:flex)
6. Return ONLY the updated code

UPDATED CODE:"""
            else:
                edit_prompt = f"""You are making an EXACT, MINIMAL change to a SOURCE CODE file.

FILE: {file_path}
EDIT REQUEST: {edit_description}
WHAT TO CHANGE: {analysis.get('what_to_change', 'the specified content')}
NEW CONTENT SHOULD BE: {analysis.get('new_content', edit_description)}

ORIGINAL CODE:

{current_content}

CRITICAL RULES:
1. This is a SOURCE CODE file (.tsx, .jsx, .ts, .js) - NOT a preview HTML file
2. Find the EXACT element or text mentioned in the request
3. Modify ONLY that specific content
4. Keep ALL existing code structure, imports, components, and functionality intact
5. Preserve ALL formatting, indentation, and line breaks

UPDATED CODE:"""

            try:
                response_text = await model_router.generate_content(
                    prompt=edit_prompt,
                    config={
                        "temperature": 0.01,
                        "max_output_tokens": 10192,
                    }
                )

                updated_content = response_text.strip()
                
                if updated_content.startswith("```"):
                    lines = updated_content.split('\n')
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    updated_content = '\n'.join(lines)
                
                updated_content = updated_content.strip()
                
                if updated_content == current_content:
                    print(f"⚠️ No changes detected for {file_path}")
                    continue

                edit_results.append({
                    "file_path": file_path,
                    "original_content": current_content,
                    "updated_content": updated_content,
                    "success": True
                })
                
                print(f"✅ Successfully edited {file_path}")
                
            except Exception as e:
                print(f"❌ Error editing {file_path}: {e}")
                import traceback
                traceback.print_exc()
                continue

        if not edit_results:
            return {
                "success": False,
                "error": "No changes were made to source files. Please be more specific about what to change.",
                "analysis": analysis,
                "hint": "Try being more specific, e.g., 'Change the navigation link Home to Dashboard'"
            }

        # Apply all edits to source files
        updated_files = {**all_files}
        for result in edit_results:
            updated_files[result["file_path"]] = result["updated_content"]

        # ========== FORCE REGENERATE PREVIEW ==========
        preview_html = existing_preview
        
        # ALWAYS regenerate preview when navigation changes
        should_regenerate = force_regenerate or is_navigation_edit or navigation_changed or len(edit_results) > 0
        
        if should_regenerate:
            print(f"🔄 Regenerating preview (navigation edit: {is_navigation_edit or navigation_changed})")
            
            try:
                # Get project name from files or generate one
                project_name = "Scorpio Project"
                for file_path, content in updated_files.items():
                    if "Navigation.tsx" in file_path and isinstance(content, str):
                        # Try to extract brand name
                        brand_match = re.search(r'<Link[^>]*>([^<]+)</Link>', content)
                        if brand_match:
                            project_name = brand_match.group(1).strip()
                        break
                
                # Regenerate preview with updated files
                preview_result = await generate_preview_internal(updated_files, project_name)
                
                if preview_result.get("success"):
                    preview_html = preview_result.get("preview_html")
                    print(f"✅ Preview regenerated successfully! Length: {len(preview_html)} chars")
                else:
                    print(f"⚠️ Preview regeneration failed: {preview_result.get('error')}")
                    
            except Exception as e:
                print(f"⚠️ Preview regeneration error: {e}")
                import traceback
                traceback.print_exc()

        print(f"\n{'='*70}")
        print(f"✅ EDIT COMPLETE: {len(edit_results)} source file(s) modified")
        for result in edit_results:
            print(f"   - {result['file_path']}")
        print(f"   Preview updated: {preview_html != existing_preview}")
        print(f"{'='*70}\n")

        return {
            "success": True,
            "edits": edit_results,
            "files_edited": [r["file_path"] for r in edit_results],
            "preview_html": preview_html,
            "analysis": analysis,
            "preview_regenerated": should_regenerate
        }

    except Exception as e:
        print(f"❌ Edit Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
































def generate_file_snippets_for_preview(files: Dict[str, str], max_files: int = 5) -> str:
    """Generate useful snippets of source files for preview generation"""
    snippets = []
    count = 0
    
    for file_path, content in files.items():
        if file_path == "preview_html":
            continue
        if count >= max_files:
            break
            
        # Extract key information from the file
        lines = content.split('\n')
        
        # Look for important elements
        title_match = None
        button_matches = []
        heading_matches = []
        
        for i, line in enumerate(lines[:50]):  # Only check first 50 lines
            if '<title>' in line or '<h1>' in line:
                title_match = line.strip()
            if '<button' in line:
                button_matches.append(line.strip())
            if '<h' in line and len(line) < 200:
                heading_matches.append(line.strip())
        
        snippet = f"File: {file_path}\n"
        if title_match:
            snippet += f"Title/Heading: {title_match}\n"
        if heading_matches:
            snippet += f"Headings: {', '.join(heading_matches[:3])}\n"
        if button_matches:
            snippet += f"Buttons: {', '.join(button_matches[:3])}\n"
        
        # Add first few lines as context
        snippet += f"First lines:\n" + '\n'.join(lines[:10]) + "\n"
        
        snippets.append(snippet)
        count += 1
    
    return '\n---\n'.join(snippets)





def infer_files_from_request(edit_description: str, files: Dict[str, str]) -> List[str]:
    """Infer which source files to edit based on request keywords"""
    edit_lower = edit_description.lower()
    likely_files = []
    
    # Priority patterns for Next.js 14 files
    priority_patterns = {
        'title': [
            'app/page.tsx', 'app/(marketing)/page.tsx', 'app/layout.tsx',
            'components/Navigation.tsx', 'components/Header.tsx'
        ],
        'header': ['components/Navigation.tsx', 'app/layout.tsx', 'components/Header.tsx'],
        'button': ['.tsx', '.jsx'],
        'style': ['app/globals.css', 'globals.css'],
        'color': ['app/globals.css', 'globals.css', 'tailwind.config.ts'],
        'layout': ['app/layout.tsx', 'app/(marketing)/layout.tsx', 'app/(shop)/layout.tsx'],
        'page': ['app/page.tsx', 'app/(marketing)/page.tsx', 'page.tsx'],
        'nav': ['components/Navigation.tsx', 'components/Header.tsx'],
        'footer': ['components/Footer.tsx'],
        'background': ['app/globals.css', 'globals.css'],
        'loading': ['app/loading.tsx', 'loading.tsx'],
        'error': ['app/error.tsx', 'error.tsx'],
        'text': ['.tsx', '.jsx'],
    }
    
    # Check for keywords
    for keyword, patterns in priority_patterns.items():
        if keyword in edit_lower:
            for pattern in patterns:
                if pattern.startswith('.'):
                    matches = [f for f in files.keys() if f.endswith(pattern)]
                elif '(' in pattern or ')' in pattern:
                    # Route group patterns
                    matches = [f for f in files.keys() if pattern.split('/')[-1] in f]
                else:
                    matches = [f for f in files.keys() if pattern in f]
                likely_files.extend(matches)
    
    # If no matches, look for main page files
    if not likely_files:
        main_patterns = ['page.tsx', 'layout.tsx', 'loading.tsx', 'error.tsx']
        for pattern in main_patterns:
            matches = [f for f in files.keys() if pattern in f.lower()]
            likely_files.extend(matches)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in likely_files:
        if f not in seen and f != "preview_html":
            seen.add(f)
            unique_files.append(f)
    
    return unique_files[:3]  # Allow up to 3 files for route groups









async def regenerate_preview_for_edit(data: Dict[str, Any]):
    """Regenerate preview HTML for edited files"""
    try:
        files = data.get("files", {})
        modified_files = data.get("modified_files", [])
        edit_description = data.get("edit_description", "")

        # Get snippets of modified files
        modified_snippets = []
        for file_path in modified_files[:3]:  # Limit to 3 files
            content = files.get(file_path, "")
            if content:
                lines = content.split('\n')[:30]
                snippet = '\n'.join(lines)
                modified_snippets.append(f"\n=== {file_path} ===\n{snippet}")

        prompt = f"""Update the HTML preview to reflect these specific changes.

CHANGE MADE: {edit_description}
FILES MODIFIED: {', '.join(modified_files)}

Modified content snippets:
{''.join(modified_snippets)}

CRITICAL:
- Update ONLY what's needed to reflect the changes described
- Keep the overall design, layout, and all other elements exactly the same
- If the change was to text, only update that text in the preview
- If the change was to add a button or element, ONLY add that element
- Do NOT redesign or restructure anything
- Return ONLY the raw HTML code starting with <!DOCTYPE html>

Updated HTML preview:"""

        response_text = await model_router.generate_content(
            prompt=prompt,
            config={
                "temperature": 0.1,
                "max_output_tokens": 8192,
            }
        )

        preview_html = response_text.strip()

        preview_html = clean_html_response(preview_html)
        
        # Ensure proper start
        if preview_html.lower().startswith("html"):
            doctype_index = preview_html.lower().find("<!doctype")
            if doctype_index != -1:
                preview_html = preview_html[doctype_index:]
        
        return {"success": True, "preview_html": preview_html}

    except Exception as e:
        print(f"❌ Preview regeneration error: {e}")
        return {"success": False, "error": str(e)}


# ====================== BATCH EDIT ======================
@app.post("/api/edit-batch")
async def edit_batch(request: Dict[str, Any]):
    try:
        edits: List[Dict] = request.get("edits", [])
        if not edits:
            raise HTTPException(status_code=400, detail="No edits provided")

        async def process(edit: Dict):
            try:
                return await edit_file(edit)
            except Exception as e:
                return {
                    "success": False,
                    "file_path": edit.get("file_path"),
                    "error": str(e)
                }

        results = await asyncio.gather(*[process(edit) for edit in edits])

        return {
            "success": True,
            "total": len(edits),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





















@app.post("/api/update-preview")
async def update_preview(request: Dict[str, Any]):
    """Quickly update preview without full regeneration"""
    try:
        files: Dict = request.get("files", {})
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        preview_content = request.get("preview_content", "")
        
        if preview_content:
            updated_preview = clean_html_response(preview_content)
        else:
            prompt = f"""Generate a clean HTML preview for this project.

Files: {list(files.keys())[:10]}

Create a functional preview with Tailwind CSS. Include navigation if multiple pages.
Return ONLY the raw HTML code starting with <!DOCTYPE html>:"""

            response_text = await model_router.generate_content(
                prompt=prompt,
                config={"temperature": 0.2, "max_output_tokens": 8192}
            )
            updated_preview = clean_html_response(response_text.strip())  # ✅ Define updated_preview here

        return {
            "success": True,
            "preview_html": updated_preview  # ✅ Now updated_preview exists
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ====================== UTILITY ENDPOINTS ======================
@app.post("/api/search-content")
async def search_content(request: Dict[str, Any]):
    try:
        files: Dict = request.get("files", {})
        search_text: str = request.get("search_text", "")

        if not files or not search_text:
            raise HTTPException(status_code=400, detail="Missing files or search text")

        results = []
        search_lower = search_text.lower()

        for file_path, content in files.items():
            if isinstance(content, str) and search_lower in content.lower():
                lines = content.splitlines()
                matches = []
                for i, line in enumerate(lines):
                    if search_lower in line.lower():
                        matches.append({
                            "line_number": i + 1,
                            "line": line.strip(),
                            "context": "\n".join(lines[max(0, i-2):min(len(lines), i+3)])
                        })
                if matches:
                    results.append({
                        "file": file_path,
                        "matches": matches,
                        "match_count": len(matches)
                    })

        return {
            "success": True,
            "search_text": search_text,
            "total_matches": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
















@app.post("/api/regenerate-preview")
async def regenerate_preview(request: Dict[str, Any]):
    try:
        files: Dict = request.get("files", {})
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        prompt = f"""Generate a beautiful standalone HTML preview for this Next.js project.
Use Tailwind via CDN and Inter font from Google.
Make it visually rich, interactive, and faithful to the project.
Return ONLY the raw HTML code starting with <!DOCTYPE html>:

Files: {list(files.keys())[:15]}"""

        response_text = await model_router.generate_content(
            prompt=prompt,
            config={"temperature": 0.3, "max_output_tokens": 8192}
        )

        preview_html = clean_html_response(response_text.strip())

        return {"success": True, "preview_html": preview_html}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))












@app.post("/api/search-images")
async def search_images(request: Dict[str, Any]):
    try:
        query = request.get("query", "")
        count = request.get("count", 3)

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        results = await search_free_images(query, count)

        # Convert URLs to base64 for immediate use
        processed_results = []
        for result in results:
            try:
                base64_img = await get_image_as_base64(result["url"])
                if base64_img:
                    processed_results.append({
                        **result,
                        "base64": base64_img,
                        "preview": f"data:image/jpeg;base64,{base64_img[:100]}..."  # Just a preview
                    })
                else:
                    processed_results.append({
                        **result,
                        "base64": generate_placeholder_image(400, 300, query),
                        "preview": generate_placeholder_image(100, 75, "img")
                    })
            except Exception as e:
                print(f"Error processing image {result['url']}: {e}")
                processed_results.append({
                    **result,
                    "base64": generate_placeholder_image(400, 300, query),
                    "preview": generate_placeholder_image(100, 75, "img")
                })

        return {
            "success": True,
            "query": query,
            "count": len(processed_results),
            "results": processed_results
        }

    except Exception as e:
        print(f"❌ Image search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))










@app.post("/api/deploy")
async def deploy_project(request: Dict[str, Any]):
    """
    Package the project as a ZIP file for deployment
    """
    try:
        files: Dict[str, str] = request.get("files", {})
        project_name: str = request.get("project_name", "my-app")
        
        if not files:
            raise HTTPException(status_code=400, detail="No files to deploy")
        
        print(f"🚀 Packaging project: {project_name}")
        print(f"📁 Files to package: {len(files)} files")
        
        # Create a temporary directory for the project
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.join(tmpdir, project_name)
            os.makedirs(project_dir)
            




            # Write all files to the temporary directory
            for file_path, content in files.items():
                if file_path == "preview_html":
                    continue
                full_path = os.path.join(project_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Convert content to string if it's a dict
                if isinstance(content, dict):
                    content = json.dumps(content, indent=2)
                elif not isinstance(content, str):
                    content = str(content)
                
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
            






            
            print(f"✅ Files written to {project_dir}")
            
            # Create a zip file of the project
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files_in_dir in os.walk(project_dir):
                    for file in files_in_dir:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, project_dir)
                        zip_file.write(file_path, arcname)
            
            zip_buffer.seek(0)
            
            # Encode zip as base64 for response
            zip_base64 = base64.b64encode(zip_buffer.getvalue()).decode('utf-8')
            
            return {
                "success": True,
                "message": "Project packaged successfully",
                "zip_data": zip_base64,
                "project_name": project_name,
                "file_count": len(files)
            }
            
    except Exception as e:
        print(f"❌ Deploy error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))











@app.post("/api/deploy-advanced")
async def deploy_advanced(request: Dict[str, Any]):
    """
    Advanced deployment with database and environment configuration
    """
    try:
        files = request.get("files", {})
        raw_project_name = request.get("projectName", "scorpio-project")
        options = request.get("options", {})
        
        if not files:
            raise HTTPException(status_code=400, detail="No files to deploy")
        
        # ========== SANITIZE PROJECT NAME ==========
        import re
        project_name = re.sub(r'[^a-z0-9-]', '-', raw_project_name.lower())
        project_name = re.sub(r'-+', '-', project_name)  # Replace multiple hyphens with single
        project_name = project_name.strip('-')
        if len(project_name) > 100:
            project_name = project_name[:100].rstrip('-')
        if not project_name:
            project_name = "scorpio-project"
        
        print(f"📝 Original project name: {raw_project_name}")
        print(f"📝 Sanitized project name: {project_name}")
        print(f"🚀 Advanced deployment for: {project_name}")
        print(f"📦 Options: {options}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.join(tmpdir, project_name)
            os.makedirs(project_dir)
            
            # Write all files
            for file_path, content in files.items():
                if file_path == "preview_html":
                    continue
                full_path = os.path.join(project_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Handle binary images (convert to real files)
                if isinstance(content, dict) and content.get('__type') == 'binary_image':
                    data = content.get('data')
                    if data:
                        if isinstance(data, dict):
                            # Convert Uint8Array dict to bytes
                            byte_list = []
                            for i in range(len(data)):
                                if str(i) in data:
                                    byte_list.append(data[str(i)])
                            binary_data = bytes(byte_list)
                        elif isinstance(data, (bytes, bytearray)):
                            binary_data = bytes(data)
                        else:
                            binary_data = None
                        
                        if binary_data:
                            with open(full_path, "wb") as f:
                                f.write(binary_data)
                            print(f"  🖼️ Wrote image: {file_path} ({len(binary_data)} bytes)")
                            continue
                
                # Handle regular text files
                if isinstance(content, dict):
                    content = json.dumps(content, indent=2)
                elif not isinstance(content, str):
                    content = str(content)
                
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
            
            # Add database configuration if selected
            if options.get("database") != "none":
                db_type = options.get("database")
                env_vars = options.get("envVars", {})
                
                # Add database connection strings to .env
                env_content = ""
                for key, value in env_vars.items():
                    env_content += f"{key}={value}\n"
                
                with open(os.path.join(project_dir, ".env.example"), "w") as f:
                    f.write(env_content)
                
                # Add database setup instructions
                with open(os.path.join(project_dir, "DATABASE_SETUP.md"), "w") as f:
                    f.write(f"# Database Setup for {db_type}\n\n")
                    f.write("Environment variables needed:\n")
                    for key in env_vars.keys():
                        f.write(f"- {key}\n")
            
            # Create platform-specific configuration
            platform = options.get("platform", "vercel")
            if platform == "vercel":
                vercel_config = {
                    "version": 2,
                    "builds": [{"src": "package.json", "use": "@vercel/next"}],
                    "env": options.get("envVars", {})
                }
                with open(os.path.join(project_dir, "vercel.json"), "w") as f:
                    json.dump(vercel_config, f, indent=2)
            
            # Create README with deployment instructions
            readme_content = f"""# {project_name}

## Deploy to {platform.capitalize()}

### Quick Deploy:
1. Go to https://vercel.com/new
2. Drag and drop this folder
3. Click Deploy

### Files included:
- Complete Next.js 14 project
- {len([f for f in files.keys() if 'public/images/' in f])} images included
- Ready for production

### Environment Variables (if needed):
Check the `.env.example` file for required variables.
"""
            with open(os.path.join(project_dir, "README.md"), "w") as f:
                f.write(readme_content)
            
            # Create zip package
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files_in_dir in os.walk(project_dir):
                    for file in files_in_dir:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, project_dir)
                        zip_file.write(file_path, arcname)
            
            zip_buffer.seek(0)
            zip_base64 = base64.b64encode(zip_buffer.getvalue()).decode('utf-8')
            
            return {
                "success": True,
                "message": f"Project packaged for {platform} deployment",
                "zip_data": zip_base64,
                "project_name": project_name,
                "url": f"https://{project_name}.{platform}.app"
            }
            
    except Exception as e:
        print(f"❌ Advanced deploy error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))








@app.post("/api/deploy-vercel")
async def deploy_to_vercel(request: Dict[str, Any]):
    """Deploy to Vercel - Upload images first, then replace paths, then deploy"""
    try:
        files = request.get("files", {})
        raw_project_name = request.get("projectName", "scorpio-project")
        vercel_token = request.get("vercel_token", "")
        env_vars = request.get("envVars", {})
        
        # ========== SANITIZE PROJECT NAME FOR VERCEL ==========
        import re
        # Convert to lowercase and replace invalid characters with hyphens
        project_name = re.sub(r'[^a-z0-9-]', '-', raw_project_name.lower())
        # Replace multiple hyphens with single hyphen
        project_name = re.sub(r'-+', '-', project_name)
        # Remove leading/trailing hyphens
        project_name = project_name.strip('-')
        # Limit to 100 characters
        if len(project_name) > 100:
            project_name = project_name[:100].rstrip('-')
        # Ensure it's not empty
        if not project_name:
            project_name = "scorpio-project"
        
        print(f"📝 Original project name: {raw_project_name}")
        print(f"📝 Sanitized for Vercel: {project_name}")
        
        













        # 👇 ADD DEBUG CODE RIGHT HERE 👇
        print("\n📁 FILES IN PROJECT:")
        for file_path, content in files.items():
            if file_path.startswith("public/images/"):
                print(f"  {file_path}: {type(content)}")
                if isinstance(content, str):
                    print(f"    Preview: {content[:100]}...")





        
        
        if not vercel_token:
            raise HTTPException(status_code=400, detail="Vercel token required")
        
        print(f"\n{'='*70}")
        print(f"🚀 DEPLOYING TO VERCEL: {project_name}")
        print(f"{'='*70}\n")
        













        # ========== STEP 1: UPLOAD ALL IMAGES TO CLOUDINARY ==========
        print("📸 STEP 1: Uploading images to Cloudinary...")
        print("-" * 40)
        
        image_urls = {}
        image_count = 0
        
        for file_path, content in files.items():
            # Skip non-image files
            if not file_path.startswith("public/images/"):
                continue
            
            is_binary_image = False
            base64_data = None
            binary_bytes = None
            
            # Case 1: String with __binary_base64__ prefix
            if isinstance(content, str) and content.startswith("__binary_base64__"):
                is_binary_image = True
                base64_data = content.replace("__binary_base64__", "")
                print(f"  📸 Found base64 string: {file_path}")
            
            # Case 2: Dict with binary image data (from your frontend)
            elif isinstance(content, dict):
                print(f"  📸 Found image dict: {file_path}")
                print(f"     Keys: {list(content.keys())}")
                
                # Check for 'data' key containing Uint8Array or bytes
                if 'data' in content:
                    data = content['data']
                    
                    # Handle Uint8Array (comes as dict with '0', '1', '2'... keys or actual bytes)
                    if isinstance(data, dict):
                        # Convert dict of numbered keys to bytes
                        print(f"     Converting Uint8Array dict to bytes...")
                        byte_list = []
                        for i in range(len(data)):
                            if str(i) in data:
                                byte_list.append(data[str(i)])
                        binary_bytes = bytes(byte_list)
                        is_binary_image = True
                        print(f"     Converted Uint8Array to {len(binary_bytes)} bytes")
                    
                    elif isinstance(data, (bytes, bytearray)):
                        binary_bytes = bytes(data)
                        is_binary_image = True
                        print(f"     Found bytes data: {len(binary_bytes)} bytes")
                    
                    elif isinstance(data, str):
                        # Check if it's base64
                        if data.startswith('data:image'):
                            base64_data = data.split(',')[1] if ',' in data else data
                        else:
                            base64_data = data
                        is_binary_image = True
                        print(f"     Found string data: {len(base64_data)} chars")
                
                # Alternative: check for 'base64' key
                elif 'base64' in content:
                    base64_data = content['base64']
                    is_binary_image = True
                    print(f"     Found base64 data: {len(base64_data)} chars")
                
                # Convert binary_bytes to base64 for Cloudinary upload
                if binary_bytes and not base64_data:
                    import base64 as b64
                    base64_data = b64.b64encode(binary_bytes).decode('utf-8')
                    print(f"     Converted {len(binary_bytes)} bytes to base64")
            
            if is_binary_image and base64_data:
                try:
                    print(f"  ☁️ Uploading to Cloudinary: {file_path}")
                    
                    upload_result = cloudinary.uploader.upload(
                        f"data:image/jpeg;base64,{base64_data}",
                        folder="scorpio_projects",
                        public_id=file_path.replace('/', '_').replace('.', '_'),
                        overwrite=True
                    )
                    
                    image_urls[file_path] = upload_result['secure_url']
                    print(f"  ✅ Uploaded successfully!")
                    print(f"     URL: {upload_result['secure_url'][:80]}...")
                    image_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Failed to upload {file_path}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                if file_path.startswith("public/images/"):
                    print(f"  ⚠️ No valid image data for {file_path}")
        
        print(f"\n✅ STEP 1 COMPLETE: Uploaded {image_count} images to Cloudinary\n")
        
        # Log all uploaded URLs
        if image_urls:
            print("📋 CLOUDINARY URLS:")
            for local_path, url in image_urls.items():
                public_path = "/" + local_path.replace("public/", "")
                print(f"  {public_path} -> {url}")
        print()
        
        # ========== STEP 2: REPLACE IMAGE PATHS IN ALL FILES ==========
        print("🔄 STEP 2: Replacing image paths with Cloudinary URLs...")
        print("-" * 40)
        
        deployment_files = {}
        
        # Create path mapping
        path_to_url = {}
        for local_path, cloudinary_url in image_urls.items():
            public_path = "/" + local_path.replace("public/", "")
            path_to_url[public_path] = cloudinary_url
            print(f"  📋 Mapping: {public_path}")
        
        for file_path, content in files.items():
            # Skip preview_html and metadata
            if file_path == "preview_html" or file_path == "__image_urls__":
                continue
            
            # Skip binary images (already uploaded, don't include in deployment)
            if isinstance(content, dict) and content.get('__type') == 'binary_image':
                continue
            
            if isinstance(content, str) and content.startswith("__binary_base64__"):
                continue
            
            # For text files, replace image paths
            if isinstance(content, str):
                updated_content = content
                replaced = False
                
                for old_path, new_url in path_to_url.items():
                    if old_path in updated_content:
                        updated_content = updated_content.replace(old_path, new_url)
                        replaced = True
                        print(f"  🔄 {file_path}: '{old_path}' -> replaced")
                
                # Also check for src pattern
                for old_path, new_url in path_to_url.items():
                    pattern = f'src="{old_path}"'
                    if pattern in updated_content:
                        updated_content = updated_content.replace(pattern, f'src="{new_url}"')
                        replaced = True
                
                deployment_files[file_path] = updated_content
                if replaced:
                    print(f"  ✅ {file_path} updated with Cloudinary URLs")
            else:
                deployment_files[file_path] = content
        
        print(f"\n✅ STEP 2 COMPLETE: Replaced paths in {len(deployment_files)} files\n")
        
        # ========== STEP 3: DEPLOY TO VERCEL ==========
        print("🚀 STEP 3: Deploying to Vercel...")
        print("-" * 40)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.join(tmpdir, project_name)
            os.makedirs(project_dir)
            
            # Write deployment files
            file_count = 0
            for file_path, content in deployment_files.items():
                full_path = os.path.join(project_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                if isinstance(content, dict):
                    content = json.dumps(content, indent=2)
                elif not isinstance(content, str):
                    content = str(content)
                
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                file_count += 1
            
            print(f"  📁 Wrote {file_count} files to temp directory")
            
            # Build file list for Vercel
            file_list = []
            total_size = 0
            for root, dirs, files_in_dir in os.walk(project_dir):
                for file in files_in_dir:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_dir).replace('\\', '/')
                    
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                    
                    file_list.append({
                        "file": arcname,
                        "data": base64.b64encode(file_content).decode('utf-8'),
                        "encoding": "base64"
                    })
                    total_size += len(file_content)
            
            print(f"  📦 Total size: {total_size / 1024 / 1024:.2f} MB")
            
            if total_size > 9 * 1024 * 1024:
                return {
                    "success": False,
                    "message": f"Project too large ({total_size / 1024 / 1024:.2f} MB)",
                    "manual_deploy": True
                }
            
            # Deploy to Vercel
            async with httpx.AsyncClient(timeout=300.0) as client:
                print("  📡 Sending to Vercel API...")
                deploy_response = await client.post(
                    "https://api.vercel.com/v13/deployments",
                    headers={
                        "Authorization": f"Bearer {vercel_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "name": project_name,
                        "files": file_list,
                        "projectSettings": {
                            "framework": "nextjs",
                            "buildCommand": "npm run build",
                            "outputDirectory": ".next",
                            "installCommand": "npm install"
                        },
                        "env": env_vars
                    }
                )
                
                if deploy_response.status_code not in [200, 201]:
                    error_data = deploy_response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    raise Exception(f"Vercel API error: {error_msg}")
                
                deploy_data = deploy_response.json()
                deployment_url = deploy_data.get("url")
                
                print(f"\n{'='*70}")
                print(f"✅ DEPLOYMENT SUCCESSFUL!")
                print(f"🔗 URL: https://{deployment_url}")
                print(f"{'='*70}\n")
                
                return {
                    "success": True,
                    "message": "Deployed to Vercel successfully!",
                    "deployment_url": f"https://{deployment_url}",
                    "deployment_id": deploy_data.get("id"),
                    "project_name": project_name,
                    "images_uploaded": image_count
                }
                
    except Exception as e:
        print(f"❌ Deploy error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))







@app.post("/api/generate-static-preview")
async def generate_static_preview(request: Dict[str, Any]):
    """
    Generate static HTML preview by building and exporting the Next.js project,it should navigate to different pages and interact with components,ensuring the preview is fully functional and visually accurate, not just a screenshot. This is more resource-intensive but provides a true representation of the project.
    """
    try:
        files = request.get("files", {})
        project_name = request.get("projectName", "scorpio-project")
        
        if not files:
            raise HTTPException(status_code=400, detail="No files to preview")
        
        print(f"🚀 Generating static preview for: {project_name}")
        print(f"📁 Files to process: {len(files)}")
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.join(tmpdir, project_name)
            os.makedirs(project_dir)
            
            # Write all files to the temporary directory
            for file_path, content in files.items():
                if file_path == "preview_html":
                    continue
                full_path = os.path.join(project_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Convert content to string if it's a dict
                if isinstance(content, dict):
                    content = json.dumps(content, indent=2)
                elif not isinstance(content, str):
                    content = str(content)
                
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
            
            print(f"✅ Files written to {project_dir}")
            
            # Ensure package.json exists with correct scripts
            package_json_path = os.path.join(project_dir, "package.json")
            if os.path.exists(package_json_path):
                with open(package_json_path, 'r') as f:
                    package_json = json.load(f)
            else:
                package_json = {}
            
            # Ensure required scripts for build and export
            if "scripts" not in package_json:
                package_json["scripts"] = {}
            
            # Add export script if not present
            if "export" not in package_json["scripts"]:
                package_json["scripts"]["export"] = "next export"
            
            # Ensure build script exists
            if "build" not in package_json["scripts"]:
                package_json["scripts"]["build"] = "next build"
            
            # Ensure Next.js is in dependencies
            if "dependencies" not in package_json:
                package_json["dependencies"] = {}
            if "next" not in package_json["dependencies"]:
                package_json["dependencies"]["next"] = "14.2.35"
            if "react" not in package_json["dependencies"]:
                package_json["dependencies"]["react"] = "^18.2.0"
            if "react-dom" not in package_json["dependencies"]:
                package_json["dependencies"]["react-dom"] = "^18.2.0"
            
            with open(package_json_path, 'w') as f:
                json.dump(package_json, f, indent=2)
            
            # Install dependencies
            print("📦 Installing dependencies...")
            install_process = await asyncio.create_subprocess_exec(
                "npm", "install", "--no-fund", "--no-audit",
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await install_process.wait()
            
            if install_process.returncode != 0:
                print("⚠️ npm install had warnings, continuing...")
            
            # Build the project
            print("🔨 Building project...")
            build_process = await asyncio.create_subprocess_exec(
                "npm", "run", "build",
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await build_process.wait()
            
            if build_process.returncode != 0:
                stderr = await build_process.stderr.read()
                print(f"❌ Build failed: {stderr.decode()}")
                raise Exception("Next.js build failed")
            
            # Export to static HTML
            print("📤 Exporting static HTML...")
            export_process = await asyncio.create_subprocess_exec(
                "npm", "run", "export",
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await export_process.wait()
            
            if export_process.returncode != 0:
                stderr = await export_process.stderr.read()
                print(f"⚠️ Export warning: {stderr.decode()}")
                # Try alternative export method
                export_process2 = await asyncio.create_subprocess_exec(
                    "npx", "next", "export",
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await export_process2.wait()
            
            # Read the generated index.html
            out_dir = os.path.join(project_dir, "out")
            index_path = os.path.join(out_dir, "index.html")
            
            if not os.path.exists(index_path):
                # Try looking for other HTML files
                for root, dirs, files in os.walk(out_dir):
                    for file in files:
                        if file.endswith('.html'):
                            index_path = os.path.join(root, file)
                            break
                    if index_path:
                        break
            
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    preview_html = f.read()
                
                # Also collect all static assets
                static_files = {}
                for root, dirs, files in os.walk(out_dir):
                    for file in files:
                        if file.endswith(('.html', '.css', '.js', '.json')):
                            rel_path = os.path.relpath(os.path.join(root, file), out_dir)
                            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                                static_files[rel_path] = f.read()
                
                print(f"✅ Static preview generated successfully")
                print(f"📄 Preview HTML size: {len(preview_html)} chars")
                
                return {
                    "success": True,
                    "preview_html": preview_html,
                    "static_files": static_files,
                    "message": "Static preview generated successfully"
                }
            else:
                raise Exception("No HTML file found in out directory")
            
    except Exception as e:
        print(f"❌ Static preview error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

















@app.post("/api/generate-preview")
async def generate_preview(request: Dict[str, Any]):
    """
    Dynamic Interactive Preview - Fast, fully functional with working buttons and navigation.
    Supports Next.js 14 App Router features: route groups, private folders, nested layouts
    """
    try:
        files: Dict[str, Any] = request.get("files", {})
        project_name: str = request.get("projectName", "Scorpio Project")

        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        print(f"🚀 Generating dynamic interactive preview for: {project_name}")

        # ========== DETECT NEXT.JS 14 STRUCTURE ==========
        # Detect route groups (folders in parentheses)
        route_groups = []
        private_folders = []
        dynamic_routes = []
        
        for file_path in files.keys():
            # Detect route groups: app/(group)/...
            if '/(' in file_path and ')/' in file_path:
                group_match = re.search(r'app/\(([^)]+)\)/', file_path)
                if group_match and group_match.group(1) not in route_groups:
                    route_groups.append(group_match.group(1))
            
            # Detect private folders: _components, _lib, etc.
            if '/_' in file_path:
                private_match = re.search(r'/(_[^/]+)/', file_path)
                if private_match and private_match.group(1) not in private_folders:
                    private_folders.append(private_match.group(1))
            
            # Detect dynamic routes: [param] or [...param]
            if '/[' in file_path and ']/' in file_path:
                dynamic_routes.append(file_path)
        
        print(f"📁 Detected route groups: {route_groups}")
        print(f"🔒 Detected private folders: {private_folders}")
        print(f"🔄 Detected dynamic routes: {len(dynamic_routes)}")

        # ========== EXTRACT NAVIGATION LINKS ==========
        nav_links = []
        
        # Method 1: Extract from Navigation.tsx if exists
        nav_content = files.get("components/Navigation.tsx", "")
        if not nav_content:
            # Also check for Navigation in other locations
            for file_path in files.keys():
                if 'Navigation' in file_path and file_path.endswith('.tsx'):
                    nav_content = files.get(file_path, "")
                    if nav_content:
                        print(f"📍 Found navigation at: {file_path}")
                        break
        
        if nav_content:
            # Look for href patterns in the navigation component
            href_pattern = r'href:\s*["\']([^"\']+)["\']'
            label_pattern = r'label:\s*["\']([^"\']+)["\']'
            
            matches = re.findall(href_pattern, nav_content)
            labels = re.findall(label_pattern, nav_content)
            
            # Create pairs if we have both
            if matches and labels:
                nav_links = list(zip(matches, labels))
            elif matches:
                # If only hrefs found, create labels from hrefs
                nav_links = [(path, path.strip('/').capitalize() or 'Home') for path in matches]
        
        # Method 2: Detect from route groups
        if not nav_links and route_groups:
            print(f"📍 Building navigation from route groups: {route_groups}")
            for group in route_groups:
                if group == 'marketing':
                    nav_links.append(('/', 'Home'))
                elif group == 'shop':
                    # Look for shop pages
                    has_products = any('products' in f for f in files.keys())
                    has_cart = any('cart' in f for f in files.keys())
                    if has_products:
                        nav_links.append(('/products', 'Shop'))
                    if has_cart:
                        nav_links.append(('/cart', 'Cart'))
                elif group == 'movies':
                    nav_links.append(('/', 'Home'))
                    nav_links.append(('/movies', 'Movies'))
                    nav_links.append(('/tv-sho', 'TV Sho'))
        
        # Method 3: Fallback based on file detection
        if not nav_links:
            # Detect project type from files
            has_movies = any('movies' in f.lower() for f in files.keys())
            has_products = any('products' in f.lower() for f in files.keys())
            has_courses = any('courses' in f.lower() for f in files.keys())
            has_blog = any('blog' in f.lower() for f in files.keys())
            
            if has_movies:
                nav_links = [("/", "Home"), ("/movies", "Movies"), ("/tv-shows", "TV Shows"), ("/search", "Search")]
            elif has_products:
                nav_links = [("/", "Home"), ("/products", "Products"), ("/cart", "Cart"), ("/checkout", "Checkout")]
            elif has_courses:
                nav_links = [("/", "Home"), ("/courses", "Courses"), ("/blog", "Blog"), ("/contact", "Contact")]
            elif has_blog:
                nav_links = [("/", "Home"), ("/blog", "Blog"), ("/about", "About"), ("/contact", "Contact")]
            else:
                nav_links = [("/", "Home"), ("/about", "About"), ("/services", "Services"), ("/contact", "Contact")]

        # ========== FIND PAGE FILES WITH ROUTE GROUP SUPPORT ==========
        async def find_page_file(path: str):
            """Find the corresponding page file supporting route groups"""
            for file_path in files.keys():
                if not file_path.endswith("page.tsx") or "layout" in file_path.lower():
                    continue
                
                # Extract route from file path
                route = file_path.replace("app/", "").replace("/page.tsx", "")
                
                # Handle route groups: remove (group)/ from route
                route = re.sub(r'\([^)]+\)/', '', route)
                
                # Handle home page
                if route == "" or route == "page" or route == "/page" or file_path == "app/page.tsx":
                    route = "/"
                else:
                    route = route.rstrip('/')
                    if not route.startswith("/"):
                        route = f"/{route}"
                    route = route.replace(".tsx", "").replace(".jsx", "")
                
                # Check if routes match (handle both /path and path)
                if route == path or route.lstrip('/') == path.lstrip('/'):
                    return file_path, files[file_path]
            
            return None, None

        # ========== GENERATE PAGE CONTENT IN PARALLEL ==========
        pages_content = {}
        
        async def generate_page_ai(path, label, page_content):
            """Generate HTML from React component using AI"""
            try:
                print(f"🤖 AI generating {path} page...")
                
                # Enhanced prompt for Next.js components
                ai_prompt = f"""Convert this Next.js React component to clean HTML.
                
RULES:
- Remove imports, exports, TypeScript
- Convert JSX to HTML
- Convert Next.js Image to <img> (keep src and alt)
- Convert Next.js Link to <a> (keep href)
- Keep Tailwind CSS classes
- Show actual data content from arrays/maps
- Return ONLY the HTML (no body/script tags)

Component:
{page_content[:2000]}"""

                response_text = await model_router.generate_content(
                    prompt=ai_prompt,
                    config={
                        "temperature": 0.1,
                        "max_output_tokens": 4000,
                    }
                )
                
                ai_content = response_text.strip()
                # Clean up markdown code blocks
                ai_content = re.sub(r'^```html\s*', '', ai_content)
                ai_content = re.sub(r'^```\s*', '', ai_content)
                ai_content = re.sub(r'\s*```$', '', ai_content)
                
                print(f"✅ AI generated {path}: {len(ai_content)} chars")
                return path, ai_content
                
            except Exception as e:
                print(f"⚠️ AI failed for {path}: {e}")
                fallback = f"""
                <div class="text-center py-20">
                    <h1 class="text-4xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                        {label}
                    </h1>
                    <p class="text-xl text-gray-400">Content is being generated.</p>
                </div>
                """
                return path, fallback
        
        # Collect all pages for AI generation
        tasks = []
        for path, label in nav_links:
            page_file_path, page_content = await find_page_file(path)
            
            if page_content:
                tasks.append(generate_page_ai(path, label, page_content))
            else:
                # Create default content for missing pages
                print(f"⚠️ No page file found for {path}, using default content")
                pages_content[path] = f"""
                <div class="text-center py-20">
                    <h1 class="text-4xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                        {label}
                    </h1>
                    <p class="text-xl text-gray-400 mb-8">Welcome to the {label} page.</p>
                </div>
                """
        
        # Run all AI tasks in parallel
        if tasks:
            results = await asyncio.gather(*tasks)
            for path, content in results:
                pages_content[path] = content
        
        print(f"✅ Generated {len(pages_content)} pages in parallel")

        # ========== BUILD NAVIGATION WITH ACTIVE STATES ==========
        nav_buttons_html = ""
        for path, label in nav_links:
            active_class = 'active' if path == '/' else ''
            nav_buttons_html += f'''
            <a href="{path}" data-path="{path}" class="nav-link {active_class} px-4 py-2 rounded-lg transition-all duration-200 text-gray-300 hover:text-white hover:bg-purple-500/20">
                {label}
            </a>
            '''

        # ========== BUILD PAGES WITH PROPER IDS ==========
        pages_html = ""
        page_map_items = []
        for path, content in pages_content.items():
            # Create safe page ID
            if path == "/":
                page_id = "page_home"
            else:
                clean_path = path.lstrip('/').replace('/', '_').replace('-', '_').replace('[', '').replace(']', '')
                page_id = f"page_{clean_path}" if clean_path else "page_home"
            
            active_class = 'active' if path == '/' else ''
            pages_html += f'''
            <div id="{page_id}" class="page {active_class}">
                <div class="container mx-auto px-4 py-8">
                    {content}
                </div>
            </div>
            '''
            page_map_items.append(f'"{path}": "{page_id}"')
        
        page_map_str = ', '.join(page_map_items)

        # ========== ADD LOADING STATES FOR NEXT.JS ==========
        # Check if loading.tsx exists
        has_loading = any('loading.tsx' in f for f in files.keys())
        loading_html = ""
        if has_loading:
            loading_html = '''
            <div id="loading-overlay" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 hidden">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
            </div>
            '''

        # ========== BUILD COMPLETE HTML PREVIEW ==========
        preview_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - Live Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', system-ui, sans-serif;
            background: radial-gradient(ellipse at top, #0a0212 0%, #1a052a 50%, #0a0212 100%);
            color: #e2e8f0;
            min-height: 100vh;
        }}
        
        .page {{
            display: none;
            animation: fadeIn 0.3s ease-in-out;
        }}
        
        .page.active {{
            display: block;
        }}
        
        .nav-link.active {{
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.3), rgba(236, 72, 153, 0.3));
            color: white;
            border: 1px solid rgba(168, 85, 247, 0.5);
        }}
        
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        /* Loading animation */
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .animate-spin {{
            animation: spin 1s linear infinite;
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #1a1a2e;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #4a5568;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #6b7280;
        }}
    </style>
</head>
<body>
    {loading_html}
    
    <nav class="sticky top-0 z-50 bg-black/80 backdrop-blur-xl border-b border-white/10">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                    {project_name}
                </div>
                <div class="hidden md:flex items-center space-x-2" id="nav-links">
                    {nav_buttons_html}
                </div>
                <button id="mobile-menu-button" class="md:hidden p-2 rounded-lg hover:bg-white/10">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                    </svg>
                </button>
            </div>
            <div id="mobile-menu" class="hidden md:hidden pb-4 space-y-2">
                {''.join([f'<a href="{path}" data-path="{path}" class="nav-link-mobile block px-4 py-2 rounded-lg hover:bg-white/10 text-gray-300 hover:text-white">{label}</a>' for path, label in nav_links])}
            </div>
        </div>
    </nav>

    <div class="min-h-screen">
        {pages_html}
    </div>

    <script>
        const pageMap = {{ {page_map_str} }};
        
        function showLoading() {{
            const overlay = document.getElementById('loading-overlay');
            if (overlay) overlay.classList.remove('hidden');
        }}
        
        function hideLoading() {{
            const overlay = document.getElementById('loading-overlay');
            if (overlay) overlay.classList.add('hidden');
        }}
        
        function showPage(path) {{
            showLoading();
            
            setTimeout(() => {{
                const pageId = pageMap[path] || 'page_home';
                document.querySelectorAll('.page').forEach(page => {{
                    page.classList.remove('active');
                }});
                const targetPage = document.getElementById(pageId);
                if (targetPage) {{
                    targetPage.classList.add('active');
                }}
                
                document.querySelectorAll('.nav-link, .nav-link-mobile').forEach(link => {{
                    link.classList.remove('active');
                    if (link.getAttribute('href') === path) {{
                        link.classList.add('active');
                    }}
                }});
                
                hideLoading();
                console.log('📍 Showing page:', path);
                window.parent.postMessage({{ type: 'NAVIGATE', path: path }}, '*');
            }}, 100);
        }}
        
        function handleNavigation(event) {{
            const target = event.target.closest('a');
            if (!target) return;
            
            const href = target.getAttribute('href');
            if (!href || href.startsWith('http') || href.startsWith('//') || href.startsWith('mailto:')) {{
                return;
            }}
            
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
            
            const cleanPath = href.split('#')[0] || '/';
            if (cleanPath !== window.location.pathname) {{
                console.log('🎯 Navigating to:', cleanPath);
                showPage(cleanPath);
                window.history.pushState({{}}, '', cleanPath);
            }}
            
            return false;
        }}
        
        function handlePopState() {{
            const path = window.location.pathname || '/';
            console.log('⬅️ Popstate:', path);
            showPage(path);
        }}
        
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenuButton && mobileMenu) {{
            mobileMenuButton.addEventListener('click', () => {{
                mobileMenu.classList.toggle('hidden');
            }});
        }}
        
        document.querySelectorAll('.nav-link, .nav-link-mobile').forEach(link => {{
            link.addEventListener('click', handleNavigation);
        }});
        
        document.addEventListener('click', function(e) {{
            const link = e.target.closest('a');
            if (link && link.getAttribute('href') && !link.getAttribute('href').startsWith('http')) {{
                handleNavigation(e);
            }}
        }}, true);
        
        
        
        const currentPath = window.location.pathname || '/';
        showPage(currentPath);
        
        console.log('✅ Preview initialized with proper navigation');
        console.log('📋 Navigation links:', {nav_links});
        console.log('🗺️ Route groups detected:', {route_groups});
    </script>
</body>
</html>"""

        return {
            "success": True,
            "preview_html": preview_html,
            "preview_type": "dynamic",
            "message": "Dynamic interactive preview with Next.js 14 support",
            "no_overlay": True,
            "metadata": {
                "route_groups": route_groups,
                "private_folders": private_folders,
                "has_loading": has_loading
            }
        }

    except Exception as e:
        print(f"❌ Dynamic preview error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))











@app.post("/api/generate-static-html")
async def generate_static_html(request: Dict[str, Any]):
    """
    Generate static HTML that works on Vercel (no blob URLs)
    """
    try:
        files: Dict[str, Any] = request.get("files", {})
        project_name: str = request.get("projectName", "Scorpio Project")

        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        # Extract navigation links
        nav_links = []
        nav_content = files.get("components/Navigation.tsx", "")
        if nav_content:
            import re
            href_pattern = r'href:\s*["\']([^"\']+)["\']'
            label_pattern = r'label:\s*["\']([^"\']+)["\']'
            
            matches = re.findall(href_pattern, nav_content)
            labels = re.findall(label_pattern, nav_content)
            
            if matches and labels:
                nav_links = list(zip(matches, labels))
            elif matches:
                nav_links = [(path, path.strip('/').capitalize() or 'Home') for path in matches]
        
        # Fallback navigation
        if not nav_links:
            nav_links = [("/", "Home"), ("/about", "About"), ("/contact", "Contact")]

        # Extract page content
        pages_content = {}
        
        for path, label in nav_links:
            page_file = None
            for file_path in files.keys():
                if file_path.endswith("page.tsx") and "layout" not in file_path.lower():
                    route = file_path.replace("app/", "").replace("/page.tsx", "")
                    if route == "" or route == "page" or route == "/page" or file_path == "app/page.tsx":
                        route = "/"
                    else:
                        route = route.rstrip('/')
                        if not route.startswith("/"):
                            route = f"/{route}"
                    
                    if route == path:
                        page_file = files[file_path]
                        break
            
            if page_file:
                # Extract meaningful content
                clean = page_file
                # Remove imports
                clean = re.sub(r'import\s+.*?from\s+["\'][^"\']+["\'];?\s*', '', clean)
                # Remove exports
                clean = re.sub(r'export\s+default\s+function\s+\w+\s*\([^)]*\)\s*{?', '', clean)
                clean = re.sub(r'export\s+const\s+\w+\s*=\s*', '', clean)
                
                # Extract return JSX
                return_match = re.search(r'return\s*\(\s*([\s\S]*?)\s*\)\s*;', clean)
                if return_match:
                    html_content = return_match.group(1)
                    # Convert className to class
                    html_content = re.sub(r'className=', 'class=', html_content)
                    # Remove curly braces with expressions
                    html_content = re.sub(r'{[^}]*}', '', html_content)
                    # Convert Image to img
                    html_content = re.sub(r'<Image\s+', '<img ', html_content)
                    html_content = re.sub(r'\/>', '>', html_content)
                    # Convert Link to a
                    html_content = re.sub(r'<Link\s+href=', '<a href=', html_content)
                    html_content = re.sub(r'</Link>', '</a>', html_content)
                    pages_content[path] = html_content[:4000]
                else:
                    pages_content[path] = f'<div class="text-center py-20"><h1 class="text-4xl font-bold">{label}</h1><p>Content preview</p></div>'
            else:
                pages_content[path] = f'<div class="text-center py-20"><h1 class="text-4xl font-bold">{label}</h1><p>Content will appear here</p></div>'

        # Build navigation
        nav_buttons_html = ""
        for path, label in nav_links:
            nav_buttons_html += f'<button onclick="showPage(\'{path}\')" class="nav-link px-4 py-2 rounded-lg transition-all text-gray-300 hover:text-white hover:bg-purple-500/20">{label}</button>'

        # Build pages
        pages_html = ""
        page_map = {}
        for path, content in pages_content.items():
            page_id = "page_home" if path == "/" else f"page_{path.lstrip('/').replace('/', '_')}"
            page_map[path] = page_id
            active = 'active' if path == '/' else ''
            pages_html += f'<div id="{page_id}" class="page {active}"><div class="container mx-auto px-4 py-8">{content}</div></div>'

        # Complete HTML
        static_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - Live Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', system-ui, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: #f1f5f9;
            min-height: 100vh;
        }}
        .page {{ display: none; }}
        .page.active {{ display: block; animation: fadeIn 0.3s ease-out; }}
        .nav-link {{ cursor: pointer; transition: all 0.2s; }}
        .nav-link:hover {{ background: rgba(168, 85, 247, 0.2); }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body>
    <nav class="sticky top-0 z-50 bg-black/80 backdrop-blur-xl border-b border-white/10">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                    {project_name}
                </div>
                <div class="hidden md:flex items-center space-x-2" id="nav-links">
                    {nav_buttons_html}
                </div>
                <button id="mobile-menu-button" class="md:hidden p-2 rounded-lg hover:bg-white/10">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                    </svg>
                </button>
            </div>
            <div id="mobile-menu" class="hidden md:hidden pb-4 space-y-2">
                {mobile_nav_html}
            </div>
        </div>
    </nav>

    <div class="min-h-screen">
        {pages_html}
    </div>

    <script>
        const pageMap = {json.dumps(page_map)};
        
        function showPage(path) {{
            const pageId = pageMap[path] || 'page_home';
            document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
            const targetPage = document.getElementById(pageId);
            if (targetPage) targetPage.classList.add('active');
            
            document.querySelectorAll('.nav-link, .nav-link-mobile').forEach(btn => {{
                btn.classList.remove('active', 'bg-purple-500/20');
                if (btn.getAttribute('onclick')?.includes(path)) {{
                    btn.classList.add('active', 'bg-purple-500/20');
                }}
            }});
            
            window.history.pushState({{}}, '', path);
        }}
        
        function handlePopState() {{
            showPage(window.location.pathname);
        }}
        
        document.querySelectorAll('.nav-link, .nav-link-mobile').forEach(btn => {{
            btn.addEventListener('click', (e) => {{
                e.preventDefault();
                const onclick = btn.getAttribute('onclick');
                if (onclick) eval(onclick);
            }});
        }});
        
       
        
        const currentPath = window.location.pathname || '/';
        showPage(currentPath);
    </script>
</body>
</html>"""

        return {
            "success": True,
            "preview_html": static_html,
            "message": "Static HTML generated for Vercel deployment"
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

















@app.post("/api/check-name")
async def check_name(request: Dict[str, Any]):
    """Check if a project name is already used"""
    try:
        name = request.get("name", "")
        if not name:
            raise HTTPException(status_code=400, detail="Name required")
        
        is_used = name_tracker.is_name_used(name)
        
        return {
            "success": True,
            "name": name,
            "is_used": is_used,
            "available": not is_used
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/name-stats")
async def name_stats():
    """Get statistics about name usage"""
    return name_tracker.get_stats()









async def generate_thumbnail_from_html(html_content: str, project_id: str) -> str:
    """Generate thumbnail using Chrome (works in Docker with Chrome installed)"""
    import os
    from pathlib import Path
    
    try:
        if not html_content:
            return None
        
        # Use /tmp for temporary files (works on Render/Docker)
        temp_dir = Path("/tmp/temp_thumbnails")
        temp_dir.mkdir(exist_ok=True)
        
        # Save HTML to temp file
        temp_html = temp_dir / f"{project_id}.html"
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generate screenshot with Chrome
        from html2image import Html2Image
        
        # Use Chrome from environment variable or default path
        chrome_path = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome-stable")
        
        hti = Html2Image(
            output_path=str(temp_dir),
            size=(400, 225),
            browser='chrome',
            browser_executable=chrome_path,
            disable_logging=True
        )
        
        output_file = f"{project_id}.png"
        hti.screenshot(
            html_file=str(temp_html),
            save_as=output_file
        )
        
        temp_thumbnail = temp_dir / output_file
        
        if temp_thumbnail.exists():
            local_path = str(temp_thumbnail.absolute())
            print(f"📸 Thumbnail generated at: {local_path}")
            print(f"   Size: {temp_thumbnail.stat().st_size} bytes")
            
            # Cleanup temp HTML file
            os.remove(temp_html)
            
            return local_path
        
        return None
        
    except Exception as e:
        print(f"❌ Thumbnail generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

















@app.get("/api/get-project/{project_id}")
async def get_project(project_id: str):
    try:
        async with AsyncSessionLocal() as session:
            # Get project metadata
            stmt = select(Project).where(Project.id == project_id)
            result = await session.execute(stmt)
            project = result.scalar_one_or_none()
            
            if not project:
                return {"success": False, "message": "Project not found"}
            
            # Get all files metadata for this project
            stmt = select(ProjectFile).where(ProjectFile.project_id == project_id)
            result = await session.execute(stmt)
            files = result.scalars().all()
            
            # Reconstruct files dictionary with Cloudinary URLs
            files_dict = {}
            for file in files:
                # Store file metadata (content is on Cloudinary)
                files_dict[file.file_path] = {
                    "type": file.file_type,
                    "size": file.size_bytes,
                    "url": file.cloudinary_url,
                    "path": file.file_path
                }
            
            return {
                "success": True,
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "prompt": project.prompt,
                    "preview_url": project.preview_url,      # Cloudinary URL for preview
                    "thumbnail_url": project.thumbnail_url,  # Cloudinary URL for thumbnail
                    "files_url": project.files_url,          # Cloudinary URL for ZIP
                    "timestamp": project.timestamp.isoformat(),
                    "project_type": project.project_type,
                    "file_count": project.file_count
                },
                "files": files_dict,
                "file_count": len(files)
            }
            
    except Exception as e:
        print(f"❌ Get project failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))








@app.delete("/api/delete-project/{project_id}")
async def delete_project(project_id: str):
    try:
        async with AsyncSessionLocal() as session:
            # Delete project files first
            stmt = delete(ProjectFile).where(ProjectFile.project_id == project_id)
            await session.execute(stmt)
            
            # Delete project metadata
            stmt = delete(Project).where(Project.id == project_id)
            result = await session.execute(stmt)
            
            await session.commit()
            
            if result.rowcount > 0:
                return {"success": True, "message": "Project deleted successfully"}
            else:
                return {"success": False, "message": "Project not found"}
                
    except Exception as e:
        print(f"❌ Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))








async def generate_thumbnail_from_html(html_content: str, project_id: str) -> str:
    """Generate thumbnail using Playwright (works in Docker)"""
    import tempfile
    from pathlib import Path

    try:
        if not html_content:
            return None

        temp_dir = Path(tempfile.gettempdir()) / "temp_thumbnails"
        temp_dir.mkdir(exist_ok=True)

        temp_html = temp_dir / f"{project_id}.html"
        temp_html.write_text(html_content, encoding="utf-8")

        output_path = temp_dir / f"{project_id}.png"

        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-zygote",
                    "--single-process",
                ],
            )
            page = await browser.new_page(viewport={"width": 1280, "height": 720})
            await page.goto(
                f"file://{temp_html.absolute()}",
                wait_until="networkidle",
                timeout=15_000,
            )
            await page.screenshot(
                path=str(output_path),
                clip={"x": 0, "y": 0, "width": 1280, "height": 720},
            )
            await browser.close()

        temp_html.unlink(missing_ok=True)

        if output_path.exists() and output_path.stat().st_size > 0:
            print(f"📸 Thumbnail generated: {output_path} ({output_path.stat().st_size:,} bytes)")
            return str(output_path.absolute())

        print("⚠️ Screenshot file is empty or missing")
        return None

    except Exception as e:
        import traceback
        print(f"❌ Thumbnail generation failed: {e}")
        traceback.print_exc()
        return None







@app.get("/api/get-projects")
async def get_projects(request: Request, limit: int = 10, offset: int = 0):
    """Get projects metadata only (fastest - no file contents)"""
    
    # Get user info from JWT token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    if not token:
        return {
            "success": True,
            "projects": [],
            "count": 0,
            "total": 0,
            "has_more": False
        }
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_email = payload.get('email')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return {
            "success": True,
            "projects": [],
            "count": 0,
            "total": 0,
            "has_more": False
        }
    
    try:
        async with AsyncSessionLocal() as session:
            # Get user ID (single query)
            user_stmt = select(User.id).where(User.email == user_email)
            user_result = await session.execute(user_stmt)
            actual_user_id = user_result.scalar_one_or_none()
            
            if not actual_user_id:
                return {
                    "success": True,
                    "projects": [],
                    "count": 0,
                    "total": 0,
                    "has_more": False
                }
            
            # Get total count (lightweight)
            count_stmt = select(func.count()).select_from(Project).where(Project.user_id == actual_user_id)
            total_count = await session.execute(count_stmt)
            total_count = total_count.scalar() or 0
            
            # ✅ Get metadata including ALL Cloudinary URLs
            stmt = select(
                Project.id,
                Project.name,
                Project.prompt,
                Project.timestamp,
                Project.project_type,
                Project.file_count,
                Project.thumbnail_url,   # Cloudinary URL for thumbnail
                Project.preview_url,     # Cloudinary URL for preview HTML
                Project.files_url        # Cloudinary URL for ZIP file
            ).where(
                Project.user_id == actual_user_id
            ).order_by(
                desc(Project.timestamp)
            ).offset(offset).limit(limit)
            
            result = await session.execute(stmt)
            rows = result.all()
            
            project_list = [
                {
                    "id": row[0],
                    "name": row[1],
                    "prompt": (row[2][:100] + "...") if row[2] and len(row[2]) > 100 else (row[2] or ""),
                    "timestamp": row[3].isoformat(),
                    "project_type": row[4],
                    "file_count": row[5],
                    "thumbnail_url": row[6],   # ← Cloudinary URL
                    "preview_url": row[7],     # ← Cloudinary URL (NEW)
                    "files_url": row[8]        # ← Cloudinary URL (NEW)
                }
                for row in rows
            ]
            
            has_more = (offset + len(project_list)) < total_count
            
            return {
                "success": True,
                "projects": project_list,
                "count": len(project_list),
                "total": total_count,
                "has_more": has_more,
                "is_metadata": True
            }
    except Exception as e:
        print(f"❌ Error loading projects: {e}")
        return {
            "success": True,
            "projects": [],
            "count": 0,
            "total": 0,
            "has_more": False
        }





# ========== CREDITS ENDPOINTS ==========

@app.get("/api/credits")
async def get_user_credits(user_id: str):
    """Get user credits from database"""
    try:
        async with AsyncSessionLocal() as session:
            # Check if user has credits record
            stmt = select(UserCredits).where(UserCredits.user_id == user_id)
            result = await session.execute(stmt)
            user_credits = result.scalar_one_or_none()
            
            today = date.today()
            
            if not user_credits:
                # Create new credits record
                user_credits = UserCredits(
                    user_id=user_id,
                    plan="free",
                    daily_credits_used=0,
                    daily_reset_date=today,
                    monthly_credits_used=0,
                    monthly_reset_date=today
                )
                session.add(user_credits)
                await session.commit()
                await session.refresh(user_credits)
            
            # Check if daily reset needed
            if user_credits.daily_reset_date != today:
                user_credits.daily_credits_used = 0
                user_credits.daily_reset_date = today
                await session.commit()
            
            plan_limits = {
                "free": {"daily": 5, "monthly": 30},
                "pro": {"daily": 15, "monthly": 120},
                "business": {"daily": 40, "monthly": 350}
            }
            limits = plan_limits.get(user_credits.plan, plan_limits["free"])
            
            daily_remaining = limits["daily"] - user_credits.daily_credits_used
            monthly_remaining = limits["monthly"] - user_credits.monthly_credits_used
            
            return {
                "success": True,
                "plan": user_credits.plan,
                "dailyRemaining": max(0, daily_remaining),
                "monthlyRemaining": max(0, monthly_remaining),
                "dailyUsed": user_credits.daily_credits_used,
                "monthlyUsed": user_credits.monthly_credits_used,
                "dailyLimit": limits["daily"],
                "monthlyLimit": limits["monthly"]
            }
    except Exception as e:
        print(f"❌ Credits error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/credits/deduct")
async def deduct_credits(request: Request):
    """Deduct credits from user"""
    try:
        data = await request.json()
        user_id = data.get("userId")
        credits = data.get("credits", 0)
        
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID required")
        
        async with AsyncSessionLocal() as session:
            # Get user credits
            stmt = select(UserCredits).where(UserCredits.user_id == user_id)
            result = await session.execute(stmt)
            user_credits = result.scalar_one_or_none()
            
            if not user_credits:
                raise HTTPException(status_code=404, detail="User credits not found")
            
            today = date.today()
            
            # Check daily reset
            if user_credits.daily_reset_date != today:
                user_credits.daily_credits_used = 0
                user_credits.daily_reset_date = today
            
            plan_limits = {
                "free": {"daily": 5, "monthly": 30},
                "pro": {"daily": 15, "monthly": 120},
                "business": {"daily": 40, "monthly": 350}
            }
            limits = plan_limits.get(user_credits.plan, plan_limits["free"])
            
            daily_remaining = limits["daily"] - user_credits.daily_credits_used
            monthly_remaining = limits["monthly"] - user_credits.monthly_credits_used
            
            if daily_remaining < credits or monthly_remaining < credits:
                raise HTTPException(status_code=400, detail="Insufficient credits")
            
            # Deduct credits
            user_credits.daily_credits_used += credits
            user_credits.monthly_credits_used += credits
            await session.commit()
            
            return {
                "success": True,
                "creditsUsed": credits,
                "dailyRemaining": daily_remaining - credits,
                "monthlyRemaining": monthly_remaining - credits
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Deduct error: {e}")
        raise HTTPException(status_code=500, detail=str(e))









@app.post("/api/admin/upgrade")
async def admin_upgrade_user(request: Request):
    """Admin endpoint to upgrade user plan (development only)"""
    try:
        data = await request.json()
        user_id = data.get("userId")
        plan = data.get("plan")
        
        if not user_id or not plan:
            raise HTTPException(status_code=400, detail="Missing userId or plan")
        
        if plan not in ["free", "pro", "business"]:
            raise HTTPException(status_code=400, detail="Invalid plan")
        
        async with AsyncSessionLocal() as session:
            # Update user credits
            stmt = select(UserCredits).where(UserCredits.user_id == user_id)
            result = await session.execute(stmt)
            user_credits = result.scalar_one_or_none()
            
            if not user_credits:
                # Create if doesn't exist
                today = date.today()
                user_credits = UserCredits(
                    user_id=user_id,
                    plan=plan,
                    daily_credits_used=0,
                    daily_reset_date=today,
                    monthly_credits_used=0,
                    monthly_reset_date=today
                )
                session.add(user_credits)
            else:
                user_credits.plan = plan
            
            await session.commit()
            
            return {"success": True, "plan": plan}
    except Exception as e:
        print(f"❌ Admin upgrade error: {e}")
        raise HTTPException(status_code=500, detail=str(e))













@app.get("/")
async def root():
    return {
        "message": "EagleCode API is running",
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/health",
            "/api/auth/google/signin",
            "/api/auth/google/signup",
            "/ws/build"
        ]
    }









@app.post("/api/save-project")
async def save_project(request: Request):
    try:
        body = await request.json()
        name = body.get("name", "")
        prompt = body.get("prompt", "")
        files = body.get("files", {})
        preview_html = body.get("preview_html", "")
        
        # ========== EXTRACT BRAND NAME FROM GENERATED FILES ==========
        extracted_name = extract_brand_name(files)
        if extracted_name:
            name = extracted_name
            print(f"🏷️ Extracted brand name: {name}")
        # ============================================================
        
        # Get user info from token
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "")
        
        if not token:
            print("⚠️ No token provided")
            return {"success": False, "message": "Authentication required"}
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_email = payload.get('email')
            print(f"💾 Saving project for email: {user_email}")
        except Exception as e:
            print(f"⚠️ Token decode error: {e}")
            return {"success": False, "message": "Invalid token"}
        
        # Find user by email to get user_id
        async with AsyncSessionLocal() as session:
            user_stmt = select(User).where(User.email == user_email)
            user_result = await session.execute(user_stmt)
            db_user = user_result.scalar_one_or_none()
            
            if db_user:
                user_id = db_user.id
                print(f"✅ Found user: {user_email} -> {user_id}")
            else:
                print(f"❌ User not found: {user_email}")
                return {"success": False, "message": "User not found"}
            
            # Handle timestamp
            timestamp_raw = body.get("timestamp")
            if timestamp_raw and isinstance(timestamp_raw, str):
                if '+' in timestamp_raw or timestamp_raw.endswith('Z'):
                    timestamp_raw = timestamp_raw.replace('Z', '').split('+')[0]
                timestamp = datetime.fromisoformat(timestamp_raw)
            else:
                timestamp = datetime.now()
            
            # Detect project type
            prompt_lower = prompt.lower()
            if any(w in prompt_lower for w in ['school', 'academy', 'university', 'college']):
                project_type = "school"
            elif any(w in prompt_lower for w in ['coffee', 'roastery', 'cafe', 'brew']):
                project_type = "coffee"
            elif any(w in prompt_lower for w in ['hotel', 'resort', 'lodge', 'inn']):
                project_type = "hotel"
            elif any(w in prompt_lower for w in ['gym', 'fitness', 'workout']):
                project_type = "gym"
            elif any(w in prompt_lower for w in ['restaurant', 'bistro', 'dining']):
                project_type = "restaurant"
            else:
                project_type = "general"
            
            # Create project ID
            import uuid
            project_id = str(uuid.uuid4())
            
            # ========== UPLOAD TO CLOUDINARY ==========
            preview_url = None
            files_url = None
            thumbnail_url = None
            
            # 1. Upload preview HTML to Cloudinary (as HTML, not raw)
            if preview_html:
                try:
                        import gzip
                        import tempfile
                        import os
                        
                        # Create a temporary HTML file
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp:
                                tmp.write(preview_html)
                                tmp_path = tmp.name
                        
                        # Upload the file as HTML
                        upload_result = cloudinary.uploader.upload(
                                tmp_path,
                                folder=f"project_previews/{project_id}",
                                public_id="preview",
                                resource_type="auto",
                                overwrite=True,
                                format="html",
                                use_filename=True,
                                unique_filename=False,
                              
                        )
                        preview_url = upload_result['secure_url']
                        print(f"☁️ Preview uploaded to Cloudinary: {preview_url[:60]}...")
                        
                        # Cleanup temp file
                        os.unlink(tmp_path)
                        
                except Exception as e:
                        print(f"⚠️ Failed to upload preview: {e}")
            
            # 2. Upload files as ZIP to Cloudinary
            if files:
                try:
                        import zipfile
                        from io import BytesIO
                        
                        # Create ZIP in memory
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                                for file_path, content in files.items():
                                        if file_path == "preview_html":
                                                continue
                                        if isinstance(content, dict):
                                                content = json.dumps(content, indent=2)
                                        elif not isinstance(content, str):
                                                content = str(content)
                                        zipf.writestr(file_path, content)
                        
                        zip_buffer.seek(0)
                        
                        # Upload to Cloudinary
                        upload_result = cloudinary.uploader.upload(
                                zip_buffer.getvalue(),
                                folder=f"project_files/{project_id}",
                                public_id="files",
                                resource_type="raw",
                                overwrite=True
                        )
                        files_url = upload_result['secure_url']
                        print(f"☁️ Files uploaded to Cloudinary: {files_url[:60]}...")
                        
                except Exception as e:
                        print(f"⚠️ Failed to upload files: {e}")
                        files_url = None
            
            # 3. Generate and upload thumbnail to Cloudinary
            if preview_html:
                try:
                        # Generate thumbnail and get local file path
                        thumbnail_local_path = await generate_thumbnail_from_html(preview_html, project_id)
                        
                        if thumbnail_local_path and os.path.exists(thumbnail_local_path):
                                print(f"📸 Uploading thumbnail from: {thumbnail_local_path}")
                                
                                # Upload to Cloudinary
                                upload_result = cloudinary.uploader.upload(
                                        thumbnail_local_path,
                                        folder=f"project_thumbnails/{project_id}",
                                        public_id="thumbnail",
                                        overwrite=True,
                                        width=400,
                                        height=225,
                                        crop="fill",
                                        quality="auto:best"
                                )
                                thumbnail_url = upload_result['secure_url']
                                print(f"☁️ Thumbnail uploaded to Cloudinary: {thumbnail_url[:60]}...")
                                
                                # Cleanup local thumbnail file
                                if os.path.exists(thumbnail_local_path):
                                        os.unlink(thumbnail_local_path)
                                        print(f"🗑️ Cleaned up local thumbnail")
                        else:
                                print(f"⚠️ Thumbnail file not generated")
                                
                except Exception as e:
                        print(f"⚠️ Failed to upload thumbnail: {e}")
                        import traceback
                        traceback.print_exc()
            
            # ========== CREATE PROJECT WITH URLs ONLY ==========
            project = Project(
                    id=project_id,
                    name=name,
                    prompt=prompt,
                    user_id=user_id,
                    preview_url=preview_url,
                    thumbnail_url=thumbnail_url,
                    files_url=files_url,
                    timestamp=timestamp,
                    project_type=project_type,
                    file_count=len(files),
                    size_bytes=len(json.dumps(files)),
                    is_public=False,
                    version=1
            )
            session.add(project)
            await session.flush()
            
            # ========== SAVE FILE METADATA (NO CONTENT) ==========
            file_saved_count = 0
            for file_path, content in files.items():
                    if file_path == "preview_html":
                            continue
                    
                    # Determine file type
                    file_type = None
                    if '.' in file_path:
                            ext = file_path.split('.')[-1].lower()
                            file_type_map = {
                                    'html': 'html', 'htm': 'html',
                                    'css': 'css', 'scss': 'scss',
                                    'js': 'javascript', 'ts': 'typescript',
                                    'jsx': 'jsx', 'tsx': 'tsx',
                                    'json': 'json', 'md': 'markdown',
                                    'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 'svg': 'image'
                            }
                            file_type = file_type_map.get(ext, 'text')
                    
                    # Convert content to string for size calculation
                    if isinstance(content, dict):
                            content_str = json.dumps(content, indent=2)
                    elif not isinstance(content, str):
                            content_str = str(content)
                    else:
                            content_str = content
                    
                    # Store ONLY metadata (no content)
                    project_file = ProjectFile(
                            project_id=project_id,
                            file_path=file_path,
                            file_type=file_type,
                            size_bytes=len(content_str),
                            cloudinary_url=f"{files_url}/{file_path}" if files_url else None
                    )
                    session.add(project_file)
                    file_saved_count += 1
            
            await session.commit()
            
            # ✅ Notify all connected clients to refresh their projects list
            await notify_projects_updated(name)
            print(f"✅ Saved project '{name}' for user {user_email}")
            
            return {
                    "success": True,
                    "id": project_id,
                    "name": name,
                    "user_email": user_email,
                    "file_count": file_saved_count,
                    "has_thumbnail": thumbnail_url is not None,
                    "thumbnail_url": thumbnail_url,
                    "preview_url": preview_url,
                    "files_url": files_url
            }
            
    except Exception as e:
        print(f"❌ Save failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}













# ========== ADMIN TIERS / UPGRADE SYSTEM ==========

@app.get("/api/admin/users")
async def get_all_users(request: Request):
    """Admin: Get all users with their credit plans"""
    # Verify admin token (you can add proper admin auth later)
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    if not token:
        raise HTTPException(status_code=401, detail="Admin access required")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_email = payload.get('email')
        
        # Check if user is admin (you can add admin flag in users table)
        # For now, allow specific emails as admin
        admin_emails = ["admin@eaglecode.com", "hopefreymosingi1@gmail.com"]
        if user_email not in admin_emails:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        async with AsyncSessionLocal() as session:
            # Get all users with their credits info
            stmt = select(User, UserCredits).join(
                UserCredits, User.id == UserCredits.user_id, isouter=True
            ).order_by(User.created_at.desc())
            
            result = await session.execute(stmt)
            users_data = result.all()
            
            users = []
            for user, credits in users_data:
                users.append({
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "created_at": user.created_at.isoformat(),
                    "plan": credits.plan if credits else "free",
                    "daily_credits_used": credits.daily_credits_used if credits else 0,
                    "monthly_credits_used": credits.monthly_credits_used if credits else 0,
                    "daily_limit": 5 if (credits and credits.plan == "free") else (15 if (credits and credits.plan == "pro") else 40),
                    "monthly_limit": 30 if (credits and credits.plan == "free") else (120 if (credits and credits.plan == "pro") else 350)
                })
            
            return {
                "success": True,
                "users": users,
                "total": len(users)
            }
            
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"❌ Admin users error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/upgrade-user")
async def admin_upgrade_user(request: Request):
    """Admin: Upgrade a user to a different plan"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        new_plan = data.get("plan")  # free, pro, business
        
        # Verify admin
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "")
        
        if not token:
            raise HTTPException(status_code=401, detail="Admin access required")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        admin_email = payload.get('email')
        
        admin_emails = ["admin@eaglecode.com", "hopefreymosingi1@gmail.com"]
        if admin_email not in admin_emails:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if new_plan not in ["free", "pro", "business"]:
            raise HTTPException(status_code=400, detail="Invalid plan")
        
        async with AsyncSessionLocal() as session:
            # Get user credits
            stmt = select(UserCredits).where(UserCredits.user_id == user_id)
            result = await session.execute(stmt)
            user_credits = result.scalar_one_or_none()
            
            today = date.today()
            
            if not user_credits:
                # Create new credits record
                user_credits = UserCredits(
                    user_id=user_id,
                    plan=new_plan,
                    daily_credits_used=0,
                    daily_reset_date=today,
                    monthly_credits_used=0,
                    monthly_reset_date=today
                )
                session.add(user_credits)
            else:
                user_credits.plan = new_plan
            
            await session.commit()
            
            return {
                "success": True,
                "message": f"User upgraded to {new_plan} plan",
                "user_id": user_id,
                "new_plan": new_plan
            }
            
    except Exception as e:
        print(f"❌ Admin upgrade error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/reset-credits")
async def admin_reset_credits(request: Request):
    """Admin: Reset user credits manually"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        
        # Verify admin
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "")
        
        if not token:
            raise HTTPException(status_code=401, detail="Admin access required")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        admin_email = payload.get('email')
        
        admin_emails = ["admin@eaglecode.com", "hopefreymosingi1@gmail.com"]
        if admin_email not in admin_emails:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        async with AsyncSessionLocal() as session:
            stmt = select(UserCredits).where(UserCredits.user_id == user_id)
            result = await session.execute(stmt)
            user_credits = result.scalar_one_or_none()
            
            if user_credits:
                today = date.today()
                user_credits.daily_credits_used = 0
                user_credits.daily_reset_date = today
                user_credits.monthly_credits_used = 0
                user_credits.monthly_reset_date = today
                await session.commit()
            
            return {
                "success": True,
                "message": "Credits reset successfully"
            }
            
    except Exception as e:
        print(f"❌ Reset credits error: {e}")
        raise HTTPException(status_code=500, detail=str(e))











# ========== UPGRADE REQUEST SYSTEM ==========

@app.post("/api/request-upgrade")
async def request_upgrade(request: Request):
    """User requests an upgrade (sends notification to admin)"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        requested_plan = data.get("plan")  # pro, business, custom
        message = data.get("message", "")
        
        # Get auth token
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "")
        
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_email = payload.get('email')
        
        async with AsyncSessionLocal() as session:
            # Get user details
            stmt = select(User).where(User.email == user_email)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Create upgrade request
            upgrade_request = UpgradeRequest(
                user_id=db_user.id,
                user_email=db_user.email,
                user_name=db_user.username,
                requested_plan=requested_plan,
                message=message,
                status="pending"
            )
            session.add(upgrade_request)
            await session.commit()
            
            # In a real app, send email to admin here
            # For now, just log it
            print(f"\n📧 UPGRADE REQUEST RECEIVED!")
            print(f"   User: {db_user.email} ({db_user.username})")
            print(f"   Requested Plan: {requested_plan}")
            print(f"   Message: {message[:200] if message else 'No message'}")
            print(f"   Request ID: {upgrade_request.id}")
            
            return {
                "success": True,
                "message": "Upgrade request sent to admin. You will be contacted shortly.",
                "request_id": upgrade_request.id
            }
            
    except Exception as e:
        print(f"❌ Upgrade request error: {e}")
        raise HTTPException(status_code=500, detail=str(e))









@app.get("/api/admin/upgrade-requests")
async def get_upgrade_requests(request: Request):
    """Admin: Get all upgrade requests"""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    # Verify admin access
    admin_emails = ["admin@eaglecode.com", "hopefreymosingi1@gmail.com"]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        admin_email = payload.get('email')
        
        if admin_email not in admin_emails:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        async with AsyncSessionLocal() as session:
            stmt = select(UpgradeRequest).order_by(desc(UpgradeRequest.created_at))
            result = await session.execute(stmt)
            requests = result.scalars().all()
            
            # Debug: Print screenshot URLs
            for r in requests:
                print(f"📸 Request {r.id}: screenshot_url = {r.payment_screenshot_url}")
            
            return {
                "success": True,
                "requests": [
                    {
                        "id": r.id,
                        "user_id": r.user_id,
                        "user_email": r.user_email,
                        "user_name": r.user_name,
                        "requested_plan": r.requested_plan,
                        "payment_screenshot_url": r.payment_screenshot_url,  # ✅ Fixed: was 'req' now 'r'
                        "email_sent": r.email_sent,  # ✅ Add this
                        "email_sent_at": r.email_sent_at.isoformat() if r.email_sent_at else None, 
                        "message": r.message,
                        "status": r.status,
                        "admin_notes": r.admin_notes,
                        "created_at": r.created_at.isoformat() if r.created_at else None
                    }
                    for r in requests
                ]
            }
            
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"❌ Get upgrade requests error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

















@app.post("/api/admin/update-request-status")
async def update_request_status(request: Request):
    """Admin: Update upgrade request status and add notes"""
    try:
        data = await request.json()
        request_id = data.get("request_id")
        status = data.get("status")  # approved, rejected, contacted
        admin_notes = data.get("admin_notes", "")
        
        # Verify admin
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "")
        
        admin_emails = ["admin@eaglecode.com", "hopefreymosingi1@gmail.com"]
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        admin_email = payload.get('email')
        
        if admin_email not in admin_emails:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        async with AsyncSessionLocal() as session:
            stmt = select(UpgradeRequest).where(UpgradeRequest.id == request_id)
            result = await session.execute(stmt)
            upgrade_request = result.scalar_one_or_none()
            
            if not upgrade_request:
                raise HTTPException(status_code=404, detail="Request not found")
            
            upgrade_request.status = status
            upgrade_request.admin_notes = admin_notes
            upgrade_request.updated_at = datetime.now()
            
            # If approved, upgrade the user
            if status == "approved":
                # Update user credits plan
                credits_stmt = select(UserCredits).where(UserCredits.user_id == upgrade_request.user_id)
                credits_result = await session.execute(credits_stmt)
                user_credits = credits_result.scalar_one_or_none()
                
                today = date.today()
                if not user_credits:
                    user_credits = UserCredits(
                        user_id=upgrade_request.user_id,
                        plan=upgrade_request.requested_plan,
                        daily_credits_used=0,
                        daily_reset_date=today,
                        monthly_credits_used=0,
                        monthly_reset_date=today
                    )
                    session.add(user_credits)
                else:
                    user_credits.plan = upgrade_request.requested_plan
            
            await session.commit()
            
            print(f"\n✅ Upgrade request {status.upper()}: {upgrade_request.user_email} → {upgrade_request.requested_plan}")
            
            return {
                "success": True,
                "message": f"Request {status} successfully"
            }
            
    except Exception as e:
        print(f"❌ Update request error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


















@app.post("/api/admin/send-payment-email")
async def send_payment_email(request: Request):
    """Admin: Mark email as sent for an upgrade request"""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    # Verify admin access
    admin_emails = ["admin@eaglecode.com", "hopefreymosingi1@gmail.com"]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        admin_email = payload.get('email')
        
        if admin_email not in admin_emails:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        body = await request.json()
        request_id = body.get("request_id")
        
        async with AsyncSessionLocal() as session:
            stmt = select(UpgradeRequest).where(UpgradeRequest.id == request_id)
            result = await session.execute(stmt)
            upgrade_request = result.scalar_one_or_none()
            
            if upgrade_request:
                upgrade_request.email_sent = True
                upgrade_request.email_sent_at = datetime.now()
                await session.commit()
                return {"success": True, "message": "Email marked as sent"}
            else:
                return {"success": False, "message": "Request not found"}
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "message": str(e)}






@app.get("/api/preview/{filename}")
async def serve_preview(filename: str):
    """Serve saved preview HTML file"""
    previews_dir = os.path.join(os.path.dirname(__file__), "previews")
    preview_path = os.path.join(previews_dir, filename)
    
    # Security: prevent path traversal
    if not os.path.exists(preview_path) or not filename.endswith('.html'):
        raise HTTPException(status_code=404, detail="Preview not found")
    
    with open(preview_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return Response(
        content=html_content,
        media_type="text/html"
    )






@app.websocket("/ws/projects")
async def websocket_projects(websocket: WebSocket):
    """WebSocket for real-time project updates"""
    await websocket.accept()
    active_project_connections.append(websocket)
    print(f"✅ Projects WebSocket connected. Total: {len(active_project_connections)}")
    
    try:
        while True:
            # Keep connection alive
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except:
                await asyncio.sleep(30)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in active_project_connections:
            active_project_connections.remove(websocket)
        print(f"🔌 Projects WebSocket disconnected. Remaining: {len(active_project_connections)}")



async def notify_projects_updated(project_name: str = None):
    """Notify all connected clients that projects have been updated"""
    if not active_project_connections:
        return
    
    message = {
        "type": "projects_updated",
        "project_name": project_name,
        "timestamp": datetime.now().isoformat()
    }
    
    disconnected = []
    for connection in active_project_connections:
        try:
            await connection.send_json(message)
        except:
            disconnected.append(connection)
    
    for conn in disconnected:
        if conn in active_project_connections:
            active_project_connections.remove(conn)
    
    if active_project_connections:
        print(f"📡 Notified {len(active_project_connections)} clients about project update")










@app.delete("/api/admin/delete-request/{request_id}")
async def delete_request(request_id: str, request: Request):
    """Admin: Delete an upgrade request"""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    # Verify admin access
    admin_emails = ["admin@eaglecode.com", "hopefreymosingi1@gmail.com"]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        admin_email = payload.get('email')
        
        if admin_email not in admin_emails:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Delete the request
        async with AsyncSessionLocal() as session:
            stmt = delete(UpgradeRequest).where(UpgradeRequest.id == request_id)
            result = await session.execute(stmt)
            await session.commit()
            
            if result.rowcount > 0:
                return {"success": True, "message": "Request deleted successfully"}
            else:
                return {"success": False, "message": "Request not found"}
            
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"❌ Delete request error: {e}")
        raise HTTPException(status_code=500, detail=str(e))







@app.post("/api/upload-payment-proof")
async def upload_payment_proof(
    request_id: str = Form(...),
    payment_screenshot: UploadFile = File(...),
    user_id: str = Form(None),
):
    """Upload payment proof screenshot to Cloudinary"""
    try:
        # Read the file content
        content = await payment_screenshot.read()
        
        # Upload to Cloudinary
        import cloudinary.uploader
        from io import BytesIO
        
        # Create a unique filename
        timestamp = int(datetime.now().timestamp())
        public_id = f"payment_proofs/{request_id}_{timestamp}"
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            BytesIO(content),
            folder="payment_proofs",
            public_id=f"{request_id}_{timestamp}",
            allowed_formats=["jpg", "jpeg", "png", "webp"],
            transformation=[
                {"quality": "auto"},
                {"fetch_format": "auto"}
            ]
        )
        
        cloudinary_url = upload_result['secure_url']
        print(f"☁️ Uploaded to Cloudinary: {cloudinary_url}")
        
        # Update database with Cloudinary URL
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UpgradeRequest).where(UpgradeRequest.id == request_id)
            )
            upgrade_request = result.scalar_one_or_none()
            
            if upgrade_request:
                upgrade_request.payment_screenshot_url = cloudinary_url
                upgrade_request.status = "payment_received"
                upgrade_request.updated_at = datetime.now()
                await session.commit()
                print(f"✅ Database updated for request {request_id}")
            else:
                print(f"⚠️ Request {request_id} not found")
        
        return {
            "success": True, 
            "message": "Payment proof uploaded to Cloudinary",
            "screenshot_url": cloudinary_url
        }
        
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return {"success": False, "message": str(e)}






@app.get("/api/key-stats")
async def get_key_stats():
    return model_router.get_stats()



@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Scorpio Architecture Engine",
        "version": "2.6.0",
        "timestamp": datetime.now().isoformat(),
        "total_projects": name_tracker.get_stats()["total_unique_names"],
        "endpoints": [
            "/ws/build",
            "/api/edit-file",
            "/api/edit-batch",
            "/api/update-preview",
            "/api/search-content",
            "/api/regenerate-preview",
            "/api/search-images",
            "/api/check-name",
            "/api/name-stats",
            "/health"
        ]
    }













if __name__ == "__main__":
    import signal
    import sys
    import os

    def force_shutdown(signum, frame):
        print("\n💀 FORCE KILL initiated!")
        print("Terminating all processes immediately...")
        # Force exit without any cleanup
        os._exit(0)

    # Make Ctrl+C force kill (no graceful shutdown)
    signal.signal(signal.SIGINT, force_shutdown)

    print("=" * 50)
    print("🚀 Starting EagleCode Backend Server...")
    print("📍 Press Ctrl + C to FORCE KILL the server")
    print("=" * 50)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
