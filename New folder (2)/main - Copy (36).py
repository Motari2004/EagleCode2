import json
import os
import re
import io
import jwt  # noqa
import asyncio
from html2image import Html2Image
from pathlib import Path
import json as json_module

from fastapi.staticfiles import StaticFiles

from fastapi import Depends


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, datetime, timedelta
import pytz


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
            os.environ.get("MODEL_PRIMARY", "gemini-flash-lite-latest"),
            os.environ.get("MODEL_SECONDARY", "gemini-2.5-flash-lite-"), 
            
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
                        print(f"🚫 Key {key_index + 1} | Model {model} quota exceeded, trying next model...")
                    
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
                        print(f"🚫 Key {key_index + 1} | Model {model} quota exceeded, trying next model...")
                    
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







# ====================== SAVE REGENERATED PREVIEW (Option A) ======================
async def save_regenerated_preview(
    preview_html: str,
    project_name: str = "untitled",
    project_id: Optional[str] = None
) -> Optional[str]:
    """
    Saves the regenerated preview after edit to the PREVIEWS_DIR
    (same location as normal previews).
    """
    try:
        if not preview_html:
            return None

        # Create safe filename
        if project_id:
            filename = f"{project_id}_preview.html"
        else:
            # Fallback: sanitize project name
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', project_name.lower().strip())
            if not safe_name:
                safe_name = "preview"
            filename = f"{safe_name}_preview.html"

        preview_path = PREVIEWS_DIR / filename

        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(preview_html)

        print(f"💾 Regenerated preview saved → {preview_path}")
        return str(preview_path)

    except Exception as e:
        print(f"⚠️ Failed to save regenerated preview: {e}")
        import traceback
        traceback.print_exc()
        return None









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
        cloudinary_image_url = Column(String(500), nullable=True)  # ✅ ADD THIS - Hero image URL







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



















async def manage_package_json(current_content: str, edit_description: str) -> tuple[Optional[str], List[str]]:
    """
    Intelligently add or remove dependencies from package.json
    
    Returns:
        tuple: (updated_content, list_of_changes_made)
    """
    try:
        # Parse current package.json
        package_data = json_module.loads(current_content)
        
        # Ensure dependencies object exists
        if "dependencies" not in package_data:
            package_data["dependencies"] = {}
        if "devDependencies" not in package_data:
            package_data["devDependencies"] = {}
        
        changes_made = []
        edit_lower = edit_description.lower()
        
        # ========== BLACKLIST: Words that are NOT npm packages ==========
        blacklist = {
            'signup', 'login', 'auth', 'sign up', 'log in',
            'page', 'pages', 'route', 'routes', 'api', 'component',
            'create', 'delete', 'remove', 'add', 'install', 'update',
            'implement', 'implementation', 'implementatino',  # ← typo from your logs
            'neon', 'database', 'postgres', 'postgresql',  # These are aliases, not real packages
            'frontend', 'backend', 'fullstack', 'app', 'application',
            'user', 'users', 'profile', 'dashboard', 'home',
            'build', 'deploy', 'start', 'dev', 'production'
        }
        
        # ========== SPECIAL CASE: Signup/Login Creation ==========
        # Auto-add auth dependencies when signup or login is being created
        is_auth_creation = any(phrase in edit_lower for phrase in [
            'create signup', 'create login', 'create auth', 'add signup', 'add login',
            'create sign up', 'signup page', 'login page', 'authentication',
            'add authentication', 'add auth', 'implement signup', 'implement sign up', 'add sign up', 'sign up page',
        ])
        
        if is_auth_creation:
            print(f"🔐 Auth creation detected - auto-adding auth dependencies")
            
            # Remove any invalid package entries that might exist
            for invalid in blacklist:
                if invalid in package_data["dependencies"]:
                    del package_data["dependencies"][invalid]
                    changes_made.append(f"Removed invalid entry: {invalid}")
                    print(f"  🗑️ Removed invalid entry: {invalid}")
            
            # Required auth dependencies
            auth_deps = {
                "bcryptjs": "^2.4.3",
                "jsonwebtoken": "^9.0.2",
                "@neondatabase/serverless": "^0.10.4"
            }
            
            for pkg, version in auth_deps.items():
                if pkg not in package_data["dependencies"]:
                    package_data["dependencies"][pkg] = version
                    changes_made.append(f"Added {pkg}@{version} to dependencies (auth required)")
                    print(f"  ✅ Added {pkg}@{version}")
            
            # Required dev dependencies
            auth_dev_deps = {
                "@types/bcryptjs": "^2.4.6",
                "@types/jsonwebtoken": "^9.0.7"
            }
            
            for pkg, version in auth_dev_deps.items():
                if pkg not in package_data["devDependencies"]:
                    package_data["devDependencies"][pkg] = version
                    changes_made.append(f"Added {pkg}@{version} to devDependencies (auth required)")
                    print(f"  ✅ Added {pkg}@{version}")
            
            if changes_made:
                updated_content = json_module.dumps(package_data, indent=2)
                return updated_content, changes_made
        
        # ========== DETECT OPERATION TYPE ==========
        is_removal = any(keyword in edit_lower for keyword in [
            'remove', 'delete', 'uninstall', 'drop', 'get rid of', 'eliminate'
        ])
        
        is_addition = any(keyword in edit_lower for keyword in [
            'add', 'install', 'include', 'append', 'insert'
        ]) or not is_removal
        
        # ========== EXTRACT PACKAGE NAMES FROM DESCRIPTION ==========
        package_patterns = [
            r'["\']([^"\']+)["\']',
            r'`([^`]+)`',
            r'@([a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_]+)',
            r'([a-zA-Z0-9\-_@/]+)(?:\s*@\s*[\d\.\^~]+)?'
        ]
        
        detected_packages = set()
        for pattern in package_patterns:
            matches = re.findall(pattern, edit_lower)
            for match in matches:
                pkg = match.strip().strip("'\"`")
                # Skip blacklisted words
                if pkg.lower() in blacklist:
                    continue
                if pkg and len(pkg) > 2 and pkg not in ['add', 'remove', 'delete', 'install', 'package', 'json']:
                    if not pkg.startswith(('http://', 'https://', 'file:')):
                        detected_packages.add(pkg)
        
        # Also clean up any existing invalid entries from package.json
        for invalid in blacklist:
            if invalid in package_data["dependencies"]:
                del package_data["dependencies"][invalid]
                changes_made.append(f"Removed invalid entry: {invalid}")
                print(f"  🗑️ Removed invalid entry: {invalid}")
        
        # Package name mapping for common references
        package_mapping = {
            'neon': '@neondatabase/serverless',
            'neondatabase': '@neondatabase/serverless',
            'neon database': '@neondatabase/serverless',
            'postgres': 'pg',
            'postgresql': 'pg',
            'jwt': 'jsonwebtoken',
            'json web token': 'jsonwebtoken',
            'bcrypt': 'bcryptjs',
            '@types/jwt': '@types/jsonwebtoken',
            '@types/bcrypt': '@types/bcryptjs',
        }
        
        # Apply mapping
        expanded_packages = set()
        for pkg in detected_packages:
            pkg_lower = pkg.lower()
            if pkg_lower in package_mapping:
                expanded_packages.add(package_mapping[pkg_lower])
            else:
                expanded_packages.add(pkg)
        
        detected_packages = expanded_packages
        
        # Package versions database
        package_versions = {
            "@neondatabase/serverless": "^0.10.4",
            "jsonwebtoken": "^9.0.2",
            "bcryptjs": "^2.4.3",
            "@types/jsonwebtoken": "^9.0.7",
            "@types/bcryptjs": "^2.4.6",
            "pg": "^8.11.3",
            "dotenv": "^16.3.1",
            "axios": "^1.6.0",
            "lodash": "^4.17.21",
        }
        
        # Execute additions or removals
        if is_removal:
            print(f"🗑️ Removing packages: {detected_packages}")
            for pkg in detected_packages:
                if pkg in package_data["dependencies"]:
                    del package_data["dependencies"][pkg]
                    changes_made.append(f"Removed {pkg} from dependencies")
                    print(f"  ✅ Removed {pkg}")
                
                if pkg in package_data["devDependencies"]:
                    del package_data["devDependencies"][pkg]
                    changes_made.append(f"Removed {pkg} from devDependencies")
                    print(f"  ✅ Removed {pkg} from devDependencies")
        else:
            print(f"📦 Adding packages: {detected_packages}")
            for pkg in detected_packages:
                is_dev = pkg.startswith('@types/') or 'types' in pkg.lower()
                version = package_versions.get(pkg, "^1.0.0")
                
                if is_dev:
                    if pkg not in package_data["devDependencies"]:
                        package_data["devDependencies"][pkg] = version
                        changes_made.append(f"Added {pkg}@{version} to devDependencies")
                        print(f"  ✅ Added {pkg} to devDependencies")
                else:
                    if pkg not in package_data["dependencies"]:
                        package_data["dependencies"][pkg] = version
                        changes_made.append(f"Added {pkg}@{version} to dependencies")
                        print(f"  ✅ Added {pkg} to dependencies")
        
        # Handle special requests
        if any(phrase in edit_lower for phrase in ['remove database', 'remove neon', 'remove @neondatabase']):
            for db_pkg in ['@neondatabase/serverless', 'pg']:
                if db_pkg in package_data["dependencies"]:
                    del package_data["dependencies"][db_pkg]
                    changes_made.append(f"Removed {db_pkg}")
                    print(f"  ✅ Removed {db_pkg}")
        
        if any(phrase in edit_lower for phrase in ['add database', 'add neon']):
            if '@neondatabase/serverless' not in package_data["dependencies"]:
                package_data["dependencies"]['@neondatabase/serverless'] = '^0.10.4'
                changes_made.append("Added @neondatabase/serverless")
                print(f"  ✅ Added @neondatabase/serverless")
        
        if changes_made:
            updated_content = json_module.dumps(package_data, indent=2)
            return updated_content, changes_made
        else:
            return None, []
            
    except Exception as e:
        print(f"❌ Package.json management error: {e}")
        return None, []



















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
        
        
        
        "null",  # ← ADD THIS - for local HTML files
        "blob:",  # ← ADD THIS - for preview iframes        
        
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)







# Image cache for storing downloaded images to avoid duplicate downloads
IMAGE_CACHE = {}













# ========== CLOUDINARY IMAGE CACHE FOR PREVIEWS ==========
CLOUDINARY_CACHE_DIR = Path("cloudinary_cache")
CLOUDINARY_CACHE_DIR.mkdir(exist_ok=True)




async def get_cloudinary_url_for_preview(file_key: str, content: str, project_files: Dict = None) -> str:
    """Upload image to Cloudinary and return URL (cached locally)"""
    import hashlib
    
    if not content or not content.startswith("__binary_base64__"):
        return None
    
    # Create a cache key based on the image content
    raw_b64 = content[len("__binary_base64__"):]
    cache_key = hashlib.md5(raw_b64.encode()).hexdigest()
    cache_file = CLOUDINARY_CACHE_DIR / f"{cache_key}.txt"
    
    # Check if already uploaded and cached
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached_url = f.read().strip()
            print(f"📸 Using cached Cloudinary URL for {file_key}")
            
            # ✅ Store the URL in project_files for database
            if project_files is not None:
                project_files["__cloudinary_image_url__"] = cached_url
            
            return cached_url
    
    try:
        print(f"☁️ Uploading {file_key} to Cloudinary...")
        
        # Clean base64 data
        if ',' in raw_b64 and raw_b64.startswith('data:'):
            raw_b64 = raw_b64.split(',')[1]
        raw_b64 = raw_b64.strip().replace('\n', '').replace('\r', '')
        
        # Generate a unique public ID
        public_id = f"preview_{cache_key[:16]}"
        
        upload_result = cloudinary.uploader.upload(
            f"data:image/jpeg;base64,{raw_b64}",
            folder="preview_images",
            public_id=public_id,
            overwrite=True,
            transformation=[
                {"quality": "auto:best"},
                {"fetch_format": "auto"},
                {"width": 1920, "height": 1080, "crop": "limit"}
            ]
        )
        
        cloudinary_url = upload_result['secure_url']
        
        # Cache the URL
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(cloudinary_url)
        
        print(f"✅ Uploaded and cached Cloudinary URL")
        
        # ✅ Store the URL in project_files for database
        if project_files is not None:
            project_files["__cloudinary_image_url__"] = cloudinary_url
            print(f"📸 Stored Cloudinary image URL in project_files")
        
        return cloudinary_url
        
    except Exception as e:
        print(f"❌ Failed to upload {file_key} to Cloudinary: {e}")
        return None
















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





















def preserve_cloudinary_urls(html_content: str, existing_files: Dict[str, Any]) -> str:
    """Preserve Cloudinary URLs from existing files"""
    import re
    
    # Look for image Cloudinary URL (image/upload, not raw/upload)
    image_cloudinary_url = None
    
    # Check for thumbnail_url first (this is the actual image)
    if 'thumbnail_url' in existing_files and existing_files['thumbnail_url']:
        image_cloudinary_url = existing_files['thumbnail_url']
        print(f"  📸 Found thumbnail_url: {image_cloudinary_url[:80]}...")
    
    # If no thumbnail_url, look for any image URL in files
    if not image_cloudinary_url and 'files' in existing_files:
        if 'thumbnail_url' in existing_files['files']:
            image_cloudinary_url = existing_files['files']['thumbnail_url']
    
    # If found thumbnail_url (image), use it
    if image_cloudinary_url and 'image/upload' in image_cloudinary_url:
        # Replace any incorrect src attributes
        html_content = re.sub(
            r'src="[^"]*?(?:image_1\.jpg|raw/upload[^"]*\.html)[^"]*"',
            f'src="{image_cloudinary_url}"',
            html_content
        )
        print(f"  ✅ Replaced with image Cloudinary URL")
    
    # Also fix onError syntax (JSX to HTML)
    html_content = re.sub(
        r'onError=\{\s*\(e\)\s*=>\s*\{[^}]+\}\s*\}',
        'onerror="this.style.display=\'none\'"',
        html_content
    )
    
    return html_content


























async def generate_preview_internal(files: Dict[str, Any], project_name: str, existing_image_url: str = None) -> Dict[str, Any]:
    import re  # ⭐ ADD THIS LINE - MUST BE FIRST
    """Generate beautiful HTML preview - extracts ALL pages and footer content"""
    try:
        print(f"🤖 AI generating beautiful HTML preview for: {project_name}")




























        # ========== ADD FONT AWESOME CDN TO HEAD ==========
        font_awesome_cdn = '''
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
        '''
        
        
        
          # ========== FUNCTION TO CONVERT FOOTER TO FONT AWESOME ==========
        def convert_footer_to_fontawesome(footer_html: str) -> str:
            """Convert Lucide icons in footer to Font Awesome icons"""
            if not footer_html:
                return footer_html
            
            # Map React/Lucide icon names to Font Awesome classes
            icon_map = {
                'Instagram': 'fab fa-instagram',
                'Facebook': 'fab fa-facebook',
                'Twitter': 'fab fa-twitter',
                'Mail': 'fas fa-envelope',
                'Phone': 'fas fa-phone',
                'MapPin': 'fas fa-map-marker-alt',
                'Send': 'fas fa-paper-plane',
                'Heart': 'fas fa-heart',
                'Sparkles': 'fas fa-sparkles',
            }
            
            # Replace <IconName /> with Font Awesome <i>
            for react_icon, fa_class in icon_map.items():
                # Handle <IconName /> pattern
                footer_html = re.sub(
                    rf'<{react_icon}\s*/>',
                    f'<i class="{fa_class} text-purple-400"></i>',
                    footer_html
                )
                # Handle <IconName></IconName> pattern
                footer_html = re.sub(
                    rf'<{react_icon}>\s*</{react_icon}>',
                    f'<i class="{fa_class} text-purple-400"></i>',
                    footer_html
                )
                # Handle <IconName className="..." />
                footer_html = re.sub(
                    rf'<{react_icon}\s+className="([^"]*)"\s*/>',
                    lambda m: f'<i class="{fa_class} {m.group(1)} text-purple-400"></i>',
                    footer_html
                )
            
            return footer_html
















        def convert_navigation_to_html(nav_content: str, brand_name: str, nav_links: list) -> str:
            """Convert Next.js Navigation component to HTML with Lucide icons - with cart badge support"""
            
            # ========== DYNAMIC ICON EXTRACTION ==========
            icon_name = "Sparkles"  # default
            icon_size = "w-8 h-8"
            icon_color = "text-purple-500"
            
            # Method 1: Extract from JSX with any className pattern
            jsx_pattern = r'<(\w+)\s+className="([^"]*)"'
            jsx_matches = re.findall(jsx_pattern, nav_content)
            for match in jsx_matches:
                potential_icon = match[0]
                class_str = match[1]
                # Check if it's likely an icon (not a div or span)
                if potential_icon[0].isupper() and len(potential_icon) > 1:
                    icon_name = potential_icon
                    # Extract size from className
                    size_match = re.search(r'w-(\d+)\s+h-(\d+)', class_str)
                    if size_match:
                        icon_size = f"w-{size_match.group(1)} h-{size_match.group(2)}"
                    # Extract color from className
                    color_match = re.search(r'text-(\w+-\d+)', class_str)
                    if color_match:
                        icon_color = f"text-{color_match.group(1)}"
                    break
            
            # Method 2: Extract from imports if JSX extraction failed
            if icon_name == "Sparkles":
                import_match = re.search(r'import\s+\{\s*(\w+)\s*\}\s+from\s+[\'"]lucide-react[\'"]', nav_content)
                if import_match:
                    icon_name = import_match.group(1)
            
            print(f"🎨 Extracted icon: {icon_name}")
            print(f"   Size: {icon_size}")
            print(f"   Color: {icon_color}")
            
            # Map icon name to Lucide data-lucide attribute
            lucide_icon = icon_name.lower()
            special_mappings = {
                "graduationcap": "graduation-cap",
                "shoppingbag": "shopping-bag",
                "shoppingcart": "shopping-cart",
                "sparkles": "sparkles",
                "dumbbell": "dumbbell",
            }
            lucide_icon = special_mappings.get(lucide_icon, lucide_icon)
            
            # Extract brand text gradient className
            brand_text_class = "text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent"
            text_match = re.search(r'<span[^>]*className="([^"]*)"[^>]*>[^<]*</span>', nav_content)
            if text_match:
                brand_text_class = text_match.group(1)
            
            # ========== BUILD NAVIGATION BUTTONS WITH CART BADGE SUPPORT ==========
            nav_buttons_html = ""
            cart_link_html = ""  # Store cart link separately for badge
            print(f"📋 Building navigation for {len(nav_links)} links: {nav_links}")
            
            # E-commerce keywords that should have icons
            ECOMMERCE_KEYWORDS = ["shop", "store", "catalog", "catalogue", "cart", "basket", "products", "checkout"]
            
            for href, label in nav_links:
                label_lower = label.lower()
                
                # Check if this is the CART link (special handling for badge)
                is_cart = 'cart' in label_lower or href == '/cart'
                
                # Check if this is an e-commerce link (should have icon)
                is_ecommerce = any(keyword in label_lower for keyword in ECOMMERCE_KEYWORDS)
                
                if is_cart:
                    # Special cart link WITH badge
                    if "shop" in label_lower or "store" in label_lower:
                        item_icon = "shopping-bag"
                    elif "catalog" in label_lower or "catalogue" in label_lower:
                        item_icon = "grid"
                    else:
                        item_icon = "shopping-cart"
                    
                    base_color = icon_color.replace('500', '400') if '500' in icon_color else icon_color
                    hover_color = icon_color.replace('500', '600') if '500' in icon_color else icon_color
                    
                    cart_link_html = f'''
                        <a href="{href}" class="nav-link relative flex items-center gap-2 group" data-page="{href.replace('/', '')}">
                            <i data-lucide="{item_icon}" class="w-4 h-4 {base_color} group-hover:{hover_color} group-hover:scale-110 transition-all duration-300"></i>
                            <span class="text-gray-300 group-hover:{icon_color} transition-colors duration-300">{label}</span>
                            <span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1 shadow-lg shadow-purple-500/25">0</span>
                        </a>'''
                elif is_ecommerce:
                    # Regular e-commerce link WITH icon (no badge)
                    if "shop" in label_lower or "store" in label_lower:
                        item_icon = "shopping-bag"
                    elif "catalog" in label_lower or "catalogue" in label_lower:
                        item_icon = "grid"
                    elif "products" in label_lower:
                        item_icon = "package"
                    elif "checkout" in label_lower:
                        item_icon = "credit-card"
                    else:
                        item_icon = "circle"
                    
                    base_color = icon_color.replace('500', '400') if '500' in icon_color else icon_color
                    hover_color = icon_color.replace('500', '600') if '500' in icon_color else icon_color
                    
                    nav_buttons_html += f'''
                        <a href="{href}" class="nav-link flex items-center gap-2 group" data-page="{href.replace('/', '')}">
                            <i data-lucide="{item_icon}" class="w-4 h-4 {base_color} group-hover:{hover_color} group-hover:scale-110 transition-all duration-300"></i>
                            <span class="text-gray-300 group-hover:{icon_color} transition-colors duration-300">{label}</span>
                        </a>'''
                else:
                    # Build non-e-commerce link WITHOUT icon (text only)
                    nav_buttons_html += f'''
                        <a href="{href}" class="nav-link group" data-page="{href.replace('/', '')}">
                            <span class="text-gray-300 group-hover:{icon_color} transition-colors duration-300">{label}</span>
                        </a>'''
            
            # ========== GENERATE MOBILE NAV BUTTONS WITH CART BADGE ==========
            mobile_nav_html = nav_buttons_html.replace('class="nav-link flex items-center gap-2 group"', 'class="mobile-nav-link flex items-center gap-3 group w-full px-4 py-2 rounded-lg hover:bg-white/10"')
            mobile_nav_html = mobile_nav_html.replace('class="nav-link group"', 'class="mobile-nav-link block w-full px-4 py-2 rounded-lg hover:bg-white/10"')
            
            # Add mobile cart link with badge
            mobile_cart_html = f'''
                        <div class="flex items-center justify-between w-full px-4 py-2 rounded-lg hover:bg-white/10">
                            <a href="/cart" class="mobile-nav-link flex items-center gap-3" data-page="cart">
                                <i data-lucide="shopping-cart" class="w-4 h-4 {icon_color}"></i>
                                <span class="text-gray-300">Cart</span>
                            </a>
                            <span data-cart-count class="cart-count-badge hidden bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1">0</span>
                        </div>'''
            
            # ========== GENERATE FINAL NAVIGATION HTML ==========
            return f'''
                    <nav class="flex justify-between items-center p-6 container mx-auto sticky top-0 z-50 bg-black/80 backdrop-blur-lg border-b border-white/10">
                        <a href="/" class="brand flex items-center gap-2 group" onclick="handleBrandClick(event)">
                            <i data-lucide="{lucide_icon}" class="{icon_size} {icon_color} drop-shadow-lg group-hover:scale-110 transition-all duration-300"></i>
                            <span class="{brand_text_class}">{brand_name}</span>
                        </a>
                        <div class="hidden md:flex space-x-2 items-center">
                            {nav_buttons_html}
                            {cart_link_html}
                        </div>
                        <button id="mobile-menu-button" class="md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors">
                            <i data-lucide="menu" class="{icon_size.replace('w-8', 'w-6')} {icon_color}"></i>
                        </button>
                    </nav>
                    
                    <div id="mobile-menu" class="hidden md:hidden bg-black/80 backdrop-blur-lg p-4 space-y-2 border-t border-white/10">
                        {mobile_nav_html}
                        {mobile_cart_html}
                    </div>
                    
                    <style>
                        /* Cart Badge Animation */
                        .cart-count-badge {{
                            animation: bounceIn 0.3s ease-out;
                        }}
                        @keyframes bounceIn {{
                            0% {{ transform: scale(0); opacity: 0; }}
                            50% {{ transform: scale(1.2); }}
                            100% {{ transform: scale(1); opacity: 1; }}
                        }}
                    </style>
                    
                    <script>
                        document.getElementById('mobile-menu-button')?.addEventListener('click', function() {{
                            const menu = document.getElementById('mobile-menu');
                            if (menu) menu.classList.toggle('hidden');
                        }});
                        lucide.createIcons();
                    </script>
                    '''
                    
                    
                    
                    
                    
                    
                    











        def clean_onError_handlers(html: str) -> str:
            """Convert string onError handlers to actual JavaScript"""
            import re
            
            # Count how many fixes were made
            fixes_count = 0
            
            # ⭐ NEW: Fix broken onError that appears as text with double braces
            # Pattern: onError="{{ (e) => { ... } }}" 
            pattern0 = r'onError="\{\{\s*\(e\)\s*=>\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\s*\}\}"'
            html, count = re.subn(pattern0, r'onError={(e) => { \1 }}', html)
            fixes_count += count
            
            # Fix pattern with optional chaining and double braces
            pattern0b = r'onError="\{\{\s*\(e\)\s*=>\s*\{([^}]+?\.parentElement\?\.classList[^}]+)\}\s*\}\}"'
            html, count = re.subn(pattern0b, r'onError={(e) => { \1 }}', html)
            fixes_count += count
            
            # Fix pattern: onError="{(e) => { ... }}"
            pattern = r'onError="\{\(e\)\s*=>\s*\{([^}]+)\}\}"'
            html, count = re.subn(pattern, r'onError={(e) => { \1 }}', html)
            fixes_count += count
            
            # Fix any onError with quotes
            pattern2 = r'onError="([^"]+)"'
            def fix_handler(match):
                handler = match.group(1)
                handler = handler.strip()
                if handler.startswith('{') and handler.endswith('}'):
                    handler = handler[1:-1]
                return f'onError={{{handler}}}'
            html, count = re.subn(pattern2, fix_handler, html)
            fixes_count += count
            
            # Fix escaped characters
            html = html.replace('&quot;', '"')
            html = html.replace('&#39;', "'")
            html = html.replace('&#123;', '{')
            html = html.replace('&#125;', '}')
            
            # Fix double braces
            html, count = re.subn(r'onError=\{\{(.+?)\}\}', r'onError={\1}', html)
            fixes_count += count
            
            # ⭐ NEW: Remove any remaining broken onError that might render as text
            html = re.sub(
                r'onError="[^"]*parentElement\?\.classList[^"]*"\s*/>',
                'onError={(e) => { e.currentTarget.style.display = "none"; }} />',
                html
            )
            
            if fixes_count > 0:
                print(f"🔧 Fixed {fixes_count} onError handler(s) in preview HTML")
            
            return html
























        # ========== COLLECT NAVIGATION ==========
        nav_links = []
        nav_content = ""
        brand_name = project_name
        
        nav_paths = [
            "components/Navigation.tsx",
            "components/Navigation.jsx", 
            "components/Navbar.tsx",
            "components/Navbar.jsx",
            "app/components/Navigation.tsx",
            "components/Header.tsx"
        ]
        
        for fp in nav_paths:
            if fp in files:
                nav_content = files[fp]
                break
        
        if not nav_content:
            for fp, content in files.items():
                if any(x in fp for x in ["Navigation", "Navbar", "Header"]) and fp.endswith((".tsx", ".jsx")):
                    nav_content = content
                    break
        
        # ========== EXTRACT BRAND AND NAVIGATION LINKS ==========
        print(f"🔍 DEBUG - nav_content length: {len(nav_content) if nav_content else 0}")
        print(f"🔍 DEBUG - nav_content preview: {nav_content[:500] if nav_content else 'EMPTY'}")
        
        if nav_content:
            brand_patterns = [
                r'<Link\s+href="/"[^>]*>(.*?)</Link>',
                r'<div\s+className="[^"]*brand[^"]*"[^>]*>(.*?)</div>',
            ]
            for pattern in brand_patterns:
                match = re.search(pattern, nav_content, re.DOTALL)
                if match:
                    brand_name = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                    if brand_name:
                        break
            
            # Extract ALL hrefs first (captures cart with icon)
            href_pattern = r'<Link\s+href="/([^"]+)"'
            all_hrefs = re.findall(href_pattern, nav_content)
            href_pattern2 = r"<Link\s+href='/([^']+)'"
            all_hrefs.extend(re.findall(href_pattern2, nav_content))
            
            print(f"🔍 Found hrefs: {all_hrefs}")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_hrefs = []
            for href in all_hrefs:
                if href not in seen:
                    seen.add(href)
                    unique_hrefs.append(href)
            
            print(f"🔍 Unique hrefs: {unique_hrefs}")
            
            # Generate labels from hrefs
            for href in unique_hrefs:
                if href != "/" and href.lower() != brand_name.lower():
                    # Try to extract label from the link content first
                    label_pattern = rf'<Link\s+href="/{href}"[^>]*>(.*?)</Link>'
                    label_match = re.search(label_pattern, nav_content, re.DOTALL)
                    if label_match:
                        label_content = label_match.group(1)
                        # Remove icon tags to get text
                        clean_label = re.sub(r'<[^>]+>', '', label_content).strip()
                        if clean_label:
                            label = clean_label
                        else:
                            label = href.capitalize()
                    else:
                        label = href.capitalize()
                    
                    nav_links.append((href, label))
                    print(f"🔍 Added link: {href} -> {label}")
            
            # If still no links, fallback to old patterns
            if not nav_links:
                link_patterns = [
                    r'<Link\s+href="/([^"]+)"[^>]*>([^<]+)</Link>',
                    r'<Link\s+href=\'/([^\']+)\'[^>]*>([^<]+)</Link>',
                ]
                for pattern in link_patterns:
                    matches = re.findall(pattern, nav_content, re.DOTALL)
                    for href, text in matches:
                        clean_text = re.sub(r'<[^>]+>', '', text).strip()
                        if href and clean_text and href != "/" and clean_text.lower() != brand_name.lower():
                            nav_links.append((href, clean_text))
                    if nav_links:
                        break
        
        if not nav_links:
            nav_links = [("shop", "Shop"), ("catalog", "Catalog"), ("cart", "Cart")]
            print("🔍 Using default nav_links")

        print(f"📍 Navigation: {brand_name} -> {nav_links}")
        
        # ========== CONVERT NAVIGATION TO HTML ==========
        navigation_html = convert_navigation_to_html(nav_content, brand_name, nav_links)
        navigation_html_for_prompt = navigation_html












        
        # ========== EXTRACT FOOTER CONTENT ==========
        footer_html = ""
        footer_paths = [
            "components/Footer.tsx",
            "components/Footer.jsx",
            "app/components/Footer.tsx",
        ]
        
        for fp in footer_paths:
            if fp in files:
                footer_content = files[fp]
                # Extract the JSX return content
                match = re.search(r'return\s*\(\s*([\s\S]*?)\s*\)\s*;', footer_content)
                if match:
                    footer_html = match.group(1)
                else:
                    footer_html = footer_content
                
                # Convert JSX to HTML
                footer_html = re.sub(r'className=', 'class=', footer_html)
                footer_html = re.sub(r'<Link\s+href="([^"]+)"[^>]*>', r'<a href="\1">', footer_html)
                footer_html = re.sub(r'</Link>', '</a>', footer_html)
                
                # Convert icons to Font Awesome
                footer_html = convert_footer_to_fontawesome(footer_html)
                print(f"✅ Footer extracted and converted to Font Awesome")
                break
        
        # If no footer found, use default
        if not footer_html:
            from datetime import datetime
            footer_html = f'''
            <footer class="bg-zinc-950 border-t border-zinc-800 py-12">
                <div class="container mx-auto grid md:grid-cols-4 gap-8 px-4">
                    <div>
                        <h4 class="font-bold mb-4">{brand_name}</h4>
                        <p class="text-sm text-gray-400">Premium lifestyle goods.</p>
                    </div>
                    <div>
                        <h4 class="font-bold mb-4">Links</h4>
                        <p class="text-sm text-gray-400">Shop | Catalog | Cart</p>
                    </div>
                    <div>
                        <h4 class="font-bold mb-4">Contact</h4>
                        <p class="text-sm text-gray-400">info@{brand_name.lower().replace(' ', '')}.com</p>
                    </div>
                    <div class="flex gap-4">
                        <i class="fab fa-instagram text-gray-400 hover:text-purple-400"></i>
                        <i class="fab fa-facebook text-gray-400 hover:text-purple-400"></i>
                        <i class="fab fa-twitter text-gray-400 hover:text-purple-400"></i>
                    </div>
                </div>
                <div class="text-center mt-8 text-sm text-gray-600">
                    © {datetime.now().year} {brand_name}. Crafted with <i class="fas fa-heart text-red-400"></i> in Nairobi
                </div>
            </footer>
            '''
        
        # ========== INCLUDE FONT AWESOME CDN IN PREVIEW ==========
        # Make sure to add this to your final preview HTML <head> section
        font_awesome_cdn = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">'
        
        # Continue with the rest of your preview generation...
        # Make sure to add {font_awesome_cdn} to your <head> section






















        # ========== EXTRACT FOOTER CONTENT ==========
        footer_html = ""
        footer_paths = [
            "components/Footer.tsx",
            "components/Footer.jsx",
            "app/components/Footer.tsx",
            "components/Footer/index.tsx",
            "components/Layout/Footer.tsx"
        ]
        
        for fp in footer_paths:
            if fp in files:
                content = files[fp]
                # Remove 'use client' and imports first
                clean_footer = re.sub(r'^["\']use client["\'];\s*$', '', content, flags=re.MULTILINE)
                clean_footer = re.sub(r'^import\s+.*?from\s+["\'][^"\']+["\'];\s*$', '', clean_footer, flags=re.MULTILINE)
                
                # Extract JSX return content
                match = re.search(r'return\s*\(\s*([\s\S]*?)\s*\)\s*;', clean_footer, re.DOTALL)
                if match:
                    footer_html = match.group(1)
                else:
                    match = re.search(r'<footer[\s\S]*?</footer>', content, re.DOTALL)
                    if match:
                        footer_html = match.group(0)
                
                if footer_html:
                    # Clean up footer HTML (preserve content)
                    footer_html = re.sub(r'className=', 'class=', footer_html)
                    footer_html = re.sub(r'<Link\s+href="([^"]+)"[^>]*>', r'<a href="\1">', footer_html)
                    footer_html = re.sub(r'</Link>', '</a>', footer_html)
                    footer_html = re.sub(r'\s+key=["\'][^"\']*["\']', '', footer_html)
                    # Don't remove curly braces in footer
                    # footer_html = re.sub(r'\{[^}]+\}', '', footer_html)  # COMMENTED OUT
                    print(f"✅ Footer extracted: {len(footer_html)} chars")
                    break
        
        
        
        
        
        
        
        
        
        



        
        
        
        
        
        
        
        # ========== EXTRACT ALL PAGE CONTENTS ==========
        page_contents = {}
        
        
        
        
















              # Helper function to extract content from TSX/JSX files
        def extract_page_content(content: str, route_name: str) -> str:
            """Extract meaningful content from page component - captures ALL sections including arrays and maps"""
            print(f"\n{'='*60}")
            print(f"🔍 EXTRACTING: {route_name}")
            print(f"{'='*60}")
            print(f"📦 Original content length: {len(content)} chars")
            
            if not content:
                  print(f"❌ Content is empty!")
                  return ""
            
            # Remove imports and exports (but keep the JSX structure)
            print(f"\n📌 STEP 1: Removing imports and exports...")
            clean = re.sub(r'^import\s+.*?from\s+["\'][^"\']+["\'];\s*$', '', content, flags=re.MULTILINE)
            clean = re.sub(r'^export\s+default\s+\w+;?\s*$', '', clean, flags=re.MULTILINE)
            clean = re.sub(r'^export\s+const\s+\w+\s*=\s*', '', clean, flags=re.MULTILINE)
            clean = re.sub(r'^export\s+function\s+\w+\s*\([^)]*\)\s*{?', '', clean, flags=re.MULTILINE)
            print(f"   ✅ Length after import removal: {len(clean)} chars")
            
            # Remove 'use client' directive
            print(f"\n📌 STEP 2: Removing 'use client' directive...")
            clean = re.sub(r'^["\']use client["\'];\s*$', '', clean, flags=re.MULTILINE)
            print(f"   ✅ Length after 'use client' removal: {len(clean)} chars")
            
            # ⭐ NEW: Check for image in cleaned content
            if 'image_1.jpg' in clean or 'image_' in clean:
                  print(f"   ✅ Image found in cleaned content")
            
            # Check for key sections in cleaned content
            print(f"\n📌 STEP 3: Checking for key sections in cleaned content...")
            if 'Our Core Pillars' in clean or 'Core Features' in clean:
                  print(f"   ✅ Features/Pillars section FOUND")
                  features_pos = clean.find('Our Core Pillars') if 'Our Core Pillars' in clean else clean.find('Core Features')
                  print(f"   📍 Section at position: {features_pos}")
                  print(f"   📄 Preview around section:")
                  print(f"      {clean[features_pos-50:features_pos+100]}...")
            else:
                  print(f"   ❌ Features/Pillars section NOT FOUND")
            
            # Check for inline array
            print(f"\n📌 STEP 4: Checking for inline array (.map())...")
            if '.map(' in clean:
                  print(f"   ✅ .map() found in cleaned content")
            else:
                  print(f"   ❌ .map() NOT found in cleaned content")
            
            # Extract return JSX using bracket counting
            print(f"\n📌 STEP 5: Extracting return JSX...")
            start_match = re.search(r'return\s*\(', clean)
            if not start_match:
                  start_match = re.search(r'return\s+', clean)
                  if not start_match:
                        print(f"   ❌ No return statement found!")
                        return f'<div class="container"><h1 class="gradient-text">{route_name.replace("_", " ").title()}</h1></div>'
            
            print(f"   ✅ Return statement found at position {start_match.start()}")
            start_pos = start_match.end()
            print(f"   📍 Start position: {start_pos}")
            
            # Count brackets to find the matching closing parenthesis
            open_count = 1
            i = start_pos
            extracted = ""
            bracket_count = 0
            
            print(f"   🔄 Counting brackets to find matching closing parenthesis...")
            while i < len(clean) and open_count > 0:
                  char = clean[i]
                  extracted += char
                  if char == '(':
                        open_count += 1
                        bracket_count += 1
                  elif char == ')':
                        open_count -= 1
                        bracket_count += 1
                  i += 1
            
            print(f"   ✅ Extraction complete. Processed {bracket_count} brackets")
            print(f"   📏 Extracted length: {len(extracted)} chars")
            
            # ⭐ CRITICAL FIX: DO NOT truncate at semicolons!
            print(f"   📏 Keeping full extracted content (no semicolon truncation): {len(extracted)} chars")
            
            extracted = extracted.strip()
            print(f"   📏 Final extracted length: {len(extracted)} chars")
            
            # ⭐ Check if image was preserved in extracted content
            if 'image_1.jpg' in extracted:
                  print(f"   ✅ Image preserved in extracted content")
            else:
                  print(f"   ⚠️ Image NOT found in extracted content")
            
            # Show preview of extracted content
            print(f"\n📌 STEP 6: Preview of extracted content (first 500 chars):")
            print(f"{'-'*60}")
            print(extracted[:500])
            print(f"{'-'*60}")
            
            if extracted:
                  # Process inline arrays inside JSX
                  print(f"\n📌 STEP 7: Processing inline arrays...")
                  
                  # Find and render the pillars/features array
                  array_pattern = r'\{\s*\[([\s\S]*?)\]\s*\.map\(\(([^,]+),\s*([^)]+)\)\s*=>\s*\(\s*([\s\S]*?)\s*\)\s*\)\s*\}'
                  
                  def render_array(match):
                        array_items_str = match.group(1)
                        item_var = match.group(2).strip()
                        index_var = match.group(3).strip()
                        template = match.group(4).strip()
                        
                        print(f"      📦 Found array with {array_items_str.count('title:')} items")
                        print(f"      🏷️ Item variable: {item_var}, Index variable: {index_var}")
                        
                        items = []
                        object_pattern = r'\{\s*title:\s*["\']([^"\']+)["\']\s*,\s*desc:\s*["\']([^"\']+)["\']\s*\}'
                        object_matches = re.findall(object_pattern, array_items_str)
                        
                        for title, desc in object_matches:
                              items.append({"title": title, "desc": desc})
                              print(f"         📌 Item: '{title}' -> '{desc[:40]}...'")
                        
                        if items:
                              rendered_items = []
                              for idx, item in enumerate(items):
                                    rendered_html = template
                                    rendered_html = rendered_html.replace(f'{{{item_var}.title}}', item['title'])
                                    rendered_html = rendered_html.replace(f'{{{item_var}.desc}}', item['desc'])
                                    rendered_html = rendered_html.replace(f'{{{index_var}}}', str(idx))
                                    rendered_items.append(rendered_html)
                                    # Fix icon class for ShieldCheck
                                    rendered_html = rendered_html.replace('fa-shield-check', 'fa-shield-alt')
                              
                              print(f"      ✅ Rendered {len(rendered_items)} items")
                              return '\n'.join(rendered_items)
                        
                        return match.group(0)
                  
                  extracted = re.sub(array_pattern, render_array, extracted, flags=re.DOTALL)
                  
                  if '.map(' in extracted:
                        print(f"   ⚠️ Some .map() patterns may not have been processed")
                  
                  # Convert JSX to HTML
                  print(f"\n📌 STEP 8: Converting JSX to HTML...")
                  extracted = re.sub(r'className=', 'class=', extracted)
                  
                  
                  extracted = extracted.replace('fa-shield-check', 'fa-shield-alt')
                  
                  
                  extracted = re.sub(r'htmlFor=', 'for=', extracted)
                  extracted = re.sub(r'<Link\s+href="([^"]+)"[^>]*>', r'<a href="\1">', extracted)
                  extracted = re.sub(r'<Link\s+href=\'([^\']+)\'[^>]*>', r'<a href="\1">', extracted)
                  extracted = re.sub(r'</Link>', '</a>', extracted)
                  extracted = re.sub(r'<Image\s+src="([^"]+)"[^>]*/?>', r'<img src="\1" alt="" />', extracted)
                  extracted = re.sub(r'<Image\s+src=\'([^\']+)\'[^>]*/?>', r'<img src="\1" alt="" />', extracted)
                  extracted = re.sub(r'<>', '<div>', extracted)
                  extracted = re.sub(r'</>', '</div>', extracted)
                  extracted = re.sub(r'\s+key=["\'][^"\']*["\']', '', extracted)
                  extracted = re.sub(r'\s+priority\s*', '', extracted)
                  extracted = re.sub(r'\s+loading="lazy"\s*', '', extracted)
                  extracted = re.sub(r'<Fragment>', '', extracted)
                  extracted = re.sub(r'</Fragment>', '', extracted)
                  extracted = re.sub(r'>\s+<', '><', extracted)
                  extracted = re.sub(r'\n{3,}', '\n\n', extracted)
                  
                  # ⭐ FINAL CHECK: If image was lost, manually inject it
                  if 'image_1.jpg' not in extracted and 'image_' in str(files.keys()):
                        print(f"\n   🔧 Image lost during conversion - manually injecting...")
                        # Find the hero section and add the image
                        if '<section class="relative h-screen' in extracted:
                              # Inject image right after section opening
                              image_tag = '<img src="/images/image_1.jpg" alt="Hero background" class="absolute inset-0 w-full h-full object-cover" />'
                              extracted = extracted.replace(
                                    '<section class="relative h-screen',
                                    f'<section class="relative h-screen">{image_tag}'
                              )
                              # Also add the dark overlay
                              overlay = '<div class="absolute inset-0 bg-black/50"></div>'
                              extracted = extracted.replace(image_tag, f'{image_tag}\n    {overlay}')
                              print(f"   ✅ Image injected into hero section")
                  
                  # Final verification
                  print(f"\n📌 STEP 9: Final verification...")
                  if 'Core Features' in extracted or 'Our Core Pillars' in extracted:
                        print(f"   ✅ Features/Pillars section present in final extracted content")
                        card_count = extracted.count('rounded-xl')
                        print(f"   📊 Cards found: {card_count}")
                        
                        if card_count >= 3:
                              print(f"   ✅ All features successfully extracted!")
                  else:
                        print(f"   ❌ Features section MISSING from final extracted content!")
                  
                  # ⭐ Final image check
                  if 'image_1.jpg' in extracted:
                        print(f"   ✅ Image present in final output!")
                  else:
                        print(f"   ⚠️ Image missing from final output!")
                  
                  print(f"\n✅ Extraction complete for {route_name}")
                  print(f"{'='*60}\n")
                  return extracted.strip()
            
            
            
            
            
            
            
            
            
            print(f"❌ No JSX extracted, using fallback")
            return f'<div class="container"><h1 class="gradient-text">{route_name.replace("_", " ").title()}</h1><p>Content from {route_name}</p></div>'
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # Scan all files for page components
        for file_path, content in files.items():
            # Match Next.js page patterns
            if file_path.endswith((".tsx", ".jsx", ".js")) and ("/app/" in file_path or file_path.startswith("app/")):
                # Skip non-page files
                if "layout" in file_path.lower() or "error" in file_path.lower() or "loading" in file_path.lower():
                    continue
                
                # Extract route name
                route = file_path.replace("app/", "").replace("/page.tsx", "").replace("/page.jsx", "").replace("/page.js", "")
                route = route.replace(".tsx", "").replace(".jsx", "").replace(".js", "")
                route_name = route if route else "home"
                route_name = route_name.replace("/", "_")
                
                print(f"\n📄 Found page: {file_path} -> {route_name}")
                

                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                extracted_content = extract_page_content(content, route_name)
                
                
                
                
                
                
                
                
                # ========== DEBUG: Log extracted content for home page ==========
                if route_name == 'page' or route_name == 'home':
                    print(f"\n{'='*60}")
                    print(f"🔍 DEBUGGING EXTRACTED CONTENT FOR HOME PAGE")
                    print(f"{'='*60}")
                    print(f"📏 Extracted content length: {len(extracted_content)} chars")
                    print(f"\n📄 FIRST 500 CHARACTERS:")
                    print("-" * 40)
                    print(extracted_content[:500])
                    print("-" * 40)
                    
                    print(f"\n🔎 SEARCHING FOR KEY SECTIONS:")
                    print("-" * 40)
                    
                    # Check for hero section
                    if 'relative h-screen' in extracted_content or 'hero' in extracted_content.lower():
                        print("✅ Hero section found")
                    else:
                        print("❌ Hero section MISSING")
                    
                    # Check for features section
                    if 'Our Features' in extracted_content:
                        print("✅ 'Our Features' heading found")
                    else:
                        print("❌ 'Our Features' heading MISSING")
                    
                    # Check for grid
                    if 'grid md:grid-cols-3' in extracted_content:
                        print("✅ Grid container found")
                    else:
                        print("❌ Grid container MISSING")
                    
                    # Check for individual feature cards
                    card_count = extracted_content.count('rounded-xl bg-white/5')
                    print(f"📊 Feature cards found: {card_count}")
                    
                    # Check for specific feature titles
                    if 'Cloud Analytics' in extracted_content:
                        print("✅ 'Cloud Analytics' found")
                    else:
                        print("❌ 'Cloud Analytics' MISSING")
                    
                    if 'Team Sync' in extracted_content:
                        print("✅ 'Team Sync' found")
                    else:
                        print("❌ 'Team Sync' MISSING")
                    
                    if 'Security First' in extracted_content:
                        print("✅ 'Security First' found")
                    else:
                        print("❌ 'Security First' MISSING")
                    
                    # Check if the inline array pattern exists
                    if 'map((f, i)' in extracted_content or '.map(' in extracted_content:
                        print("⚠️ Raw .map() still present (not rendered)")
                        # Find and show the map pattern
                        import re
                        map_match = re.search(r'\{[^}]*\.map\([^)]*\)[^}]*\}', extracted_content)
                        if map_match:
                            print(f"   Map pattern found: {map_match.group(0)[:150]}...")
                    else:
                        print("✅ No raw .map() found (should be rendered)")
                    
                    # Check for any JavaScript expressions left
                    if '{' in extracted_content and '}' in extracted_content:
                        # Count remaining JS expressions
                        js_exprs = re.findall(r'\{[^{}]*\}', extracted_content)
                        if js_exprs:
                            print(f"⚠️ Remaining JS expressions: {len(js_exprs)}")
                            for expr in js_exprs[:3]:
                                print(f"   - {expr[:80]}")
                    
                    print(f"\n📄 LAST 500 CHARACTERS:")
                    print("-" * 40)
                    print(extracted_content[-500:])
                    print("-" * 40)
                    print(f"{'='*60}\n")
                               
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
             # ========== ADD THIS AUTH OVERRIDE RIGHT HERE ==========
                # Override signup/login pages with backend HTML forms
                if route_name in ['signup', 'login', 'auth']:
                    if route_name == 'signup':
                        page_contents[route_name] = '''
                        <div class="min-h-screen flex items-center justify-center py-12 px-4">
                            <div class="max-w-md w-full space-y-8 bg-white/5 backdrop-blur-sm p-8 rounded-2xl border border-white/10">
                                <div>
                                    <h2 class="text-center text-3xl font-extrabold text-white">Create your account</h2>
                                    <p class="mt-2 text-center text-sm text-gray-400">
                                        Already have an account? <a href="#" onclick="showPage('login'); return false;" class="font-medium text-purple-400 hover:text-purple-300">Sign in</a>
                                    </p>
                                </div>
                                <form id="signup-form" class="mt-8 space-y-6">
                                    <div class="space-y-4">
                                        <div>
                                            <input type="text" name="name" required placeholder="Full name" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                        <div>
                                            <input type="email" name="email" required placeholder="Email address" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                        <div>
                                            <input type="password" name="password" required placeholder="Password (min. 6 characters)" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                        <div>
                                            <input type="password" name="confirmPassword" required placeholder="Confirm password" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                    </div>
                                    <button type="submit" class="w-full flex justify-center py-3 px-4 text-sm font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">Sign up</button>
                                </form>
                            </div>
                        </div>
                        '''
                        print(f"  ✅ Using backend HTML form for signup")
                    elif route_name == 'login':
                        page_contents[route_name] = '''
                        <div class="min-h-screen flex items-center justify-center py-12 px-4">
                            <div class="max-w-md w-full space-y-8 bg-white/5 backdrop-blur-sm p-8 rounded-2xl border border-white/10">
                                <div>
                                    <h2 class="text-center text-3xl font-extrabold text-white">Sign in to your account</h2>
                                    <p class="mt-2 text-center text-sm text-gray-400">
                                        Or <a href="#" onclick="showPage('signup'); return false;" class="font-medium text-purple-400 hover:text-purple-300">create a new account</a>
                                    </p>
                                </div>
                                <form id="login-form" class="mt-8 space-y-6">
                                    <div class="space-y-4">
                                        <div>
                                            <input type="email" name="email" required placeholder="Email address" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                        <div>
                                            <input type="password" name="password" required placeholder="Password" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                    </div>
                                    <button type="submit" class="w-full flex justify-center py-3 px-4 text-sm font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">Sign in</button>
                                </form>
                            </div>
                        </div>
                        '''
                        print(f"  ✅ Using backend HTML form for login")
                # ========== END OF AUTH OVERRIDE ==========
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                # ========== CHANGE THIS PART - USE ELIF ==========
                elif extracted_content and len(extracted_content) > 50:
                    page_contents[route_name] = extracted_content[:1000000]  # Limit size
                    print(f"  ✅ Extracted {len(extracted_content)} chars")
                else:
                    # Create meaningful fallback content based on route name
                    display_name = route_name.replace("_", " ").title()
                    page_contents[route_name] = f'''
                    <div class="container">
                        <div class="hero" style="min-height: 40vh; margin: 2rem;">
                            <div class="hero-content">
                                <h1 class="gradient-text">{display_name}</h1>
                                <p>Welcome to our {display_name.lower()} page. Explore what we have to offer.</p>
                                <button class="btn" onclick="showPage('home')">Back to Home</button>
                            </div>
                        </div>
                        <div class="grid">
                            <div class="card">
                                <h3>About {display_name}</h3>
                                <p>Learn more about our {display_name.lower()} offerings and how we can help you.</p>
                                <button class="btn" style="margin-top: 1rem;">Learn More</button>
                            </div>
                            <div class="card">
                                <h3>Our {display_name} Services</h3>
                                <p>Discover the range of services we provide in {display_name.lower()}.</p>
                                <button class="btn" style="margin-top: 1rem;">View Services</button>
                            </div>
                            <div class="card">
                                <h3>Contact Us About {display_name}</h3>
                                <p>Have questions? Reach out to our team for more information.</p>
                                <button class="btn" style="margin-top: 1rem;">Get in Touch</button>
                            </div>
                        </div>
                    </div>
                    '''
                    print(f"  ⚠️ Using fallback content for {route_name}")
                    
                    
                    
                    
                    
                    
                    
                    
        # Print summary
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"  - Brand: {brand_name}")
        print(f"  - Navigation links: {len(nav_links)}")
        print(f"  - Pages extracted: {len(page_contents)}")
        for route, content in page_contents.items():
            print(f"    • {route}: {len(content)} chars")
        print(f"  - Footer: {'✅ Extracted' if footer_html else '❌ Not found (will generate default)'}")
        
        
        
        
        
        
        
        
        
        
        
        
        # ========== BUILD DYNAMIC PAGES SECTION FOR PROMPT ==========
        pages_section = ""
        for route, content in page_contents.items():
            pages_section += f"""
--- PAGE: {route} ---
{content[:50000]}
--- END OF PAGE: {route} ---

"""
        
        print(f"📄 Built pages section for routes: {list(page_contents.keys())}")       
        
        
        
        
        
        
        
        
        
        
        
        
        
        

        # ========== DEBUG: CHECK WHAT WAS EXTRACTED ==========
        print(f"\n🔍 DEBUG - page_contents keys: {list(page_contents.keys())}")
        for key in page_contents.keys():
            preview = page_contents[key][:100] if page_contents[key] else "(empty)"
            print(f"  Key: '{key}' - Content preview: {preview}...")
        # ====================================================

        # ========== COLLECT AVAILABLE IMAGES ==========
        first_image = None        
                           
                    
                    
                    
                    
                    
                    
                    

        # Ensure all navigation pages have content
        for href, label in nav_links:
            route_key = href.replace("/", "_")
            if route_key not in page_contents:
                page_contents[route_key] = f'''
                <div class="container">
                    <div class="hero" style="min-height: 40vh; margin: 2rem;">
                        <div class="hero-content">
                            <h1 class="gradient-text">{label}</h1>
                            <p>Welcome to our {label.lower()} page. Explore our offerings and find what suits you best.</p>
                            <button class="btn" onclick="showPage('home')">Back to Home</button>
                        </div>
                    </div>
                    <div class="grid">
                        <div class="card">
                            <h3>Featured {label}</h3>
                            <p>Discover amazing opportunities in our {label.lower()} section.</p>
                            <button class="btn" style="margin-top: 1rem;">Learn More</button>
                        </div>
                        <div class="card">
                            <h3>Upcoming {label}</h3>
                            <p>Stay updated with the latest news and events in {label.lower()}.</p>
                            <button class="btn" style="margin-top: 1rem;">View Details</button>
                        </div>
                        <div class="card">
                            <h3>Contact Us About {label}</h3>
                            <p>Have questions? Reach out to our team for more information.</p>
                            <button class="btn" style="margin-top: 1rem;">Get in Touch</button>
                        </div>
                    </div>
                </div>
                '''

        # Print summary
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"  - Brand: {brand_name}")
        print(f"  - Navigation links: {len(nav_links)}")
        print(f"  - Pages extracted: {len(page_contents)}")
        for route, content in page_contents.items():
            print(f"    • {route}: {len(content)} chars")
        print(f"  - Footer: {'✅ Extracted' if footer_html else '❌ Not found (will generate default)'}")

        # ========== COLLECT AVAILABLE IMAGES ==========
        first_image = None
        for file_path in files.keys():
            if file_path.startswith("public/images/") and file_path.endswith((".jpg", ".png", ".jpeg")):
                first_image = "/" + file_path.replace("public/", "")
                break

        print(f"\n🖼️ First image: {first_image}")

        # ========== PREPARE DATA FOR PROMPT ==========
        nav_links_json = json.dumps(nav_links)
        page_contents_json = json.dumps(page_contents, indent=2)[:15000]
        
        # Get home page content
        home_content = page_contents.get('page', f'<div class="hero-content"><h1 class="gradient-text">{brand_name}</h1><p>Welcome to our website</p><button class="btn">Get Started</button></div>')
        
        
        
        
        # Fix ShieldCheck icon to use correct Font Awesome class
        home_content = home_content.replace('fa-shield-check', 'fa-shield-alt')       
        
        
        
        
        
        
        # Get backend URL
        BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
         # ========== FORCE EXTRACT FAQ AND STATS FROM SOURCE FILES ==========
        homepage_source = files.get("app/page.tsx", "")
        faq_component_source = files.get("components/FAQ.tsx", "")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
         # ========== STRONG FAQ EXTRACTION - HANDLES ALL FORMATS ==========
        faq_html = ""
        stats_html = ""
        
        # Combine all source files to search
        all_source = homepage_source + "\n" + faq_component_source
        
        # METHOD 1: Extract from inline map array (most common in your code)
        # Pattern: {[ { q: "text", a: "text" }, { q: "text", a: "text" } ].map(...)}
        inline_map_pattern = r'\{\s*\[\s*\{\s*(?:q|question):\s*["\']([^"\']+)["\']\s*,\s*(?:a|answer):\s*["\']([^"\']+)["\']\s*\}'
        inline_items = re.findall(inline_map_pattern, homepage_source)
        
        if inline_items:
            print(f"✅ Found {len(inline_items)} FAQ items from inline map")
            for question, answer in inline_items:
                faq_html += f'''
            <div class="bg-gradient-to-br from-white/5 to-white/3 rounded-2xl border border-white/10 overflow-hidden">
                <button class="faq-btn w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors">
                    <span class="font-semibold text-white">{question}</span>
                    <i class="fas fa-plus text-purple-400"></i>
                </button>
                <div class="faq-answer hidden px-6 pb-4 text-gray-400">
                    {answer}
                </div>
            </div>'''
        
        # METHOD 2: Extract from React component state array
        # Pattern: const [openFaq, setOpenFaq] = useState... and array defined above
        if not faq_html:
            # Look for faqs array with q/a properties
            const_faq_pattern = r'(?:const|let)\s+faqs\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'
            const_match = re.search(const_faq_pattern, all_source, re.DOTALL)
            
            if const_match:
                faq_content = const_match.group(1)
                # Match both { q: "...", a: "..." } and { question: "...", answer: "..." }
                item_pattern = r'\{\s*(?:q|question):\s*["\']([^"\']+)["\']\s*,\s*(?:a|answer):\s*["\']([^"\']+)["\']\s*\}'
                faq_items = re.findall(item_pattern, faq_content)
                
                if faq_items:
                    for question, answer in faq_items:
                        faq_html += f'''
            <div class="bg-gradient-to-br from-white/5 to-white/3 rounded-2xl border border-white/10 overflow-hidden">
                <button class="faq-btn w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors">
                    <span class="font-semibold text-white">{question}</span>
                    <i class="fas fa-plus text-purple-400"></i>
                </button>
                <div class="faq-answer hidden px-6 pb-4 text-gray-400">
                    {answer}
                </div>
            </div>'''
                    print(f"✅ Extracted {len(faq_items)} FAQ items from const faqs array")
        
        # METHOD 3: Extract from JSX directly (for inline FAQ without array variable)
        if not faq_html:
            # Look for FAQ items in the JSX structure
            jsx_faq_pattern = r'<div[^>]*className="[^"]*faq[^"]*"[^>]*>.*?<span[^>]*>([^<]+)</span>.*?<p[^>]*>([^<]+)</p>'
            jsx_matches = re.findall(jsx_faq_pattern, homepage_source, re.DOTALL)
            
            if jsx_matches:
                for question, answer in jsx_matches:
                    faq_html += f'''
            <div class="bg-gradient-to-br from-white/5 to-white/3 rounded-2xl border border-white/10 overflow-hidden">
                <button class="faq-btn w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors">
                    <span class="font-semibold text-white">{question.strip()}</span>
                    <i class="fas fa-plus text-purple-400"></i>
                </button>
                <div class="faq-answer hidden px-6 pb-4 text-gray-400">
                    {answer.strip()}
                </div>
            </div>'''
                    print(f"✅ Extracted {len(jsx_matches)} FAQ items from JSX structure")
        
        # METHOD 4: Extract as last resort using simple search
        if not faq_html:
            # Search for patterns like "question:" and "answer:" in the source
            simple_pattern = r'(?:q|question)[:\s]+["\']([^"\']+)["\']\s*,\s*(?:a|answer)[:\s]+["\']([^"\']+)["\']'
            simple_matches = re.findall(simple_pattern, all_source, re.IGNORECASE)
            
            if simple_matches:
                print(f"✅ Found {len(simple_matches)} FAQ items using simple pattern")
                for question, answer in simple_matches:
                    faq_html += f'''
            <div class="bg-gradient-to-br from-white/5 to-white/3 rounded-2xl border border-white/10 overflow-hidden">
                <button class="faq-btn w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors">
                    <span class="font-semibold text-white">{question}</span>
                    <i class="fas fa-plus text-purple-400"></i>
                </button>
                <div class="faq-answer hidden px-6 pb-4 text-gray-400">
                    {answer}
                </div>
            </div>'''
        
        if not faq_html:
            faq_html = '<p class="text-gray-400 text-center">No FAQ items found</p>'
            print("⚠️ No FAQ section found in source")
        else:
            print(f"📊 Total FAQ items extracted: {faq_html.count('faq-btn')}")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # ========== EXTRACT FOOTER FROM SOURCE ==========
        footer_html = ""
        
        # Check for Footer.tsx component file
        footer_component = files.get("components/Footer.tsx", "")
        
        if footer_component:
            print("🔍 Extracting footer from components/Footer.tsx")
            
            # Extract the JSX content from return statement
            return_match = re.search(r'return\s*\(\s*([\s\S]*?)\s*\)\s*;', footer_component, re.DOTALL)
            
            if return_match:
                footer_html = return_match.group(1)
                
                # Convert React/JSX to HTML
                footer_html = re.sub(r'className=', 'class=', footer_html)
                footer_html = re.sub(r'<Link\s+href="([^"]+)"[^>]*>', r'<a href="\1">', footer_html)
                footer_html = re.sub(r'</Link>', '</a>', footer_html)
                
                # Convert Lucide icons to Font Awesome
                footer_html = re.sub(r'<Sparkles\s*/>', '<i class="fas fa-sparkles text-purple-500"></i>', footer_html)
                footer_html = re.sub(r'<Mail\s*/>', '<i class="fas fa-envelope"></i>', footer_html)
                footer_html = re.sub(r'<Phone\s*/>', '<i class="fas fa-phone"></i>', footer_html)
                footer_html = re.sub(r'<Send\s*/>', '<i class="fas fa-paper-plane"></i>', footer_html)
                footer_html = re.sub(r'<ArrowUp\s*/>', '<i class="fas fa-arrow-up"></i>', footer_html)
                
                # Remove useState and useEffect hooks
                footer_html = re.sub(r'\{showScroll \&\& \(', '', footer_html)
                footer_html = re.sub(r'\)\}', '', footer_html)
                
                print(f"✅ Footer extracted from component: {len(footer_html)} chars")
        
        # Fallback to default footer if component not found
        if not footer_html:
            from datetime import datetime
            footer_html = f'''
            <footer class="bg-zinc-950 border-t border-white/10 py-12">
                <div class="container mx-auto px-4 grid md:grid-cols-4 gap-8">
                    <div class="space-y-4">
                        <div class="flex items-center gap-2"><i class="fas fa-sparkles text-purple-500"></i><span class="font-bold">{brand_name}</span></div>
                        <p class="text-sm text-gray-400">Premium digital solutions.</p>
                    </div>
                    <div><h4 class="font-bold mb-4">Quick Links</h4><ul class="space-y-2 text-sm text-gray-400"><li>Courses</li><li>Admissions</li></ul></div>
                    <div><h4 class="font-bold mb-4">Contact</h4><ul class="space-y-2 text-sm text-gray-400"><li>support@example.com</li><li>+1 (555) 123-4567</li></ul></div>
                    <div><h4 class="font-bold mb-4">Newsletter</h4><div class="flex gap-2"><input class="bg-white/5 p-2 rounded w-full" placeholder="Email" /><button class="bg-purple-600 p-2 rounded"><i class="fas fa-paper-plane"></i></button></div></div>
                </div>
                <div class="text-center mt-8 text-sm text-gray-600">© {datetime.now().year} {brand_name}. All rights reserved.</div>
            </footer>
            '''
        
        # Also extract scroll to top button JavaScript
        scroll_script = """
        <script>
        // Scroll to Top Functionality
        let scrollBtn = document.getElementById('scrollToTop');
        if(scrollBtn) {
            window.addEventListener('scroll', () => {
                if(window.scrollY > 500) {
                    scrollBtn.classList.remove('hidden');
                } else {
                    scrollBtn.classList.add('hidden');
                }
            });
            scrollBtn.addEventListener('click', () => {
                window.scrollTo({top: 0, behavior: 'smooth'});
            });
        }
        </script>
        """       
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
         # ========== EXTRACT TESTIMONIALS FROM SOURCE ==========
        testimonials_html = ""
        
        # Check for testimonials array in homepage
        testimonials_pattern = r'const\s+testimonials\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'
        testimonials_match = re.search(testimonials_pattern, homepage_source, re.DOTALL)
        
        if not testimonials_match:
            # Also check if testimonials are defined as a variable
            alt_pattern = r'const\s+testimonials\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'
            testimonials_match = re.search(alt_pattern, homepage_source, re.DOTALL)
        
        if testimonials_match:
            testimonials_content = testimonials_match.group(1)
            
            # Try format 1: { name: "...", role: "...", quote: "..." }
            pattern1 = r'\{\s*name:\s*["\']([^"\']+)["\']\s*,\s*role:\s*["\']([^"\']+)["\']\s*,\s*quote:\s*["\']([^"\']+)["\']\s*\}'
            testimonial_items = re.findall(pattern1, testimonials_content)
            
            # If not found, try format 2: { name: "...", text: "..." } (no role)
            if not testimonial_items:
                pattern2 = r'\{\s*name:\s*["\']([^"\']+)["\']\s*,\s*text:\s*["\']([^"\']+)["\']\s*\}'
                items = re.findall(pattern2, testimonials_content)
                for name, text in items:
                    testimonial_items.append((name, "", text))
                print(f"📝 Found testimonials without roles")
            
            if testimonial_items:
                for name, role, quote in testimonial_items:
                    if role:
                        testimonials_html += f'''
            <div class="bg-gray-900 p-8 rounded-2xl border border-white/10">
                <p class="text-gray-300 mb-6 italic">"{quote}"</p>
                <div class="font-bold text-white">{name}</div>
                <div class="text-sm text-purple-400">{role}</div>
            </div>'''
                    else:
                        testimonials_html += f'''
            <div class="bg-gray-900 p-8 rounded-2xl border border-white/10">
                <p class="text-gray-300 mb-6 italic">"{quote}"</p>
                <div class="font-bold text-purple-400">- {name}</div>
            </div>'''
                print(f"✅ Extracted {len(testimonial_items)} testimonials from source")
            else:
                testimonials_html = '<p class="text-gray-400 text-center">No testimonials found</p>'
        else:
            # Also check for inline testimonials in JSX
            inline_testimonial_pattern = r'<div[^>]*className="[^"]*testimonial[^"]*"[^>]*>.*?<p[^>]*>([^<]+)</p>.*?<h[34][^>]*>([^<]+)</h[34]>'
            inline_matches = re.findall(inline_testimonial_pattern, homepage_source, re.DOTALL)
            if inline_matches:
                for quote, name in inline_matches:
                    testimonials_html += f'''
            <div class="bg-gray-900 p-8 rounded-2xl border border-white/10">
                <p class="text-gray-300 mb-6 italic">"{quote.strip()}"</p>
                <div class="font-bold text-purple-400">- {name.strip()}</div>
            </div>'''
                print(f"✅ Extracted {len(inline_matches)} testimonials from inline JSX")
            else:
                testimonials_html = '<p class="text-gray-400 text-center">No testimonials section found</p>'
                print("⚠️ No testimonials section found in source")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
         # ⭐⭐⭐ CRITICAL: Use Cloudinary URL for images (NO base64) ⭐⭐⭐
        # Get the Cloudinary URL for the image
        image_url = existing_image_url  # Use existing URL if provided during edit
        
        # Also check if there's a Cloudinary URL in the files
        if not image_url and "__cloudinary_image_url__" in files:
            image_url = files["__cloudinary_image_url__"]
            print(f"📸 Found Cloudinary URL in files: {image_url[:80]}...")
        
        if not image_url:
            # No existing URL, upload new image
            for file_key, content in files.items():
                if file_key.startswith("public/images/") and isinstance(content, str) and content.startswith("__binary_base64__"):
                    # Upload to Cloudinary and get cached URL
                    image_url = await get_cloudinary_url_for_preview(file_key, content, files)
                    if image_url:
                        print(f"📸 Using Cloudinary URL: {image_url[:80]}...")
                    else:
                        # Fallback to placeholder if Cloudinary fails
                        image_url = "https://placehold.co/1920x1080/1a1a2e/white?text=Image"
                        print(f"⚠️ Cloudinary failed, using placeholder")
                    break
        else:
            print(f"📸 Using existing Cloudinary URL (preserved from original): {image_url[:80]}...")
            # Store the existing URL in files for database
            files["__cloudinary_image_url__"] = image_url
        
        # ⭐⭐⭐ CRITICAL FIX: ALWAYS use image_url for first_image_display ⭐⭐⭐
        # During EDIT: Use Cloudinary URL from database
        # During INITIAL BUILD: Use uploaded Cloudinary URL
        if image_url and image_url.startswith('https://res.cloudinary.com'):
            first_image_display = image_url
            print(f"🖼️ ✅ Using Cloudinary URL for hero: {first_image_display[:80]}...")
        elif first_image:
            first_image_display = first_image
            print(f"🖼️ Using local image path: {first_image_display}")
        else:
            first_image_display = 'None - use gradient background'
            print(f"🖼️ No image available, using gradient")
        
        # If we have an image URL, force it into the home content
        if image_url:
            # Replace any image path with the Cloudinary URL
            home_content = home_content.replace('/images/image_1.jpg', image_url)
            home_content = home_content.replace('/images/image_2.jpg', image_url)
            home_content = re.sub(r'src=["\']/images/[^"\']+\.jpg["\']', f'src="{image_url}"', home_content)
            home_content = re.sub(r"src=['\']/images/[^'\']+\.jpg['\']", f'src="{image_url}"', home_content)
            
            # Also ensure the hero section has the image tag
            if '<img' not in home_content:
                # Inject the image into the hero section
                home_content = f'''
        <section class="relative h-screen w-full overflow-hidden">
            <img src="{image_url}" class="absolute inset-0 w-full h-full object-cover" />
            <div class="absolute inset-0 bg-black/50"></div>
            <div class="relative z-10 flex flex-col items-center justify-center h-full text-center px-4">
                <h1 class="text-5xl md:text-7xl font-bold text-white mb-6">{brand_name}</h1>
                <p class="text-xl text-gray-200 mb-8 max-w-2xl mx-auto">Welcome to {brand_name}</p>
                <button class="btn">Get Started</button>
            </div>
        </section>
        '''
                print(f"  ✅ Injected Cloudinary image into home content")
        
        # Update the first_image display for the prompt
        first_image_display = image_url if image_url else (first_image if first_image else 'None - use gradient background')
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        prompt = f"""CRITICAL: You MUST include Tailwind CSS CDN in the <head> tag:
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/lucide@latest"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

Create a BEAUTIFUL, COMPLETE HTML preview for "{brand_name}".







================================================================================
PRODUCT CARD FORMAT FOR SHOP PAGE:
================================================================================

When generating shop page products, use this EXACT format for Add to Cart buttons:

<div class="product-card">
    <div class="product-image">
        <i data-lucide="shopping-bag" class="w-16 h-16 text-purple-400"></i>
    </div>
    <div class="product-info">
        <h3 class="product-title">Product Name</h3>
        <p class="product-price">$49.99</p>
        <button class="add-to-cart-btn" 
                data-id="prod_unique_id" 
                data-name="Product Name" 
                data-price="49.99">
            Add to Cart
        </button>
    </div>
</div>

CRITICAL: Every product button MUST have:
- class="add-to-cart-btn"
- data-id (unique for each product)
- data-name (product name)
- data-price (product price as number)

================================================================================
CART BADGE IN NAVIGATION:
================================================================================

Add this to your cart navigation link:

<a href="#" class="nav-link relative" data-page="cart">
    <i data-lucide="shopping-cart" class="w-4 h-4"></i>
    Cart
    <span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1">0</span>
</a>








================================================================================
🚨 AI INSTRUCTION: HANDLING NAVIGATION LINKS WITH ICONS 🚨
================================================================================

When you see navigation links with icons inside the Link component, you MUST:

1. Extract BOTH the href and the text label
2. Preserve the icon by converting it to HTML
3. ONLY add icons to E-COMMERCE links (Shop, Catalog, Cart, Products, Store, Basket, Checkout)
4. Keep OTHER links (About, Contact, Projects, Services, Blog, etc.) as TEXT-ONLY

================================================================================
PATTERNS TO RECOGNIZE:
================================================================================

React pattern for E-COMMERCE links (WITH icon):
```jsx
<Link href="/cart" className="flex items-center gap-2">
    <ShoppingBag className="w-5 h-5" /> Cart
</Link>

HTML output MUST be:
<a href="/cart" class="nav-link flex items-center gap-2 group" data-page="cart">
    <i data-lucide="shopping-bag" class="w-4 h-4 text-purple-400 group-hover:text-pink-500 group-hover:scale-110 transition-all duration-300"></i>
    <span class="text-gray-300 group-hover:text-purple-400 transition-colors duration-300">Cart</span>
</a>



================================================================================
ICON MAPPING FOR NAVIGATION LINKS:
================================================================================

- ShoppingBag → shopping-bag

















================================================================================
🚨 FAQ SECTION - USE THIS EXACT HTML (DO NOT MODIFY) 🚨
================================================================================

The following FAQ HTML has been pre-built from your source file.
You MUST include this EXACT HTML in the FAQ section.

{faq_html}

DO NOT generate new FAQ items. DO NOT add or remove any questions.
Simply place this HTML inside the FAQ section div.
================================================================================














================================================================================
CRITICAL: YOU MUST USE THE EXACT CONTENT BELOW FOR EACH PAGE
================================================================================

{pages_section}

================================================================================
NOW GENERATE THE HTML PREVIEW USING THE EXACT CONTENT ABOVE
================================================================================

For EACH page in the extraction above, create:
<div id="page_{route}" class="page">
    <div class="container mx-auto px-4 py-20">
        [PASTE THE EXACT CONTENT FROM THE PAGE EXTRACTION ABOVE - DO NOT MODIFY]
    </div>
</div>

DO NOT write "Welcome to our about page" or any other placeholder text.
USE THE EXACT CONTENT PROVIDED ABOVE.
================================================================================



















================================================================================
🚨 NAVIGATION STYLING REQUIREMENTS - MUST INCLUDE EXACT CLASSES 🚨
================================================================================

When generating navigation HTML, you MUST include these exact classes for the brand icon:

BRAND ICON REQUIREMENTS:
- MUST have: class="w-6 h-6 text-yellow-400 drop-shadow-lg group-hover:scale-110 transition-all duration-300"
- MUST have: data-lucide="[THE_ICON_NAME_EXTRACTED_FROM_SOURCE]" 
- MUST be wrapped in: <a class="brand flex items-center gap-2 group">

EXAMPLE - CORRECT BRAND HTML:
```html
<a href="/" class="brand flex items-center gap-2 group" onclick="handleBrandClick(event)">
    <i data-lucide="sparkles" class="w-6 h-6 text-yellow-400 drop-shadow-lg group-hover:scale-110 transition-all duration-300"></i>
    <span class="text-xl font-bold bg-gradient-to-r from-yellow-400 to-purple-500 bg-clip-text text-transparent">Brand Name</span>
</a>






================================================================================
🚨🚨🚨 ABSOLUTE REQUIREMENT - YOU MUST INCLUDE THIS EXACT CSS 🚨🚨🚨
================================================================================

FAILURE TO INCLUDE THE CSS BELOW WILL CAUSE THE PREVIEW TO BREAK.

YOU HAVE NO CHOICE. YOU MUST COPY AND PASTE THIS EXACT CSS INTO YOUR <style> TAG.

DO NOT MODIFY IT.
DO NOT SIMPLIFY IT.
DO NOT WRITE YOUR OWN CSS.
DO NOT OMIT ANY PART OF IT.

================================================================================
MANDATORY CSS - COPY THIS EXACTLY:
================================================================================
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', system-ui, sans-serif; 
    background: linear-gradient(135deg, #0a0a0c 0%, #2d1b4e 100%); 
    color: #f8fafc; 
    min-height: 100vh;}}

header {{ background: rgba(26, 26, 30, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(255,255,255,0.1); position: fixed; top: 0; left: 0; right: 0; z-index: 100; height: 72px; }}
.nav-container {{ max-width: 1280px; margin: 0 auto; height: 100%; display: flex; justify-content: space-between; align-items: center; padding: 0 1.5rem; }}
.brand {{ font-size: 1.5rem; font-weight: 800; text-decoration: none; background: linear-gradient(135deg, #c084fc, #f472b6); -webkit-background-clip: text; background-clip: text; color: transparent; display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }}
.nav-links {{ display: flex; gap: 1rem; align-items: center; }}
.nav-link {{ color: #9ca3af; text-decoration: none; padding: 0.5rem 1rem; border-radius: 0.5rem; transition: all 0.2s; cursor: pointer; }}
.nav-link:hover, .nav-link.active {{ color: #c084fc; background: rgba(192,132,252,0.1); }}

.hamburger {{ display: none; flex-direction: column; gap: 4px; background: transparent; border: none; cursor: pointer; padding: 0.5rem; }}
.hamburger span {{ width: 25px; height: 3px; background: #9ca3af; border-radius: 2px; transition: all 0.3s ease; }}
.hamburger.active span:nth-child(1) {{ transform: rotate(45deg) translate(5px, 5px); }}
.hamburger.active span:nth-child(2) {{ opacity: 0; }}
.hamburger.active span:nth-child(3) {{ transform: rotate(-45deg) translate(5px, -5px); }}

.mobile-menu {{ position: fixed; top: 72px; right: -100%; width: 280px; height: calc(100vh - 72px); background: #1a1a1e; z-index: 200; transition: right 0.3s ease; padding: 24px; border-left: 1px solid rgba(255,255,255,0.1); }}
.mobile-menu.active {{ right: 0; }}
.mobile-overlay {{ position: fixed; top: 72px; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 199; display: none; }}
.mobile-overlay.active {{ display: block; }}
.mobile-nav-link {{ display: block; padding: 12px 16px; color: #9ca3af; text-decoration: none; border-radius: 0.5rem; margin-bottom: 8px; transition: all 0.2s; cursor: pointer; }}
.mobile-nav-link:hover, .mobile-nav-link.active {{ color: #c084fc; background: rgba(192,132,252,0.1); }}

.page {{ display: none; min-height: calc(100vh - 72px); padding-top: 88px; }}
.page.active {{ display: block; }}
.container {{ max-width: 1280px; margin: 0 auto; padding: 0 1.5rem; }}

@media (max-width: 768px) {{ .nav-links {{ display: none; }} .hamburger {{ display: flex; }} }}







/* Yellow Icon Styles for Navigation */
.nav-link i, 
.mobile-nav-link i {{
    filter: drop-shadow(0 0 3px rgba(234, 179, 8, 0.5));
    transition: all 0.3s ease;
}}

.nav-link:hover i, 
.mobile-nav-link:hover i {{
    filter: drop-shadow(0 0 8px rgba(234, 179, 8, 0.8));
    transform: scale(1.1);
}}

.nav-link:hover span, 
.mobile-nav-link:hover span {{
    color: #eab308;
}}

.nav-link.active i, 
.mobile-nav-link.active i {{
    color: #fbbf24;
    filter: drop-shadow(0 0 5px rgba(251, 191, 36, 0.8));
}}

.nav-link.active span, 
.mobile-nav-link.active span {{
    color: #fbbf24;
}}

.brand i {{
    filter: drop-shadow(0 0 5px rgba(234, 179, 8, 0.5));
}}

.brand:hover i {{
    transform: scale(1.05);
    filter: drop-shadow(0 0 10px rgba(234, 179, 8, 0.8));
}}





/* ========== PRODUCT CARD STYLES ========== */
.product-card {{
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 1rem;
    padding: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
}}

.product-card:hover {{
    {{transform}}: translateY(-4px);
    border-color: #c084fc;
    box-shadow: 0 10px 25px -5px rgba(192, 132, 252, 0.3);
}}

.product-image {{
    background: linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(236, 72, 153, 0.2));
    border-radius: 0.75rem;
    transition: all 0.3s ease;
}}

.product-card:hover .product-image i {{
    {{transform}}: scale(1.1);
}}

.product-title {{
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: white;
}}

.product-price {{
    font-size: 1.5rem;
    font-weight: 700;
    color: #c084fc;
    margin-bottom: 1rem;
}}

.add-to-cart-btn {{
    width: 100%;
    padding: 0.5rem 1rem;
    background: linear-gradient(135deg, #8b5cf6, #ec4899);
    color: white;
    border-radius: 0.5rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
}}

.add-to-cart-btn:hover {{
    opacity: 0.9;
    {{transform}}: scale(0.98);
}}

/* ========== CART SIDEBAR STYLES ========== */
#cart-sidebar {{
    position: fixed;
    right: 0;
    top: 0;
    height: 100%;
    width: 100%;
    max-width: 420px;
    background: linear-gradient(135deg, #1a1a2e, #0f0f12);
    box-shadow: -5px 0 30px rgba(0, 0, 0, 0.5);
    z-index: 1000;
    {{transform}}: translateX(100%);
    transition: {{transform}} 0.3s ease;
    display: flex;
    flex-direction: column;
}}

#cart-sidebar.active {{
    {{transform}}: translateX(0);
}}

/* ========== CART PAGE STYLES ========== */
#cart-page-items {{
    max-height: 60vh;
    overflow-y: auto;
}}

#cart-page-items .flex {{
    background: rgba(255, 255, 255, 0.05);
    border-radius: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 1rem;
    transition: all 0.3s ease;
}}

#cart-page-items .flex:hover {{
    border-color: #c084fc;
    background: rgba(255, 255, 255, 0.08);
}}

#cart-summary {{
    animation: fadeInUp 0.4s ease-out;
}}

/* ========== CART BADGE STYLES ========== */
.cart-count-badge {{
    animation: bounceIn 0.3s ease-out;
    box-shadow: 0 0 10px rgba(168, 85, 247, 0.5);
}}

/* ========== TOAST NOTIFICATION ========== */
#cart-toast {{
    position: fixed;
    bottom: 2rem;
    left: 50%;
    {{transform}}: translateX(-50%);
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 2rem;
    font-size: 0.875rem;
    font-weight: 500;
    z-index: 1001;
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
    white-space: nowrap;
}}

#cart-toast.show {{
    opacity: 1;
}}

/* ========== MODAL STYLES ========== */
#checkout-modal, #success-modal {{
    animation: fadeIn 0.2s ease-out;
}}

#checkout-modal input, #success-modal input {{
    transition: all 0.2s ease;
}}

#checkout-modal input:focus, #success-modal input:focus {{
    border-color: #c084fc;
    box-shadow: 0 0 0 2px rgba(192, 132, 252, 0.2);
}}

/* ========== ANIMATIONS ========== */
@keyframes bounceIn {{
    0% {{ {{transform}}: scale(0); opacity: 0; }}
    50% {{ {{transform}}: scale(1.2); }}
    100% {{ {{transform}}: scale(1); opacity: 1; }}
}}

@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}

@keyframes fadeInUp {{
    from {{
        opacity: 0;
        {{transform}}: translateY(20px);
    }}
    to {{
        opacity: 1;
        {{transform}}: translateY(0);
    }}
}}

@keyframes spin {{
    to {{ {{transform}}: rotate(360deg); }}
}}

.fa-spinner {{
    animation: spin 1s linear infinite;
}}

/* ========== SCROLLBAR STYLES ========== */
#cart-items::-webkit-scrollbar,
#cart-page-items::-webkit-scrollbar {{
    width: 6px;
}}

#cart-items::-webkit-scrollbar-track,
#cart-page-items::-webkit-scrollbar-track {{
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
}}

#cart-items::-webkit-scrollbar-thumb,
#cart-page-items::-webkit-scrollbar-thumb {{
    background: linear-gradient(135deg, #8b5cf6, #ec4899);
    border-radius: 3px;
}}

#cart-items::-webkit-scrollbar-thumb:hover,
#cart-page-items::-webkit-scrollbar-thumb:hover {{
    background: linear-gradient(135deg, #a855f7, #f472b6);
}}

/* ========== BUTTON HOVER EFFECTS ========== */
button {{
    transition: all 0.2s ease;
}}

button:active {{
    {{transform}}: scale(0.98);
}}

/* ========== EMPTY CART MESSAGE ========== */
#empty-cart-message i {{
    opacity: 0.5;
}}

/* ========== GRID LAYOUT FOR PRODUCTS ========== */
.grid {{
    display: grid;
    gap: 1.5rem;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}}

@media (min-width: 768px) {{
    .grid {{
        grid-template-columns: repeat(3, 1fr);
    }}
}}

/* ========== RESPONSIVE ADJUSTMENTS ========== */
@media (max-width: 768px) {{
    #cart-sidebar {{
        max-width: 100%;
    }}
    
    .product-card {{
        padding: 1rem;
    }}
    
    .product-title {{
        font-size: 1rem;
    }}
    
    .product-price {{
        font-size: 1.25rem;
    }}
    
    #cart-toast {{
        font-size: 0.75rem;
        padding: 0.5rem 1rem;
        white-space: nowrap;
    }}
}}

/* ========== CHECKOUT FORM STYLES ========== */
#checkout-form input {{
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
}}

#checkout-form input:focus {{
    outline: none;
    border-color: #c084fc;
    ring: 2px solid rgba(192, 132, 252, 0.3);
}}

/* ========== SUCCESS MODAL ICON ========== */
#success-modal .fa-check {{
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}}
</style>


















================================================================================
🚨 CRITICAL: PROPER CONTAINER STRUCTURE - MUST FOLLOW EXACTLY 🚨
================================================================================

You MUST wrap ALL section content in a proper container with mx-auto for centering.

================================================================================
HERO SECTION - CORRECT STRUCTURE (MUST USE THIS EXACTLY):
================================================================================

```html
<section class="relative h-screen flex items-center justify-center overflow-hidden">
    <!-- Background Image -->
    <img src="[IMAGE_URL]" alt="Hero" class="absolute inset-0 w-full h-full object-cover" />
    
    <!-- Overlay -->
    <div class="absolute inset-0 bg-black/50"></div>
    
    <!-- Content Container - THIS IS THE KEY -->
    <div class="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <!-- ALL hero content goes INSIDE this div -->
        <span class="inline-block px-4 py-1 rounded-full bg-purple-500/20 text-purple-300 text-sm mb-4">BADGE TEXT</span>
        <h1 class="text-5xl md:text-7xl font-bold text-white mb-6">[BRAND_NAME]</h1>
        <p class="text-lg md:text-xl text-gray-200 mb-8 max-w-2xl mx-auto">[DESCRIPTION]</p>
        <div class="flex gap-4 justify-center">
            <a href="/shop" class="btn">Shop Now →</a>
            <a href="/catalog" class="btn">View Collection</a>
        </div>
    </div>
</section>























================================================================================
🚨 NAVIGATION & MOBILE MENU CSS REQUIREMENTS - MUST INCLUDE EXACTLY 🚨
================================================================================

You MUST include these COMPLETE navigation styles in your <style> tag:

```css
/* ========== HEADER & NAVIGATION ========== */
header {{
    background: rgba(26, 26, 30, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    height: 72px;
}}

.nav-container {{
    max-width: 1280px;
    margin: 0 auto;
    height: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 1.5rem;
}}

.brand {{
    font-size: 1.5rem;
    font-weight: 800;
    text-decoration: none;
    background: linear-gradient(135deg, #c084fc, #f472b6);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
}}

.nav-links {{
    display: flex;
    gap: 1rem;
    align-items: center;
}}

.nav-link {{
    color: #9ca3af;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    transition: all 0.2s;
    cursor: pointer;
}}

.nav-link:hover,
.nav-link.active {{
    color: #c084fc;
    background: rgba(192, 132, 252, 0.1);
}}

/* ========== MOBILE MENU ========== */
.hamburger {{
    display: none;
    flex-direction: column;
    gap: 4px;
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
}}

.hamburger span {{
    width: 25px;
    height: 3px;
    background: #9ca3af;
    border-radius: 2px;
    transition: all 0.3s ease;
}}

/* Hamburger animation to X when open */
.hamburger.active span:nth-child(1) {{
    transform: rotate(45deg) translate(5px, 5px);
}}

.hamburger.active span:nth-child(2) {{
    opacity: 0;
}}

.hamburger.active span:nth-child(3) {{
    transform: rotate(-45deg) translate(5px, -5px);
}}

.mobile-menu {{
    position: fixed;
    top: 72px;
    right: -100%;
    width: 280px;
    height: calc(100vh - 72px);
    background: #1a1a1e;
    z-index: 200;
    transition: right 0.3s ease;
    padding: 24px;
    border-left: 1px solid rgba(255, 255, 255, 0.1);
}}

.mobile-menu.active {{
    right: 0;
}}

.mobile-overlay {{
    position: fixed;
    top: 72px;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 199;
    display: none;
}}

.mobile-overlay.active {{
    display: block;
}}

.mobile-nav-link {{
    display: block;
    padding: 12px 16px;
    color: #9ca3af;
    text-decoration: none;
    border-radius: 0.5rem;
    margin-bottom: 8px;
    transition: all 0.2s;
    cursor: pointer;
}}

.mobile-nav-link:hover,
.mobile-nav-link.active {{
    color: #c084fc;
    background: rgba(192, 132, 252, 0.1);
}}

/* Responsive */
@media (max-width: 768px) {{
    .nav-links {{
        display: none;
    }}
    .hamburger {{
        display: flex;
    }}
}}






================================================================================
🚨 AI INSTRUCTIONS FOR HTML PREVIEW GENERATION 🚨
================================================================================

You are generating a COMPLETE HTML preview from Next.js React components.

================================================================================
CRITICAL RULES FOR NAVIGATION:
================================================================================

1. Navigation links MUST NOT have inline onclick attributes:
   ✅ CORRECT: <a href="#" class="nav-link" data-page="courses">Courses</a>
   ❌ WRONG: <a href="#" onclick="handleNavClick()" data-page="courses">Courses</a>

2. The JavaScript handles all clicks via event listeners - do NOT add onclick to nav links

3. Each page div MUST have id="page_pagename" where pagename matches data-page attribute

4. Active page MUST have class="active", others should not



================================================================================
EXACT HOME PAGE CONTENT - CONVERT THIS JSX TO HTML (PRESERVE EVERYTHING):
================================================================================
{home_content}

================================================================================
EXACT FAQ CONTENT - USE THIS EXACT HTML (DO NOT MODIFY):
================================================================================
{faq_html}

================================================================================
EXACT STATS CONTENT - USE THIS EXACT HTML (DO NOT MODIFY):
================================================================================
{faq_html}














================================================================================
🚨 CRITICAL: FAQ SECTION - PRESERVE ALL EXTRACTED ITEMS 🚨
================================================================================

You have been provided with FAQ content extracted from the source file below.
The number of FAQ items will vary based on what exists in the source.

EXTRACTED FAQ CONTENT (use ALL items below - do not add or remove):
================================================================================
{faq_html if faq_html else 'No FAQ items found in source'}
================================================================================

CRITICAL RULES FOR FAQ:
1. Use EVERY FAQ item in the HTML above - preserve ALL questions and answers
2. DO NOT add new FAQ items that don't exist
3. DO NOT remove any FAQ items
4. Each FAQ item MUST have working accordion toggle functionality
5. The answer must be hidden initially and shown when clicking the question

If there are 4 items in the extracted content → generate 4 items in HTML
If there are 3 items → generate 3 items
If there are 2 items → generate 2 items
If there is 1 item → generate 1 item
If there are 0 items → skip the FAQ section entirely

================================================================================
EXTRACTED FAQ HTML (USE THESE EXACT QUESTIONS AND ANSWERS):
================================================================================
{faq_html}









================================================================================
EXACT TESTIMONIALS CONTENT - USE THIS EXACT HTML:
================================================================================
{testimonials_html}










================================================================================
🚨 PREVIEW GENERATION INSTRUCTION - INCLUDE ALL SECTIONS FROM SOURCE FILES 🚨
================================================================================


Generate a complete HTML preview that includes EVERY section found in the source files.

CRITICAL RULES:
1. **ALWAYS include** the Navigation component (from components/Navigation.tsx)
2. **ALWAYS include** the Hero section (from app/page.tsx)
3. **ALWAYS include** the Features section (from app/page.tsx) - if present
4. **ALWAYS include** the Testimonials section (from app/page.tsx) - if present
5. **ALWAYS include** the Stats section (from app/page.tsx) - if present
6. **ALWAYS include** the FAQ section (from app/page.tsx) - if present
7. **ALWAYS include** the Footer (from components/Footer.tsx)

For EACH section found in the source files:
- Copy the EXACT content (same text, same images, same layout)
- Convert React components to HTML
- Preserve all styling classes
- Keep the same order as the original page

If a section does NOT exist in the source files → DO NOT generate it

The final HTML preview should be a TRUE representation of the Next.js project, containing ALL sections that exist in the original code.

================================================================================








================================================================================
🚨 CRITICAL: USE EXACT NAVIGATION HTML - DO NOT MODIFY 🚨
================================================================================

You MUST use the navigation HTML provided below EXACTLY as is.
DO NOT add, remove, or modify any links.

The brand/logo is the ONLY home link. There is NO separate "Home" button.

================================================================================
EXACT NAVIGATION HTML - USE THIS EXACTLY (DO NOT MODIFY):
================================================================================
{navigation_html}

================================================================================
RULES FOR THIS NAVIGATION:
================================================================================
1. ✅ The brand/logo clicks to home page (already has onclick="handleBrandClick(event)")
2. ✅ Only these links exist: Projects, About, Contact (or whatever is in the HTML above)
3. ❌ DO NOT add a "Home" link - it does not exist in the source
4. ❌ DO NOT add any extra links that aren't in the HTML above
5. ✅ Keep ALL classes, icons, and styling exactly as shown

================================================================================
IF THE NAVIGATION ABOVE IS EMPTY OR MISSING, USE THIS FALLBACK (WITHOUT HOME):
================================================================================
<nav class="flex justify-between items-center p-6 container mx-auto sticky top-0 z-50 bg-black/80 backdrop-blur-lg border-b border-white/10">
    <a href="/" class="brand flex items-center gap-2 group" onclick="handleBrandClick(event)">
        <i data-lucide="sparkles" class="w-6 h-6 text-yellow-400 drop-shadow-lg group-hover:scale-110 transition-all duration-300"></i>
        <span class="text-xl font-bold bg-gradient-to-r from-yellow-400 to-purple-500 bg-clip-text text-transparent">{brand_name}</span>
    </a>
    <div class="hidden md:flex space-x-2">
        <a href="/projects" class="nav-link flex items-center gap-2 group" data-page="projects">
            <i data-lucide="folder" class="w-4 h-4 text-yellow-400 group-hover:text-amber-500 group-hover:scale-110 transition-all duration-300"></i>
            <span class="text-gray-300 group-hover:text-yellow-400 transition-colors duration-300">Projects</span>
        </a>
        <a href="/about" class="nav-link flex items-center gap-2 group" data-page="about">
            <i data-lucide="info" class="w-4 h-4 text-yellow-400 group-hover:text-amber-500 group-hover:scale-110 transition-all duration-300"></i>
            <span class="text-gray-300 group-hover:text-yellow-400 transition-colors duration-300">About</span>
        </a>
        <a href="/contact" class="nav-link flex items-center gap-2 group" data-page="contact">
            <i data-lucide="mail" class="w-4 h-4 text-yellow-400 group-hover:text-amber-500 group-hover:scale-110 transition-all duration-300"></i>
            <span class="text-gray-300 group-hover:text-yellow-400 transition-colors duration-300">Contact</span>
        </a>
    </div>
    <button id="mobile-menu-button" class="md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors">
        <i data-lucide="menu" class="w-6 h-6 text-yellow-400"></i>
    </button>
</nav>




================================================================================
VERIFICATION: The final HTML MUST NOT contain any "Home" link in the navigation.
================================================================================



This ensures the AI:
1. Uses your exact navigation HTML (with the correct links and icons)
2. Never adds a "Home" link
3. Preserves all icons and styling
4. Only shows Projects, About, Contact (or whatever is in your source)








================================================================================
MOBILE MENU REQUIREMENTS
================================================================================
- Hamburger button must exist and be clickable
- Mobile menu must slide in from right
- Clicking overlay or link must close menu
- Hamburger must animate to X when open









================================================================================
🚨🚨🚨 CRITICAL: HERO BACKGROUND IMAGE URL - MUST USE CLOUDINARY URL 🚨🚨🚨
================================================================================

The hero background image MUST use EXACTLY this Cloudinary URL:

{image_url if image_url else first_image_display}

ABSOLUTE RULES - YOU MUST FOLLOW:
1. DO NOT replace this URL with "/images/image_1.jpg"
2. DO NOT use any local path like "/images/image_1.jpg"  
3. DO NOT use placeholder images or gradients
4. MUST use the EXACT Cloudinary URL provided above

CORRECT hero section (MUST USE THIS EXACT STRUCTURE):
<section class="relative h-screen flex items-center justify-center overflow-hidden">
    <img src="{image_url if image_url else first_image_display}" alt="Hero background" class="absolute inset-0 w-full h-full object-cover" />
    <div class="absolute inset-0 bg-black/50"></div>
    <div class="relative z-10 text-center px-4">
        <h1 class="text-6xl md:text-7xl font-bold text-white mb-6">{brand_name}</h1>
        <p class="text-xl text-gray-200 mb-8 max-w-2xl mx-auto">Your tagline here</p>
        <a href="#" class="btn">Get Started</a>
    </div>
</section>

WRONG - NEVER DO THIS:
❌ <img src="/images/image_1.jpg" ...>
❌ <img src="./image.jpg" ...>
❌ <div class="bg-gradient"></div> (without the image)
❌ Using any local path that starts with "/images/"

================================================================================













================================================================================
🚨 CRITICAL: BRAND ICON REQUIREMENT - MUST INCLUDE LUCIDE ICON
================================================================================

STATEMENT: The brand/logo link in the navigation MUST include a Lucide icon next to the brand name.

REQUIREMENT: Every brand link MUST have this structure:
- Use <a> tag (NOT <div>)
- Include flex classes: class="flex items-center gap-2"
- Add Lucide icon: <i data-lucide="icon-name" class="w-6 h-6 text-purple-400"></i>
- Add brand name text

✅ CORRECT HTML:
<a href="/" class="flex items-center gap-2 text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent" onclick="handleBrandClick(event)">
    <i data-lucide="hotel" class="w-6 h-6 text-purple-400"></i>
    Lodge Hub
</a>

❌ WRONG HTML (missing icon):
<div class="brand" onclick="handleBrandClick(event)">Lodge Hub</div>

❌ WRONG HTML (missing flex classes):
<a href="/" class="brand" onclick="handleBrandClick(event)">
    <i data-lucide="hotel"></i> Lodge Hub
</a>

CONSEQUENCE: Without the proper icon structure, the brand will have no visual icon and will not align correctly.

================================================================================











================================================================================
🚨 CRITICAL: BRAND/LOGO CLICK HANDLER - MUST INCLUDE
================================================================================

STATEMENT: The brand/logo link MUST have an onclick handler that navigates to the home page.






================================================================================
🚨 MANDATORY CSS INSTRUCTION - DO NOT IGNORE 🚨
================================================================================

You MUST include the COMPLETE CSS code below in EVERY HTML preview you generate.
This CSS is REQUIRED for proper navigation, mobile menu, and page transitions.
NEVER skip CSS. 







================================================================================
🚨🚨🚨 CRITICAL: YOU ARE AN HTML CONVERTER, NOT A CONTENT GENERATOR 🚨🚨🚨
================================================================================

Your ONLY job is to convert the EXACT React JSX content below into HTML.
DO NOT write new content. DO NOT change wording. DO NOT add or remove sections.

================================================================================
ICON REQUIREMENTS:
================================================================================
- Navigation brand: Use Lucide icons with <i data-lucide="icon-name">
- Footer social icons: Use Font Awesome with <i class="fab fa-icon-name">
- Feature cards: Use regular HTML/SVG, NOT Lucide icons
- Initialize Lucide with: lucide.createIcons()

================================================================================
EXACT NAVIGATION HTML - USE THIS EXACTLY (DO NOT MODIFY):
================================================================================
{navigation_html_for_prompt}

================================================================================
EXACT HOME PAGE CONTENT - CONVERT THIS JSX TO HTML (PRESERVE EVERYTHING):
================================================================================
{home_content}

================================================================================
EXACT OTHER PAGES CONTENT - CONVERT THESE TO HTML (PRESERVE EVERYTHING):
================================================================================
{page_contents_json}

================================================================================
EXACT BRAND NAME (use this exactly):
================================================================================
{brand_name}

================================================================================
EXACT NAVIGATION LINKS (use these exactly):
================================================================================
{nav_links_json}





================================================================================
EXACT FOOTER HTML - USE THE EXTRACTED CONTENT BELOW (DO NOT GENERATE NEW FOOTER)
================================================================================

The footer HTML below has been EXTRACTED from your components/Footer.tsx file.
You MUST use this EXACT HTML. DO NOT modify, simplify, or replace it.

EXTRACTED FOOTER HTML (USE THIS EXACTLY):
================================================================================
{footer_html}

================================================================================
🚨 CRITICAL: IF EXTRACTED FOOTER IS MISSING OR EMPTY, USE THIS FALLBACK 🚨
================================================================================
{f'''
<footer class="relative mt-20 bg-gradient-to-b from-zinc-950 to-black border-t border-white/10 py-12">
    <div class="container mx-auto px-4 grid md:grid-cols-4 gap-8">
        <div class="space-y-4">
            <div class="flex items-center gap-2">
                <i class="fas fa-sparkles text-purple-500"></i>
                <h3 class="font-bold text-lg">{brand_name}</h3>
            </div>
            <p class="text-sm text-gray-400">Premium digital solutions for modern businesses.</p>
            <div class="flex gap-4">
                <i class="fab fa-facebook-f text-gray-400 hover:text-purple-400 transition-colors cursor-pointer"></i>
                <i class="fab fa-twitter text-gray-400 hover:text-purple-400 transition-colors cursor-pointer"></i>
                <i class="fab fa-instagram text-gray-400 hover:text-purple-400 transition-colors cursor-pointer"></i>
            </div>
        </div>
        <div>
            <h4 class="font-bold mb-4">Quick Links</h4>
            <ul class="space-y-2 text-sm text-gray-400">
                <li><a href="/shop" class="hover:text-purple-400 transition-colors">Shop</a></li>
                <li><a href="/catalog" class="hover:text-purple-400 transition-colors">Catalog</a></li>
                <li><a href="/about" class="hover:text-purple-400 transition-colors">About Us</a></li>
            </ul>
        </div>
        <div>
            <h4 class="font-bold mb-4">Contact</h4>
            <ul class="space-y-2 text-sm text-gray-400">
                <li class="flex items-center gap-2"><i class="fas fa-envelope"></i> support@{brand_name.lower().replace(' ', '')}.com</li>
                <li class="flex items-center gap-2"><i class="fas fa-phone"></i> +1 (555) 123-4567</li>
                <li class="flex items-center gap-2"><i class="fas fa-map-marker-alt"></i> 123 Innovation Drive, NY 10001</li>
            </ul>
        </div>
        <div>
            <h4 class="font-bold mb-4">Newsletter</h4>
            <p class="text-sm text-gray-400 mb-3">Get 10% off your first order</p>
            <form class="flex gap-2" onsubmit="handleNewsletter(event)">
                <input type="email" placeholder="Your email address" class="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 transition-colors" />
                <button type="submit" class="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all"><i class="fas fa-paper-plane"></i></button>
            </form>
        </div>
    </div>
    <div class="text-center mt-8 pt-8 border-t border-white/10 text-sm text-gray-500">
        © 2026 {brand_name}. Crafted with <i class="fas fa-heart text-red-500"></i> in Nairobi
    </div>
</footer>
''' if not footer_html else ''}

================================================================================
🚨 FOOTER ICON CONVERSION RULES - APPLY TO EXTRACTED CONTENT 🚨
================================================================================

The extracted footer may contain Lucide icons. Convert them to Font Awesome:

| Pattern | Replace With |
|---------|--------------|
| `<Sparkles className="..." />` | `<i class="fas fa-sparkles text-purple-500"></i>` |
| `<Mail className="..." />` | `<i class="fas fa-envelope"></i>` |
| `<Phone className="..." />` | `<i class="fas fa-phone"></i>` |
| `<MapPin className="..." />` | `<i class="fas fa-map-marker-alt"></i>` |
| `<Send className="..." />` | `<i class="fas fa-paper-plane"></i>` |
| `<Heart className="..." />` | `<i class="fas fa-heart text-red-500"></i>` |
| `<Facebook className="..." />` | `<i class="fab fa-facebook-f"></i>` |
| `<Twitter className="..." />` | `<i class="fab fa-twitter"></i>` |
| `<Instagram className="..." />` | `<i class="fab fa-instagram"></i>` |
| `<ArrowUp />` | `<i class="fas fa-arrow-up"></i>` |

================================================================================
🚨 SCROLL TO TOP BUTTON & NEWSLETTER HANDLER - MUST INCLUDE 🚨
================================================================================

Add this button before closing </body>:
```html
<button id="scrollToTop" class="fixed bottom-8 right-8 z-50 w-12 h-12 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30 hover:scale-110 transition-all duration-300 flex items-center justify-center opacity-0 invisible">
    <i class="fas fa-arrow-up"></i>
</button>

Add this script before closing </body>:

<script>
(function() {{
    const scrollBtn = document.getElementById('scrollToTop');
    if (scrollBtn) {{
        window.addEventListener('scroll', function() {{
            if (window.scrollY > 500) {{
                scrollBtn.classList.remove('opacity-0', 'invisible');
                scrollBtn.classList.add('opacity-100', 'visible');
            }} else {{
                scrollBtn.classList.add('opacity-0', 'invisible');
                scrollBtn.classList.remove('opacity-100', 'visible');
            }}
        }});
        scrollBtn.addEventListener('click', function() {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});
    }}
    
    window.handleNewsletter = function(event) {{
        event.preventDefault();
        const email = event.target.querySelector('input[type="email"]')?.value;
        if (email) {{
            alert('Thank you for subscribing with: ' + email);
            event.target.reset();
        }}
    }};
}})();
</script>

================================================================================
KEEP ALL TEXT CONTENT EXACTLY AS EXTRACTED - DO NOT MODIFY:
================================================================================


1. Preserve ALL link text

2. Preserve ALL descriptions

3. Preserve ALL contact information

4. Preserve copyright text



















================================================================================
EXACT HERO BACKGROUND IMAGE URL (use this exactly):
================================================================================
{first_image_display}

================================================================================
RULES FOR CONVERTING HOME PAGE CONTENT:
================================================================================

1. Extract the hero section with EXACT text from {home_content}
2. Extract ALL feature cards with EXACT titles and descriptions
3. Extract ALL stats with EXACT numbers and labels
4. Extract ALL testimonials with EXACT quotes and names
5. Extract ALL CTA sections with EXACT button text
6. Preserve the EXACT number of items (don't add or remove cards)
7. Keep ALL text EXACTLY as written in the original JSX

================================================================================
RULES FOR CONVERTING OTHER PAGES:
================================================================================

For each page in {page_contents_json}:
1. Use the EXACT content provided
2. Preserve ALL headings, paragraphs, and button text
3. Keep the SAME number of cards, items, or sections
4. DO NOT add placeholder text like "Coming soon" or "Lorem ipsum"

================================================================================
DESIGN REQUIREMENTS:
================================================================================

1. Modern dark theme with purple/pink gradients (#c084fc, #f472b6)
2. Glass morphism effects (backdrop-blur, semi-transparent backgrounds)
3. Smooth animations and hover effects
4. Fully responsive (mobile hamburger menu at 768px)
5. ONLY ONE <style> tag and ONE <script> tag
6. Navigation brand uses Lucide icon - Footer uses Font Awesome - Features use HTML/SVG

















================================================================================
COMPLETE JAVASCRIPT:
================================================================================
<script>
    function handleBrandClick(event) {{
        event.preventDefault();
        event.stopPropagation();
        showPage('home');
        return false;
    }}
    
    function showPage(pageId) {{
        document.querySelectorAll('.page').forEach(page => {{
            page.classList.remove('active');
            page.style.display = 'none';
        }});
        const targetPage = document.getElementById('page_' + pageId);
        if (targetPage) {{
            targetPage.classList.add('active');
            targetPage.style.display = 'block';
        }}
        window.scrollTo(0, 0);
    }}
    
    function toggleMobileMenu() {{
        const mobileMenu = document.getElementById('mobileMenu');
        const mobileOverlay = document.getElementById('mobileOverlay');
        const hamburger = document.querySelector('.hamburger');
        
        if (mobileMenu) {{
            mobileMenu.classList.toggle('active');
        }}
        if (mobileOverlay) {{
            mobileOverlay.classList.toggle('active');
        }}
        if (hamburger) {{
            hamburger.classList.toggle('active');
        }}
    }}
    
    
    
    
    
    
    

    // ========== FAQ ACCORDION FUNCTIONS ==========
    function initFaqAccordion() {{
        const faqButtons = document.querySelectorAll('.faq-btn, .faq-question');
        faqButtons.forEach(button => {{
            button.removeEventListener('click', handleFaqClick);
            button.addEventListener('click', handleFaqClick);
        }});
    }}
    
    function handleFaqClick(event) {{
        const button = event.currentTarget;
        const answer = button.nextElementSibling;
        const icon = button.querySelector('i');
        if (answer && answer.classList.contains('hidden')) {{
            answer.classList.remove('hidden');
            if (icon) {{
                icon.classList.remove('fa-plus');
                icon.classList.add('fa-minus');
            }}
        }} else if (answer) {{
            answer.classList.add('hidden');
            if (icon) {{
                icon.classList.remove('fa-minus');
                icon.classList.add('fa-plus');
            }}
        }}
    }}
    

    function initScrollToTop() {{
        const scrollBtn = document.getElementById('scrollToTop');
        if (!scrollBtn) return;
        window.addEventListener('scroll', () => {{
            if (window.scrollY > 500) {{
                scrollBtn.classList.remove('opacity-0', 'invisible');
                scrollBtn.classList.add('opacity-100', 'visible');
            }} else {{
                scrollBtn.classList.add('opacity-0', 'invisible');
                scrollBtn.classList.remove('opacity-100', 'visible');
            }}
        }});
        scrollBtn.addEventListener('click', () => {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});
    }}
    
    // ========== NEWSLETTER FORM HANDLER ==========
    function initNewsletterForm() {{
        const newsletterForm = document.getElementById('newsletterForm');
        if (newsletterForm) {{
            newsletterForm.addEventListener('submit', (e) => {{
                e.preventDefault();
                const emailInput = newsletterForm.querySelector('input[type="email"]');
                if (emailInput && emailInput.value) {{
                    alert(`Thank you for subscribing with: ${{emailInput.value}}`);
                    emailInput.value = '';
                }}
            }});
        }}
    }}

    
    
    
    function toggleMobileMenu() {{
        const mobileMenu = document.getElementById('mobileMenu');
        const mobileOverlay = document.getElementById('mobileOverlay');
        const hamburger = document.querySelector('.hamburger');
        
        if (mobileMenu) mobileMenu.classList.toggle('active');
        if (mobileOverlay) mobileOverlay.classList.toggle('active');
        if (hamburger) hamburger.classList.toggle('active');
    }}
    
    
    
    
    
    
    
    function closeMobileMenu() {{
        const mobileMenu = document.getElementById('mobileMenu');
        const mobileOverlay = document.getElementById('mobileOverlay');
        const hamburger = document.querySelector('.hamburger');
        
        if (mobileMenu) {{
            mobileMenu.classList.remove('active');
        }}
        if (mobileOverlay) {{
            mobileOverlay.classList.remove('active');
        }}
        if (hamburger) {{
            hamburger.classList.remove('active');
        }}
    }}
    
    document.addEventListener('DOMContentLoaded', function() {{
        if (typeof lucide !== 'undefined') {{
            lucide.createIcons();
        }}
        
        const hamburger = document.querySelector('.hamburger');
        if (hamburger) {{
            hamburger.addEventListener('click', toggleMobileMenu);
        }}
        
        const overlay = document.getElementById('mobileOverlay');
        if (overlay) {{
            overlay.addEventListener('click', closeMobileMenu);
        }}
        
        document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {{
            link.addEventListener('click', (e) => {{
                e.preventDefault();
                const pageId = link.getAttribute('data-page');
                if (pageId) showPage(pageId);
            }});
        }});
        
        const brandLink = document.querySelector('.brand');
        if (brandLink) {{
            brandLink.addEventListener('click', handleBrandClick);
        }}
    }});
</script>













================================================================================
FINAL VERIFICATION:
================================================================================

Before outputting, verify:
- [ ] Home page has EXACT same sections as extracted content
- [ ] All text matches the original JSX word-for-word
- [ ] Number of feature cards matches (should be 4 for gym website)
- [ ] Number of stats matches (should be 4 for gym website)
- [ ] Number of testimonials matches (should be 3 for gym website)
- [ ] No placeholder or generic text was added
- [ ] Navigation HTML was copied exactly
- [ ] Footer HTML was copied exactly (if provided)
- [ ] Footer icons use Font Awesome classes (fab fa-* or fas fa-*)
- [ ] Font Awesome CDN is in the <head> tag














================================================================================
SPECIFIC INSTRUCTION FOR HOME PAGE (page_home)
================================================================================

The home page content above (from app/page.tsx) contains:

- A hero section with an image
- An h1 heading with your actual brand name (like "Amber College Prep")
- A paragraph with your actual description
- A button with your actual button text (like "Explore Programs")

YOU MUST use these EXACT values. For example:

✅ CORRECT: <h1>Amber College Prep</h1>
❌ WRONG: <h1>Welcome to our website</h1>

✅ CORRECT: <p>Empowering the next generation of scholars...</p>
❌ WRONG: <p>Welcome to our website</p>

✅ CORRECT: <button>Explore Programs</button>
❌ WRONG: <button>Get Started</button>

================================================================================




================================================================================
🚨🚨🚨 CRITICAL: SIGNUP & LOGIN PAGE REQUIREMENTS 🚨🚨🚨
================================================================================

When generating the HTML preview, you MUST follow these rules for authentication pages:

**SIGNUP PAGE (page_signup) - MUST have:**
1. Form with id="signup-form"
2. Form with onsubmit="handleSignup(event); return false;"
3. Input with name="name" for full name
4. Input with name="email" for email address
5. Input with name="password" for password
6. Input with name="confirmPassword" for password confirmation
7. Submit button that says "Sign up"

**LOGIN PAGE (page_login) - MUST have:**
1. Form with id="login-form"
2. Form with onsubmit="handleLogin(event); return false;"
3. Input with name="email" for email address
4. Input with name="password" for password
5. Submit button that says "Sign in"









================================================================================
🚨🚨🚨 CRITICAL JAVASCRIPT RULES - NO FLICKER, NO DISAPPEARING BACKGROUND 🚨🚨🚨
================================================================================

The JavaScript code MUST follow these rules:

1. NEVER call showPage() inside init() - causes unnecessary hiding/showing
2. ALWAYS check if a page is already active before hiding all pages
3. ALWAYS return early in showPage() if already on the target page
4. NEVER use inline styles that override CSS classes
5. ALWAYS use CSS for display control, not JavaScript inline styles
6. ALWAYS add a flag to prevent double initialization



================================================================================
🚨🚨🚨 CRITICAL: USE THE EXTRACTED CONTENT BELOW - NO PLACEHOLDERS! 🚨🚨🚨
================================================================================

The content below is EXTRACTED DIRECTLY from your Next.js pages. 
YOU MUST use this EXACT content for each page's HTML.

DO NOT generate placeholder text like "Welcome to our page" or "Explore our offerings".
USE THE EXACT CONTENT PROVIDED BELOW.

================================================================================
EXTRACTED PAGE CONTENTS - USE THESE EXACTLY:
================================================================================


For EACH page, copy the EXACT content from the extracted JSON above into the page div.
If the content contains arrays/maps, render them as HTML cards/items.

For example, if Programs page has program data, render the actual programs with their titles, descriptions, icons, etc.












================================================================================
COMPLETE CSS - USE THIS EXACTLY
================================================================================


<script src="https://cdn.tailwindcss.com"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: 'Inter', system-ui, sans-serif;
    background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);
    color: #e2e8f0;
    min-height: 100vh;
}}

header {{
    background: rgba(26, 26, 30, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255,255,255,0.1);
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 100;
    height: 72px;
}}

.nav-container {{
    max-width: 1280px;
    margin: 0 auto;
    height: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 1.5rem;
}}

.brand {{
    font-size: 1.5rem;
    font-weight: 800;
    text-decoration: none;
    background: linear-gradient(135deg, #c084fc, #f472b6);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}}

.nav-links {{
    display: flex;
    gap: 1rem;
    align-items: center;
}}

.nav-link {{
    color: #9ca3af;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    transition: all 0.2s;
}}

.nav-link:hover, .nav-link.active {{
    color: #c084fc;
    background: rgba(192,132,252,0.1);
}}

.page {{
    display: none;
    min-height: calc(100vh - 72px);
    padding-top: 88px;
}}

.page.active {{ display: block; }}

.container {{
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 1.5rem;
}}

.card {{
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
    border-radius: 1rem;
    padding: 1.5rem;
    border: 1px solid rgba(255,255,255,0.1);
    transition: all 0.3s;
}}

.card:hover {{
    transform: translateY(-4px);
    border-color: #c084fc;
}}

.gradient-text {{
    background: linear-gradient(135deg, #c084fc, #f472b6);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}}

.btn {{
    background: linear-gradient(135deg, #c084fc, #f472b6);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 2rem;
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
}}

.btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(192,132,252,0.3);
}}

.hero {{
    min-height: 70vh;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    position: relative;
    border-radius: 1rem;
    margin: 1rem;
    overflow: hidden;
}}

.hero-bg {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.35;
}}

.hero-content {{
    position: relative;
    z-index: 10;
    padding: 3rem;
}}

.hero-content h1 {{
    font-size: 3.5rem;
    margin-bottom: 1rem;
}}

.hero-content p {{
    font-size: 1.2rem;
    color: #9ca3af;
    margin-bottom: 2rem;
}}

.grid {{
    display: grid;
    gap: 1.5rem;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}}

/* Footer */
footer {{
    background: linear-gradient(180deg, rgba(15,15,18,0.8) 0%, #1a1a2e 100%);
    border-top: 1px solid rgba(255,255,255,0.05);
    margin-top: 4rem;
    padding: 3rem 0 2rem;
}}

.footer-container {{
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 1.5rem;
    display: grid;
    gap: 2rem;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}}

.footer-section h4 {{
    color: #c084fc;
    margin-bottom: 1rem;
}}

.footer-section a {{
    color: #9ca3af;
    text-decoration: none;
    display: block;
    margin-bottom: 0.5rem;
    transition: color 0.2s;
}}

.footer-section a:hover {{ color: #c084fc; }}

.copyright {{
    text-align: center;
    padding-top: 2rem;
    margin-top: 2rem;
    border-top: 1px solid rgba(255,255,255,0.05);
    color: #6b7280;
    font-size: 0.875rem;
}}

/* Mobile Menu */
.hamburger {{
    display: none;
    flex-direction: column;
    gap: 4px;
    background: transparent;
    border: none;
    cursor: pointer;
}}

.hamburger span {{
    width: 25px;
    height: 3px;
    background: #9ca3af;
    border-radius: 2px;
}}

.mobile-menu {{
    position: fixed;
    top: 0;
    right: -100%;
    width: 280px;
    height: 100vh;
    background: #1a1a1e;
    z-index: 200;
    transition: right 0.3s;
    padding: 80px 24px;
}}

.mobile-menu.active {{ right: 0; }}

.mobile-overlay {{
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.5);
    z-index: 199;
    display: none;
}}

.mobile-overlay.active {{ display: block; }}

.mobile-nav-link {{
    display: block;
    padding: 12px 16px;
    color: #9ca3af;
    text-decoration: none;
    border-radius: 0.5rem;
    margin-bottom: 8px;
}}

@media (max-width: 768px) {{
    .nav-links {{ display: none; }}
    .hamburger {{ display: flex; }}
    .hero-content h1 {{ font-size: 2rem; }}
    .footer-container {{ grid-template-columns: 1fr; text-align: center; }}
}}

@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.page {{ animation: fadeIn 0.3s ease; }}










/* Hamburger animation to X when open */
.hamburger.active span:nth-child(1) {{
    {{transform}}: rotate(45deg) translate(5px, 5px);
}}

.hamburger.active span:nth-child(2) {{
    opacity: 0;
}}

.hamburger.active span:nth-child(3) {{
    {{transform}}: rotate(-45deg) translate(5px, -5px);
}}

/* Add transition to hamburger spans */
.hamburger span {{
    width: 25px;
    height: 3px;
    background: #9ca3af;
    border-radius: 2px;
    transition: all 0.3s ease;
}}





















/* ========== FAQ ACCORDION STYLES ========== */
.faq-answer {{
    transition: all 0.3s ease;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    margin-top: 0.5rem;
    padding-top: 0.5rem;
}}

.faq-answer.hidden {{
    display: none;
}}

.faq-btn, .faq-question {{
    cursor: pointer;
    transition: all 0.2s ease;
    background: transparent;
    width: 100%;
    text-align: left;
}}

.faq-btn:hover, .faq-question:hover {{
    background: rgba(255, 255, 255, 0.05);
}}

.faq-btn i, .faq-question i {{
    transition: transform 0.2s ease;
}}








/* Increase feature icon sizes */
.feature-icon {{
    font-size: 3rem;
    width: auto;
    height: auto;
}}

/* For all icons in feature cards */
.grid.md\\:grid-cols-4 > div i {{
    font-size: 2rem;
    width: auto;
    height: auto;
    margin-bottom: 1rem;
}}





</style>








































================================================================================
JAVASCRIPT - WORKING NAVIGATION WITH BRAND CLICK HANDLER (FIXED)
================================================================================
<script>
function showPage(pageId) {{
    console.log('🔄 showPage called with:', pageId);
    
    // Hide ALL pages
    document.querySelectorAll('.page').forEach(page => {{
        page.classList.remove('active');
        page.style.display = 'none';
    }});
    
    // Show the target page
    const targetPage = document.getElementById('page_' + pageId);
    if (targetPage) {{
        targetPage.classList.add('active');
        targetPage.style.display = 'block';
        console.log('✅ Showing page:', pageId);
    }} else {{
        console.log('❌ Page not found:', 'page_' + pageId);
        // Fallback - show home
        const homePage = document.getElementById('page_home');
        if (homePage) {{
            homePage.classList.add('active');
            homePage.style.display = 'block';
        }}
    }}
    
    // Update navigation active states
    document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {{
        link.classList.remove('active');
        if (link.getAttribute('data-page') === pageId) {{
            link.classList.add('active');
        }}
    }});
    
    // Update URL
    if (pageId !== 'home') {{
        window.history.pushState({{}}, '', '/' + pageId);
    }} else {{
        window.history.pushState({{}}, '', '/');
    }}
    window.scrollTo(0, 0);
}}

function toggleMenu() {{
    const menu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('mobileOverlay');
    const hamburger = document.querySelector('.hamburger');
    
    if (menu) menu.classList.toggle('active');
    if (overlay) overlay.classList.toggle('active');
    if (hamburger) hamburger.classList.toggle('active');
}}

// Handle brand/logo click - ALWAYS go to home page
function handleBrandClick(e) {{
    e.preventDefault();
    e.stopPropagation();
    showPage('home');
    if (window.innerWidth <= 768) toggleMenu();
}}

// Handle navigation link clicks
function handleNavClick(e) {{
    e.preventDefault();
    const pageId = this.getAttribute('data-page');
    if (pageId) {{
        showPage(pageId);
        if (window.innerWidth <= 768) toggleMenu();
    }}
}}

// ========== INITIALIZATION - CRITICAL FOR HOME PAGE ==========
if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', init);
}} else {{
    init();
}}

function init() {{
    console.log('🎯 Initializing navigation...');
    
    // Get current path or default to home
    let currentPath = window.location.pathname.slice(1);
    if (!currentPath || currentPath === '') {{
        currentPath = 'home';
    }}
    console.log('📍 Current path:', currentPath);
    
    // Ensure ALL pages are hidden first
    document.querySelectorAll('.page').forEach(page => {{
        page.classList.remove('active');
        page.style.display = 'none';
    }});
    
    // Show the home page (or current path)
    const targetPageId = currentPath === 'home' ? 'page_home' : 'page_' + currentPath;
    const targetPage = document.getElementById(targetPageId);
    
    if (targetPage) {{
        targetPage.classList.add('active');
        targetPage.style.display = 'block';
        console.log('✅ Activated page:', targetPageId);
    }} else {{
        // Fallback - show home
        const homePage = document.getElementById('page_home');
        if (homePage) {{
            homePage.classList.add('active');
            homePage.style.display = 'block';
            console.log('✅ Fallback: Activated home page');
        }}
    }}
    
    // Update navigation active states
    document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {{
        link.classList.remove('active');
        if (link.getAttribute('data-page') === currentPath) {{
            link.classList.add('active');
        }}
    }});
    
    // Add event listeners
    const brandLink = document.querySelector('.brand');
    if (brandLink) {{
        brandLink.addEventListener('click', handleBrandClick);
        console.log('✅ Brand click handler attached');
    }}
    
    const hamburger = document.querySelector('.hamburger');
    const overlay = document.getElementById('mobileOverlay');
    if (hamburger) hamburger.addEventListener('click', toggleMenu);
    if (overlay) overlay.addEventListener('click', toggleMenu);
    
    document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {{
        link.removeEventListener('click', handleNavClick);
        link.addEventListener('click', handleNavClick);
    }});
    
    console.log('✅ Navigation initialized successfully');
}}

// Handle browser back/forward
window.addEventListener('popstate', () => {{
    const path = window.location.pathname.slice(1) || 'home';
    showPage(path);
}});
</script>







================================================================================
RETURN ONLY COMPLETE HTML starting with <!DOCTYPE html>. NO explanations.
================================================================================
"""





        response_text = await model_router.generate_content(
            prompt=prompt,
            config={"temperature": 0.1, "max_output_tokens": 4000000}
        )

        preview_html = clean_html_response(response_text)

        # ========== CLEAN ONERROR HANDLERS ==========
        preview_html = clean_onError_handlers(preview_html)  # ← ADD THIS LINE
        # ============================================
        
        
        
        # Fix ShieldCheck icon to use correct Font Awesome class
        preview_html = preview_html.replace('fa-shield-check', 'fa-shield-alt')       
        
        
        
        

        # Ensure doctype
        if not preview_html.lower().startswith("<!doctype"):
            preview_html = "<!DOCTYPE html>\n" + preview_html
            
            
            
            
            
            
            
            
            
            
            

        # Inject base64 images - Use Cloudinary URLs instead of huge base64 strings
        image_urls_cache = {}
        
        for file_key, content in files.items():
            if file_key.startswith("public/images/") and isinstance(content, str) and content.startswith("__binary_base64__"):
                public_path = "/" + file_key[len("public/"):]
                
                # Upload to Cloudinary and get URL (cached)
                cloudinary_url = await get_cloudinary_url_for_preview(file_key, content)
                
                if cloudinary_url:
                    image_urls_cache[public_path] = cloudinary_url
                    preview_html = preview_html.replace(f'src="{public_path}"', f'src="{cloudinary_url}"')
                    preview_html = preview_html.replace(f"src='{public_path}'", f'src="{cloudinary_url}"')
                    print(f"  ✅ Replaced {public_path} with Cloudinary URL")
                else:
                    # Fallback to base64 if Cloudinary fails
                    raw_b64 = content[len("__binary_base64__"):]
                    data_uri = f"data:image/jpeg;base64,{raw_b64}"
                    preview_html = preview_html.replace(f'src="{public_path}"', f'src="{data_uri}"')
                    preview_html = preview_html.replace(f"src='{public_path}'", f'src="{data_uri}"')
                    print(f"  ⚠️ Cloudinary failed, using base64 for {public_path}")
        
        # If no images were processed, use gradient background
        if not image_urls_cache:
            print("⚠️ No images available, using gradient background for hero")




































        # ========== CART HTML AND SCRIPT (DEFINED OUTSIDE F-STRING) ==========
        cart_html = """
<!-- Cart Sidebar -->
<div id="cart-sidebar" class="fixed right-0 top-0 h-full w-full max-w-md bg-gradient-to-br from-slate-900 to-slate-800 shadow-2xl z-50 transform translate-x-full transition-transform duration-300 flex flex-col">
    <div class="flex justify-between items-center p-4 border-b border-white/10">
        <h2 class="text-xl font-bold text-white flex items-center gap-2">
            <i class="fas fa-shopping-bag text-purple-400"></i> Your Cart
        </h2>
        <button onclick="closeCartSidebar()" class="p-2 rounded-lg hover:bg-white/10 transition-colors">
            <i class="fas fa-times text-gray-400"></i>
        </button>
    </div>
    <div id="cart-items" class="flex-1 overflow-y-auto p-4 space-y-4">
        <div class="text-center py-12 text-gray-400">Your cart is empty</div>
    </div>
    <div class="border-t border-white/10 p-4">
        <div class="flex justify-between mb-4">
            <span class="text-gray-400">Total:</span>
            <span id="cart-total" class="text-xl font-bold text-purple-400">$0.00</span>
        </div>
        <button onclick="openCheckoutModal()" class="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold text-white hover:opacity-90 transition">
            Checkout
        </button>
        <button onclick="closeCartSidebar()" class="w-full mt-2 py-2 text-gray-400 hover:text-white transition text-sm">
            Continue Shopping
        </button>
    </div>
</div>

<!-- Cart Toast -->
<div id="cart-toast" class="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-medium z-50 opacity-0 transition-opacity duration-300 pointer-events-none"></div>

<!-- Checkout Modal -->
<div id="checkout-modal" class="fixed inset-0 z-50 items-center justify-center px-4" style="display: none;">
    <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" onclick="closeCheckoutModal()"></div>
    <div class="relative bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl border border-white/10 shadow-2xl max-w-md w-full p-6">
        <div class="text-center mb-6">
            <div class="w-16 h-16 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center mx-auto mb-4">
                <i class="fas fa-credit-card text-white text-2xl"></i>
            </div>
            <h2 class="text-2xl font-bold text-white">Complete Your Order</h2>
            <p class="text-gray-400 text-sm mt-2">Enter your payment details</p>
        </div>
        <form id="checkout-form" onsubmit="processPayment(event)">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">Full Name</label>
                    <input type="text" id="full-name" required placeholder="John Doe" class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">Email Address</label>
                    <input type="email" id="email" required placeholder="john@example.com" class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">Card Number</label>
                    <input type="text" id="card-number" required placeholder="4242 4242 4242 4242" maxlength="19" class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-1">Expiry Date</label>
                        <input type="text" id="expiry" required placeholder="MM/YY" maxlength="5" class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-1">CVV</label>
                        <input type="password" id="cvv" required placeholder="123" maxlength="4" class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white">
                    </div>
                </div>
            </div>
            <div class="mt-6 p-4 bg-white/5 rounded-lg">
                <div class="flex justify-between text-sm">
                    <span>Order Total:</span>
                    <span id="checkout-total" class="font-bold text-purple-400">$0.00</span>
                </div>
            </div>
            <button type="submit" class="w-full mt-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl font-semibold text-white hover:opacity-90 transition">
                Pay Now
            </button>
            <button type="button" onclick="closeCheckoutModal()" class="w-full mt-2 py-2 text-gray-400 hover:text-white transition text-sm">
                Cancel
            </button>
        </form>
    </div>
</div>

<!-- Success Modal -->
<div id="success-modal" class="fixed inset-0 z-50 items-center justify-center px-4" style="display: none;">
    <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" onclick="closeSuccessModal()"></div>
    <div class="relative bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl border border-white/10 shadow-2xl max-w-md w-full p-6 text-center">
        <div class="w-20 h-20 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center mx-auto mb-4">
            <i class="fas fa-check text-white text-3xl"></i>
        </div>
        <h2 class="text-2xl font-bold text-white mb-2">Payment Successful! 🎉</h2>
        <p class="text-gray-400 mb-4">Thank you for your order!</p>
        <div class="bg-white/5 rounded-lg p-4 mb-6">
            <p class="text-sm text-gray-400">Order Confirmation sent to:</p>
            <p id="success-email" class="text-purple-400 font-semibold">email@example.com</p>
            <p class="text-sm text-gray-400 mt-2">Order Total:</p>
            <p id="success-total" class="text-2xl font-bold text-purple-400">$0.00</p>
        </div>
        <button onclick="closeSuccessModalAndReset()" class="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold text-white hover:opacity-90 transition">
            Continue Shopping
        </button>
    </div>
</div>

<style>
#cart-sidebar.active { transform: translateX(0); }
#cart-sidebar { transition: transform 0.3s ease; }
#cart-toast.show { opacity: 1; }
.cart-count-badge { animation: bounceIn 0.3s ease-out; }
@keyframes bounceIn {
    0% { transform: scale(0); opacity: 0; }
    50% { transform: scale(1.2); }
    100% { transform: scale(1); opacity: 1; }
}
</style>
"""

        cart_script = """
<script>
// ========== CART SYSTEM ==========
let cart = [];

try {
    const saved = localStorage.getItem('eaglecode_cart');
    if (saved) cart = JSON.parse(saved);
} catch(e) { console.error('Failed to load cart:', e); }

function saveCart() {
    localStorage.setItem('eaglecode_cart', JSON.stringify(cart));
    updateCartUI();
    updateCartBadge();
    updateCartPage();
}

function updateCartBadge() {
    const totalItems = cart.reduce((sum, i) => sum + i.quantity, 0);
    document.querySelectorAll('[data-cart-count]').forEach(badge => {
        if (totalItems > 0) {
            badge.textContent = totalItems > 99 ? '99+' : totalItems;
            badge.classList.remove('hidden');
            badge.classList.add('flex');
        } else {
            badge.classList.add('hidden');
            badge.classList.remove('flex');
        }
    });
}

function updateCartUI() {
    const container = document.getElementById('cart-items');
    const totalEl = document.getElementById('cart-total');
    if (!container) return;
    
    if (cart.length === 0) {
        container.innerHTML = '<div class="text-center py-12 text-gray-400">Your cart is empty</div>';
        if (totalEl) totalEl.textContent = '$0.00';
        return;
    }
    
    const total = cart.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    container.innerHTML = cart.map(item => {
        const safeName = item.name.replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
        return `
            <div class="flex gap-4 p-3 bg-white/5 rounded-xl border border-white/10">
                <div class="w-16 h-16 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-lg flex items-center justify-center">
                    <i class="fas fa-shopping-bag text-purple-400"></i>
                </div>
                <div class="flex-1">
                    <h4 class="font-semibold text-white text-sm">${safeName}</h4>
                    <p class="text-purple-400 text-sm">$${item.price.toFixed(2)}</p>
                    <div class="flex items-center gap-2 mt-2">
                        <button onclick="updateQuantity('${item.id}', -1)" class="w-6 h-6 rounded-full bg-white/10 hover:bg-white/20">-</button>
                        <span class="text-white text-sm w-6 text-center">${item.quantity}</span>
                        <button onclick="updateQuantity('${item.id}', 1)" class="w-6 h-6 rounded-full bg-white/10 hover:bg-white/20">+</button>
                        <button onclick="removeFromCart('${item.id}')" class="ml-auto text-red-400 hover:text-red-300 text-sm">Remove</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    if (totalEl) totalEl.textContent = `$${total.toFixed(2)}`;
}

function updateCartPage() {
    const container = document.getElementById('cart-page-items');
    const summary = document.getElementById('cart-summary');
    const emptyMsg = document.getElementById('empty-cart-message');
    if (!container) return;
    if (cart.length === 0) {
        if (summary) summary.classList.add('hidden');
        if (emptyMsg) emptyMsg.classList.remove('hidden');
        container.innerHTML = '';
        return;
    }
    if (summary) summary.classList.remove('hidden');
    if (emptyMsg) emptyMsg.classList.add('hidden');
    const total = cart.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    container.innerHTML = cart.map(item => `
        <div class="flex gap-4 p-4 bg-white/5 rounded-xl border border-white/10">
            <div class="w-20 h-20 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-lg flex items-center justify-center"><i class="fas fa-shopping-bag text-purple-400 text-2xl"></i></div>
            <div class="flex-1">
                <h3 class="font-semibold text-white">${item.name}</h3>
                <p class="text-purple-400">$${item.price.toFixed(2)}</p>
                <div class="flex items-center gap-3 mt-2">
                    <button onclick="updateQuantity('${item.id}', -1)" class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20">-</button>
                    <span>${item.quantity}</span>
                    <button onclick="updateQuantity('${item.id}', 1)" class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20">+</button>
                    <button onclick="removeFromCart('${item.id}')" class="ml-auto text-red-400 hover:text-red-300">Remove</button>
                </div>
            </div>
            <p class="font-bold text-lg">$${(item.price * item.quantity).toFixed(2)}</p>
        </div>
    `).join('');
    document.getElementById('cart-page-subtotal').textContent = '$' + total.toFixed(2);
    document.getElementById('cart-page-total').textContent = '$' + total.toFixed(2);
}

window.addToCart = function(id, name, price) {
    const existing = cart.find(i => i.id === id);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({ id: String(id), name: name, price: Number(price), quantity: 1 });
    }
    saveCart();
    const toast = document.getElementById('cart-toast');
    toast.textContent = name + ' added to cart!';
    toast.classList.add('show');
    setTimeout(function() { toast.classList.remove('show'); }, 2000);
    if (window.innerWidth <= 768) openCartSidebar();
};

window.updateQuantity = function(id, delta) {
    const item = cart.find(i => i.id === id);
    if (item) {
        item.quantity += delta;
        if (item.quantity <= 0) {
            cart = cart.filter(i => i.id !== id);
        }
        saveCart();
    }
};

window.removeFromCart = function(id) {
    cart = cart.filter(i => i.id !== id);
    saveCart();
    const toast = document.getElementById('cart-toast');
    toast.textContent = 'Item removed from cart';
    toast.classList.add('show');
    setTimeout(function() { toast.classList.remove('show'); }, 2000);
};

window.clearCart = function() {
    cart = [];
    saveCart();
    const toast = document.getElementById('cart-toast');
    toast.textContent = 'Cart cleared';
    toast.classList.add('show');
    setTimeout(function() { toast.classList.remove('show'); }, 2000);
};

function openCartSidebar() {
    document.getElementById('cart-sidebar').classList.add('active');
}

window.closeCartSidebar = function() {
    document.getElementById('cart-sidebar').classList.remove('active');
};

// ========== CHECKOUT FUNCTIONS ==========
function openCheckoutModal() {
    if (cart.length === 0) {
        const toast = document.getElementById('cart-toast');
        toast.textContent = 'Your cart is empty';
        toast.classList.add('show');
        setTimeout(function() { toast.classList.remove('show'); }, 2000);
        return;
    }
    const total = cart.reduce(function(s, i) { return s + (i.price * i.quantity); }, 0);
    document.getElementById('checkout-total').textContent = '$' + total.toFixed(2);
    document.getElementById('checkout-modal').style.display = 'flex';
}

function closeCheckoutModal() {
    document.getElementById('checkout-modal').style.display = 'none';
    document.getElementById('checkout-form').reset();
}

function closeSuccessModal() {
    document.getElementById('success-modal').style.display = 'none';
}

function closeSuccessModalAndReset() {
    closeSuccessModal();
    if (typeof showPage === 'function') showPage('shop');
}

function processPayment(event) {
    event.preventDefault();
    const fullName = document.getElementById('full-name').value;
    const email = document.getElementById('email').value;
    
    if (!fullName || !email) {
        const toast = document.getElementById('cart-toast');
        toast.textContent = 'Please fill in all fields';
        toast.classList.add('show');
        setTimeout(function() { toast.classList.remove('show'); }, 2000);
        return;
    }
    if (!email.includes('@')) {
        const toast = document.getElementById('cart-toast');
        toast.textContent = 'Please enter a valid email';
        toast.classList.add('show');
        setTimeout(function() { toast.classList.remove('show'); }, 2000);
        return;
    }
    
    const total = cart.reduce(function(s, i) { return s + (i.price * i.quantity); }, 0);
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    submitBtn.disabled = true;
    
    setTimeout(function() {
        closeCheckoutModal();
        document.getElementById('success-email').textContent = email;
        document.getElementById('success-total').textContent = '$' + total.toFixed(2);
        document.getElementById('success-modal').style.display = 'flex';
        cart = [];
        saveCart();
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        const toast = document.getElementById('cart-toast');
        toast.textContent = 'Payment successful! Thank you!';
        toast.classList.add('show');
        setTimeout(function() { toast.classList.remove('show'); }, 2000);
    }, 1500);
}

function wireAddToCartButtons() {
    document.querySelectorAll('.add-to-cart-btn, [data-add-to-cart]').forEach(function(btn) {
        if (!btn.hasAttribute('data-cart-wired')) {
            btn.setAttribute('data-cart-wired', 'true');
            const id = btn.getAttribute('data-id') || btn.getAttribute('data-product-id') || 'prod_' + Math.random();
            const name = btn.getAttribute('data-name') || btn.getAttribute('data-product-name') || 'Product';
            const price = parseFloat(btn.getAttribute('data-price') || btn.getAttribute('data-product-price') || '29.99');
            btn.onclick = function(e) {
                e.preventDefault();
                addToCart(id, name, price);
            };
        }
    });
}

// Card number formatting
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        updateCartUI();
        updateCartBadge();
        wireAddToCartButtons();
        
        const cardInput = document.getElementById('card-number');
        if (cardInput) {
            cardInput.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\\s/g, '');
                if (value.length > 16) value = value.slice(0, 16);
                let formatted = '';
                for (let i = 0; i < value.length; i++) {
                    if (i > 0 && i % 4 === 0) formatted += ' ';
                    formatted += value[i];
                }
                e.target.value = formatted;
            });
        }
        
        const expiryInput = document.getElementById('expiry');
        if (expiryInput) {
            expiryInput.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\\//g, '');
                if (value.length > 4) value = value.slice(0, 4);
                if (value.length > 2) {
                    value = value.slice(0, 2) + '/' + value.slice(2);
                }
                e.target.value = value;
            });
        }
    });
} else {
    updateCartUI();
    updateCartBadge();
    wireAddToCartButtons();
}

if (window.MutationObserver) {
    const observer = new MutationObserver(function() { wireAddToCartButtons(); });
    observer.observe(document.body, { childList: true, subtree: true });
}
</script>
"""

        # ========== AUTH HANDLER SCRIPT ==========
        auth_script = f"""
<script>
const BACKEND_URL = "{BACKEND_URL}";

// Get connection string directly from localStorage
function getDbConnection() {{
    let conn = localStorage.getItem("neon_db_connection");
    if (!conn) {{
        conn = sessionStorage.getItem("neon_db_connection");
    }}
    return conn;
}}

async function handleSignup(event) {{
    event.preventDefault();
    const form = event.target;
    const name = form.querySelector('[name="name"], [name="fullName"]')?.value || '';
    const email = form.querySelector('[name="email"]')?.value;
    const password = form.querySelector('[name="password"]')?.value;
    const confirmPassword = form.querySelector('[name="confirmPassword"]')?.value;
    
    // Get connection string directly
    const dbConnection = getDbConnection();
    console.log("🔑 DB Connection found:", dbConnection ? "Yes ✅" : "No ❌");
    
    if (!dbConnection) {{
        alert('❌ Database not connected. Please add your Neon DB connection string first.\\n\\nOpen console and run:\\nlocalStorage.setItem("neon_db_connection", "your-connection-string")');
        return;
    }}
    
    if (password !== confirmPassword) {{
        alert('❌ Passwords do not match');
        return;
    }}
    if (password.length < 6) {{
        alert('❌ Password must be at least 6 characters');
        return;
    }}
    
    const submitBtn = form.querySelector('[type="submit"]');
    const originalText = submitBtn?.innerText || 'Sign Up';
    if (submitBtn) submitBtn.innerText = 'Creating account...';
    
    try {{
        const response = await fetch(`${{BACKEND_URL}}/api/auth/signup`, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ 
                name, 
                email, 
                password, 
                db_connection_string: dbConnection 
            }})
        }});
        const data = await response.json();
        console.log("📡 Signup response:", data);
        
        if (data.success) {{
            alert('✅ Account created successfully! You can now log in.');
            form.reset();
            setTimeout(() => {{
                const loginLink = document.querySelector('a[href="/login"]');
                if (loginLink && typeof showPage === 'function') {{
                    showPage('login');
                }}
            }}, 1500);
        }} else if (data.requires_db) {{
            alert('❌ Database not configured. Please add your Neon DB connection string first.');
        }} else {{
            alert('❌ ' + (data.error || 'Signup failed'));
        }}
    }} catch (error) {{
        console.error('Signup error:', error);
        alert('❌ Network error. Make sure backend is running');
    }} finally {{
        if (submitBtn) submitBtn.innerText = originalText;
    }}
}}

async function handleLogin(event) {{
    event.preventDefault();
    const form = event.target;
    const email = form.querySelector('[name="email"]')?.value;
    const password = form.querySelector('[name="password"]')?.value;
    
    // Get connection string directly
    const dbConnection = getDbConnection();
    if (!dbConnection) {{
        alert('❌ Database not connected. Please add your Neon DB connection string first.');
        return;
    }}
    
    const submitBtn = form.querySelector('[type="submit"]');
    const originalText = submitBtn?.innerText || 'Login';
    if (submitBtn) submitBtn.innerText = 'Logging in...';
    
    try {{
        const response = await fetch(`${{BACKEND_URL}}/api/auth/login`, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ 
                email, 
                password, 
                db_connection_string: dbConnection 
            }})
        }});
        const data = await response.json();
        
        if (data.success) {{
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            alert('✅ Login successful! Welcome ' + (data.user.name || data.user.email));
            setTimeout(() => {{
                if (typeof showPage === 'function') showPage('home');
            }}, 1000);
        }} else if (data.requires_db) {{
            alert('❌ Database not configured. Please add your Neon DB connection string first.');
        }} else {{
            alert('❌ ' + (data.error || 'Login failed'));
        }}
    }} catch (error) {{
        console.error('Login error:', error);
        alert('❌ Network error. Make sure backend is running');
    }} finally {{
        if (submitBtn) submitBtn.innerText = originalText;
    }}
}}

// Listen for database connection from parent window (for iframe preview)
window.addEventListener('message', function(event) {{
    if (event.data && event.data.type === 'SET_DB_CONNECTION') {{
        localStorage.setItem('neon_db_connection', event.data.db_connection);
        console.log('✅ DB Connection received from parent');
    }}
}});

document.addEventListener('DOMContentLoaded', function() {{
    // Request connection string from parent if not present
    if (!getDbConnection() && window.parent !== window) {{
        window.parent.postMessage({{ type: 'GET_DB_CONNECTION' }}, '*');
    }}
    
    document.querySelectorAll('form').forEach(form => {{
        const hasPassword = form.querySelector('[type="password"]');
        const hasEmail = form.querySelector('[type="email"]');
        const submitText = form.querySelector('[type="submit"]')?.innerText?.toLowerCase() || '';
        const formId = form.id?.toLowerCase() || '';
        
        const isSignupForm = formId.includes('signup') || submitText.includes('sign') || submitText.includes('up') || (form.querySelector('[name="name"]') && hasPassword && hasEmail);
        const isLoginForm = formId.includes('login') || submitText.includes('log') || submitText.includes('in') || (!form.querySelector('[name="name"]') && hasPassword && hasEmail);
        
        if ((isSignupForm || isLoginForm) && !form.onsubmit) {{
            if (isSignupForm) form.onsubmit = handleSignup;
            else if (isLoginForm) form.onsubmit = handleLogin;
        }}
    }});
}});
</script>
"""

        # ========== INJECT CART SYSTEM FIRST, THEN AUTH ==========
        # Inject cart HTML and sidebar
        if '</body>' in preview_html:
            preview_html = preview_html.replace('</body>', f'{cart_html}\n</body>')
        
        # Inject cart JavaScript
        if '</body>' in preview_html:
            preview_html = preview_html.replace('</body>', f'{cart_script}\n</body>')
        
        # Inject auth script
        if '</body>' in preview_html:
            preview_html = preview_html.replace('</body>', f'{auth_script}\n</body>')
        else:
            preview_html = preview_html + auth_script
            
        # Fix ShieldCheck icon one more time to be safe
        preview_html = preview_html.replace('fa-shield-check', 'fa-shield-alt')           

        print(f"✅ Beautiful preview generated! Length: {len(preview_html):,} chars")
        return {"success": True, "preview_html": preview_html, "preview_type": "ai_full"}
    
    
    
    
    

    except Exception as e:
        print(f"❌ AI Preview Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    
    
    
    
  
























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
    
    
    
    
    
    
    # ⭐⭐⭐ FIX THE TEMPLATE LITERAL PATTERN FROM TESTIMONIALS ⭐⭐⭐
    # This pattern: {`"${testimonial.quote}"`}
    # Should become: "testimonial quote text" (a valid JSON string)
    text = re.sub(
        r'\{`"\$\{([^}]+)\}"`\}',
        r'"\1"',
        text
    )
    # Also fix pattern with spaces: { `"${testimonial.quote}"` }
    text = re.sub(
        r'\{\s*`"\$\{([^}]+)\}"`\s*\}',
        r'"\1"',
        text
    )
    # Fix pattern: {`${testimonial.quote}`}
    text = re.sub(
        r'\{`\$\{([^}]+)\}`\}',
        r'"\1"',
        text
    )
    # Fix pattern with just backticks: {`text`}
    text = re.sub(
        r'\{`([^`]+)`\}',
        r'"\1"',
        text
    )
    # Remove any remaining backticks
    text = text.replace('`', '"')
    
    
    
    
    
    
    
    
    # 2. ⭐⭐⭐ CRITICAL: Fix escaped apostrophes FIRST (most common issue)
    # Replace \' with ' (apostrophes don't need escaping in JSON)
    text = text.replace("\\'", "'")
    
    # 3. ⭐ NEW: Fix common contractions with escaped apostrophes
    # Pattern: it\'s -> it's, won\'t -> won't, don\'t -> don't, etc.
    text = re.sub(r"it\\'s", "it's", text)
    text = re.sub(r"won\\'t", "won't", text)
    text = re.sub(r"don\\'t", "don't", text)
    text = re.sub(r"can\\'t", "can't", text)
    text = re.sub(r"that\\'s", "that's", text)
    text = re.sub(r"what\\'s", "what's", text)
    text = re.sub(r"there\\'s", "there's", text)
    text = re.sub(r"we\\'ll", "we'll", text)
    text = re.sub(r"they\\'re", "they're", text)
    text = re.sub(r"you\\'re", "you're", text)
    text = re.sub(r"([a-zA-Z])\\'([a-zA-Z])", r"\1'\2", text)
    text = re.sub(r"n\\'t", r"n't", text)
    
    # 4. ⭐ Fix escaped quotes next
    text = text.replace('\\"', '"')
    
    # 5. Fix template literals and backticks
    text = text.replace('`', '"')
    # Fix ${...} template expressions like `${testimonial.quote}`
    text = re.sub(r'\$\{([^}]+)\}', r'\\"\1\\"', text)
    # Fix patterns like {`"text"`} or {`text`}
    text = re.sub(r'\{\s*"[^"]*"\s*\}', r'""', text)
    text = re.sub(r'\{\s*`[^`]*`\s*\}', r'""', text)
    
    # 6. Fix invalid backslashes - the #1 cause of "Invalid \escape"
    # Replace any \ that is not followed by a valid JSON escape character
    valid_escapes = r'["\\/bfnrtu]'
    text = re.sub(r'\\(?!' + valid_escapes + r')', r'\\\\', text)
    
    # 7. Fix double backslashes
    text = text.replace("\\\\", "\\")
    
    # 8. Fix unescaped double quotes inside string values (very common with Gemini)
    def safe_escape_quotes(match):
        # match.group(1) = content inside the quotes
        content = match.group(1)
        # First, restore any properly escaped quotes we might have broken
        content = content.replace('\\"', '"')
        # Escape any " that isn't already escaped
        content = re.sub(r'(?<!\\)"', r'\\"', content)
        return '"' + content + '"'
    
    # Apply to all "..." strings
    text = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', safe_escape_quotes, text)
    
    # 9. Remove trailing commas (very frequent)
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
    
    # 10. Fix missing quotes around property names
    text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)
    
    # 11. Remove BOM and invisible characters
    text = text.encode('utf-8').decode('utf-8-sig')
    
    # 12. Final cleanup - remove any stray control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # 13. If the JSON looks broken at the start, try to extract the object
    if text and not text.startswith('{'):
        json_match = re.search(r'(\{[\s\S]*\})', text)
        if json_match:
            text = json_match.group(1)
    
    # 14. Fix any remaining unescaped backslashes before quotes
    text = re.sub(r"([a-zA-Z])\\'([a-zA-Z])", r"\1'\2", text)
    
    # 15. Fix line breaks in strings (replace actual newlines with \n)
    def fix_newlines_in_strings(match):
        content = match.group(1)
        # Replace actual newlines with \n escape
        content = content.replace('\n', '\\n').replace('\r', '\\r')
        return '"' + content + '"'
    
    # Apply to strings that might contain unescaped newlines
    text = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', fix_newlines_in_strings, text)
    
    # 16. Remove any leftover control characters in strings
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # 17. Fix common HTML entities in strings
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', "'")
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    
    # 18. Fix any remaining escaped backticks or template strings
    text = re.sub(r'\\`', '"', text)
    text = re.sub(r'\\\$', '$', text)
    
    # 19. Remove any remaining JSON-invalid control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # 20. ⭐ FINAL PASS: Fix any missed escaped apostrophes
    # This catches edge cases like 'it\'s' that might have survived
    text = re.sub(r"'\\'([^']+)'", r"'\1'", text)
    text = re.sub(r'"\\\'([^"]+)"', r'"\1"', text)
    
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










================================================================================
🚨 E-COMMERCE CART SYSTEM - REQUIRED FOR SHOP/CART PAGES 🚨
================================================================================

When generating an E-COMMERCE website, you MUST include the complete cart system.

================================================================================
PRODUCT BUTTON FORMAT (CRITICAL):
================================================================================

Each product button MUST have these EXACT data attributes:

✅ CORRECT:
```html
<button class="add-to-cart-btn" 
        data-id="prod_1" 
        data-name="Premium Hoodie" 
        data-price="49.99">
    Add to Cart
</button>


❌ WRONG (missing attributes):
<button class="add-to-cart-btn">Add to Cart</button>




================================================================================
SHOP PAGE PRODUCTS (6 Products Minimum):
================================================================================


Generate at least 6 products on the shop page with:


<div class="grid md:grid-cols-3 gap-8">
    <!-- Product 1 -->
    <div class="product-card">
        <div class="product-image mb-4">
            <i data-lucide="shopping-bag" class="w-16 h-16 text-purple-400 mx-auto"></i>
        </div>
        <div class="product-info">
            <h3 class="product-title text-xl font-bold">Product Name 1</h3>
            <p class="product-price text-purple-400 text-2xl font-bold">$49.99</p>
            <button class="add-to-cart-btn" data-id="1" data-name="Product Name 1" data-price="49.99">Add to Cart</button>
        </div>
    </div>
    <!-- Product 2 through 6 with different ids and names -->
</div>






================================================================================
CART PAGE STRUCTURE (app/cart/page.tsx):
================================================================================
'use client';

import { useCart } from '@/contexts/CartContext';
import Link from 'next/link';
import { Trash2, ShoppingBag } from 'lucide-react';

export default function CartPage() {
    const { items, removeFromCart, updateQuantity, getCartTotal } = useCart();
    
    if (items.length === 0) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <ShoppingBag className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold mb-4">Your cart is empty</h2>
                    <Link href="/shop" className="px-6 py-3 bg-purple-600 rounded-lg">Continue Shopping</Link>
                </div>
            </div>
        );
    }
    
    return (
        <div className="container mx-auto px-4 py-12">
            <h1 className="text-3xl font-bold mb-8">Shopping Cart</h1>
            <div className="grid lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-4">
                    {items.map(item => (
                        <div key={item.id} className="flex gap-4 p-4 bg-white/5 rounded-xl border border-white/10">
                            <div className="w-20 h-20 bg-purple-500/20 rounded-lg flex items-center justify-center">
                                {item.image ? <img src={item.image} className="w-full h-full object-cover rounded-lg" /> : <ShoppingBag className="w-8 h-8 text-purple-400" />}
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold">{item.name}</h3>
                                <p className="text-purple-400">${item.price.toFixed(2)}</p>
                                <div className="flex items-center gap-3 mt-2">
                                    <button onClick={() => updateQuantity(item.id, item.quantity - 1)} className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20">-</button>
                                    <span>{item.quantity}</span>
                                    <button onClick={() => updateQuantity(item.id, item.quantity + 1)} className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20">+</button>
                                    <button onClick={() => removeFromCart(item.id)} className="ml-auto text-red-400 hover:text-red-300"><Trash2 className="w-4 h-4" /></button>
                                </div>
                            </div>
                            <p className="font-bold text-lg">${(item.price * item.quantity).toFixed(2)}</p>
                        </div>
                    ))}
                </div>
                <div className="bg-white/5 rounded-xl p-6 h-fit">
                    <h3 className="text-xl font-bold mb-4">Order Summary</h3>
                    <div className="flex justify-between mb-2"><span>Subtotal</span><span>${getCartTotal().toFixed(2)}</span></div>
                    <div className="flex justify-between mb-2"><span>Shipping</span><span className="text-green-400">Free</span></div>
                    <div className="border-t border-white/10 my-4"></div>
                    <div className="flex justify-between font-bold text-lg mb-6"><span>Total</span><span>${getCartTotal().toFixed(2)}</span></div>
                    <button onClick={() => window.dispatchEvent(new CustomEvent('openCheckout'))} className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold">Proceed to Checkout</button>
                </div>
            </div>
        </div>
    );
}






================================================================================
NAVIGATION CART BADGE (components/Navigation.tsx):
================================================================================



Add to your cart link:



<button onClick={() => setIsCartOpen(true)} className="relative">
    <ShoppingBag className="w-5 h-5" />
    {getTotalItems() > 0 && (
        <span className="absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full flex items-center justify-center px-1">
            {getTotalItems() > 99 ? '99+' : getTotalItems()}
        </span>
    )}
</button>


================================================================================
REQUIRED FILES FOR E-COMMERCE:
================================================================================


1. contexts/CartContext.tsx - Cart state management

2. components/CartSidebar.tsx - Slide-out cart

3. app/shop/page.tsx - Product listing page

4. app/cart/page.tsx - Cart page

5. app/layout.tsx - Wrap with CartProvider and include CartSidebar






================================================================================
CART FEATURES THAT MUST WORK:
================================================================================

Cart badge updates instantly

Cart sidebar slides out with items

Quantity can be increased/decreased

Items can be removed

Total price updates in real-time

Cart persists after page refresh

Checkout button shows payment modal

Payment modal has form validation

Success modal shows after payment

Cart clears after successful payment


This prompt ensures the AI generates proper e-commerce websites with:
1. ✅ Products with correct `data-id`, `data-name`, `data-price` attributes
2. ✅ Working Add to Cart buttons
3. ✅ Cart badge that updates
4. ✅ Cart sidebar with items
5. ✅ Cart page with order summary
6. ✅ Checkout modal with payment form
7. ✅ Success modal after payment
8. ✅ LocalStorage persistence














































================================================================================
🛒 CART SYSTEM - MUST IMPLEMENT IN EVERY E-COMMERCE PROJECT
================================================================================

For ANY project with Shop/Store/Products pages, you MUST:

1. Import useCart in shop/product pages:
```tsx
import { useCart } from '../../context/CartContext';
```

2. Add "Add to Cart" buttons that actually work:
```tsx
const { addToCart, count } = useCart();

<button
  onClick={() => addToCart({ id: product.id, name: product.name, price: product.price })}
  className="px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 transition"
>
  Add to Cart
</button>
```

3. Show cart count in Navigation:
```tsx
import { useCart } from '../context/CartContext';

const { count } = useCart();

<Link href="/cart" className="relative">
  <ShoppingBag className="w-5 h-5" />
  {count > 0 && (
    <span className="absolute -top-2 -right-2 bg-purple-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
      {count}
    </span>
  )}
</Link>
```

4. Create a WORKING cart page at `app/cart/page.tsx`:
```tsx
'use client';
import { useCart } from '../../context/CartContext';
import Link from 'next/link';

export default function CartPage() {
  const { items, removeFromCart, updateQuantity, total, clearCart } = useCart();

  if (items.length === 0) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Your cart is empty</h2>
          <Link href="/shop" className="px-6 py-3 bg-purple-600 rounded-lg hover:bg-purple-700">
            Continue Shopping
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20 container mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-8">Shopping Cart ({items.length} items)</h1>
      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          {items.map(item => (
            <div key={item.id} className="flex items-center gap-4 bg-white/5 rounded-xl p-4 border border-white/10">
              <div className="flex-1">
                <h3 className="font-semibold">{item.name}</h3>
                <p className="text-purple-400">${item.price}</p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => updateQuantity(item.id, item.quantity - 1)}
                  className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center">−</button>
                <span className="w-8 text-center">{item.quantity}</span>
                <button onClick={() => updateQuantity(item.id, item.quantity + 1)}
                  className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center">+</button>
              </div>
              <p className="font-bold w-20 text-right">${(item.price * item.quantity).toFixed(2)}</p>
              <button onClick={() => removeFromCart(item.id)} className="text-red-400 hover:text-red-300">✕</button>
            </div>
          ))}
        </div>
        <div className="bg-white/5 rounded-xl p-6 border border-white/10 h-fit">
          <h3 className="text-xl font-bold mb-4">Order Summary</h3>
          <div className="flex justify-between mb-2"><span>Subtotal</span><span>${total.toFixed(2)}</span></div>
          <div className="flex justify-between mb-2"><span>Shipping</span><span>Free</span></div>
          <div className="border-t border-white/10 my-4"></div>
          <div className="flex justify-between font-bold text-lg mb-6"><span>Total</span><span>${total.toFixed(2)}</span></div>
          <button className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold hover:opacity-90 transition">
            Checkout
          </button>
          <button onClick={clearCart} className="w-full py-2 mt-3 text-sm text-gray-400 hover:text-white transition">
            Clear Cart
          </button>
        </div>
      </div>
    </div>
  );
}







================================================================================
🚨 FEATURES SECTION - MUST HAVE HEADING 🚨
================================================================================

The Features section MUST include a heading "Features" before the grid.

REQUIRED STRUCTURE:
```html
<section className="py-20 px-4">
  <div className="container mx-auto">
    <h2 className="text-4xl font-bold text-center mb-12 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
      Features
    </h2>
    <div className="grid md:grid-cols-3 gap-8">
      <!-- Feature cards here -->
    </div>
  </div>
</section>
















================================================================================
🚨 FAQ SECTION REQUIREMENTS - MUST FOLLOW EXACTLY 🚨
================================================================================

When generating the FAQ section, you MUST use this EXACT pattern:

1. **Define FAQ array at top of component:**
```tsx
const faqs = [
  { q: "Question 1?", a: "Answer 1" },
  { q: "Question 2?", a: "Answer 2" },
  { q: "Question 3?", a: "Answer 3" }
];















================================================================================
🚨 COMPLETE WEBSITE SECTIONS - MUST GENERATE ALL 7 SECTIONS 🚨
================================================================================

Generate a COMPLETE, PREMIUM Next.js 14 home page (app/page.tsx) with ALL 7 sections below.
EACH SECTION MUST HAVE REAL CONTENT - NO PLACEHOLDERS OR EMPTY DIVS.

================================================================================
SECTION 1: HERO SECTION - FULL SCREEN WITH IMAGE
================================================================================

REQUIRED STRUCTURE:
```tsx
<section className="relative h-screen flex items-center justify-center overflow-hidden">
  <img 
    src="/images/image_1.jpg" 
    alt="Hero background" 
    className="absolute inset-0 w-full h-full object-cover" 
    onError={(e) => { 
      e.currentTarget.style.display = 'none'; 
      e.currentTarget.parentElement?.classList.add('bg-gradient-to-br', 'from-purple-950', 'to-pink-950'); 
    }} 
  />
  <div className="absolute inset-0 bg-black/50" />
  <div className="relative z-10 text-center px-4 max-w-4xl mx-auto">
    <span className="inline-block px-4 py-1 rounded-full bg-purple-500/20 text-purple-300 text-sm mb-4 backdrop-blur-sm">LIMITED EDITION</span>
    <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">[BRAND NAME]</h1>
    <p className="text-lg md:text-xl text-gray-200 mb-8 max-w-2xl mx-auto">[UNIQUE TAGLINE - 10-15 WORDS DESCRIBING THE BRAND]</p>
    <div className="flex gap-4 justify-center">
      <Link href="/shop" className="px-8 py-3 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold hover:scale-105 transition-all duration-300 shadow-lg shadow-purple-500/25">
        Shop Now →
      </Link>
      <Link href="/catalog" className="px-8 py-3 rounded-full border border-white/30 text-white font-semibold hover:bg-white/10 transition-all duration-300">
        View Collection
      </Link>
    </div>
  </div>
</section>



================================================================================
SECTION 2: FEATURES SECTION - 4 CARDS WITH ICONS
================================================================================

REQUIRED STRUCTURE:
'''tsx
<section className="py-20 px-4 bg-gradient-to-br from-purple-950/20 via-transparent to-pink-950/20">
  <div className="container mx-auto">
    <div className="text-center mb-12">
      <span className="text-purple-400 text-sm uppercase tracking-wider">Why Choose Us</span>
      <h2 className="text-3xl md:text-4xl font-bold mt-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
        Premium Features
      </h2>
      <p className="text-gray-400 mt-4 max-w-2xl mx-auto">Experience excellence with our premium services</p>
    </div>
    
    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[
        { icon: Truck, title: "Free Shipping", desc: "Free delivery on orders over $50", color: "from-blue-500 to-cyan-500" },
        { icon: ShieldCheck, title: "Secure Payment", desc: "100% secure transactions", color: "from-green-500 to-emerald-500" },
        { icon: Headphones, title: "24/7 Support", desc: "Round-the-clock assistance", color: "from-purple-500 to-pink-500" },
        { icon: Star, title: "Premium Quality", desc: "Handpicked premium products", color: "from-yellow-500 to-orange-500" }
      ].map((feature, idx) => (
        <div key={idx} className="group relative bg-gradient-to-br from-white/5 to-white/3 rounded-2xl p-6 backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300 hover:-translate-y-1">
          <div className={`w-14 h-14 rounded-xl bg-gradient-to-r ${feature.color} flex items-center justify-center mb-4 shadow-lg`}>
            <feature.icon className="w-7 h-7 text-white" />
          </div>
          <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
          <p className="text-gray-400 text-sm">{feature.desc}</p>
        </div>
      ))}
    </div>
  </div>
</section>



================================================================================
SECTION 3: TESTIMONIALS SECTION - 3 UNIQUE REVIEWS
================================================================================

REQUIRED STRUCTURE:
'''tsx
<section className="py-20 px-4">
  <div className="container mx-auto">
    <div className="text-center mb-12">
      <span className="text-purple-400 text-sm uppercase tracking-wider">Testimonials</span>
      <h2 className="text-3xl md:text-4xl font-bold mt-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
        What Our Customers Say
      </h2>
    </div>
    
    <div className="grid md:grid-cols-3 gap-6">
      {[
        { quote: "Absolutely love this brand! The quality is exceptional and customer service is top-notch.", name: "Sarah Johnson", role: "Verified Buyer", rating: 5, initial: "S" },
        { quote: "Fast shipping and beautiful packaging. Will definitely order again!", name: "Michael Chen", role: "Repeat Customer", rating: 5, initial: "M" },
        { quote: "Great products at reasonable prices. The attention to detail is impressive.", name: "Emily Rodriguez", role: "Happy Customer", rating: 4, initial: "E" }
      ].map((testimonial, idx) => (
        <div key={idx} className="bg-gradient-to-br from-white/5 to-white/3 rounded-2xl p-6 backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300">
          <div className="flex gap-1 mb-4">
            {[...Array(5)].map((_, i) => (
              <Star key={i} className={`w-4 h-4 ${i < testimonial.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'}`} />
            ))}
          </div>
          <p className="text-gray-300 mb-6 italic">"{testimonial.quote}"</p>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <span className="text-white font-bold">{testimonial.initial}</span>
            </div>
            <div>
              <h4 className="font-semibold text-white">{testimonial.name}</h4>
              <p className="text-xs text-purple-400">{testimonial.role}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
</section>




================================================================================
SECTION 4: STATS SECTION - 4 IMPRESSIVE NUMBERS
================================================================================

REQUIRED STRUCTURE:
'''tsx
<section className="py-20 px-4 bg-gradient-to-r from-purple-950/50 to-pink-950/50">
  <div className="container mx-auto">
    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
      {[
        { number: "5000+", label: "Happy Customers", icon: "😊" },
        { number: "50+", label: "Countries Served", icon: "🌍" },
        { number: "10K+", label: "Products Sold", icon: "📦" },
        { number: "24/7", label: "Customer Support", icon: "💬" }
      ].map((stat, idx) => (
        <div key={idx} className="text-center group">
          <div className="text-4xl mb-2">{stat.icon}</div>
          <div className="text-3xl md:text-4xl font-bold text-white mb-2">{stat.number}</div>
          <p className="text-gray-400 text-sm">{stat.label}</p>
        </div>
      ))}
    </div>
  </div>
</section>








================================================================================
SECTION 5: FAQ SECTION - ACCORDION WITH 4 QUESTIONS
================================================================================

REQUIRED STRUCTURE (MUST HAVE 'use client'):
'''tsx
'use client';

import { useState } from 'react';
import { Plus, Minus } from 'lucide-react';

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState(null);

  const faqs = [
    { q: "What is your shipping policy?", a: "We offer free shipping on orders over $50. Standard shipping takes 3-5 business days." },
    { q: "How do I track my order?", a: "Once your order ships, you'll receive a tracking number via email." },
    { q: "What is your return policy?", a: "We accept returns within 30 days of purchase for a full refund." },
    { q: "Do you ship internationally?", a: "Yes, we ship to over 50 countries worldwide." }
  ];

  return (
    <section className="py-20 px-4">
      <div className="container mx-auto max-w-3xl">
        <div className="text-center mb-12">
          <span className="text-purple-400 text-sm uppercase tracking-wider">FAQ</span>
          <h2 className="text-3xl md:text-4xl font-bold mt-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            Frequently Asked Questions
          </h2>
        </div>
        
        <div className="space-y-4">
          {faqs.map((faq, idx) => (
            <div key={idx} className="bg-gradient-to-br from-white/5 to-white/3 rounded-2xl border border-white/10 overflow-hidden">
              <button
                onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
                className="w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors"
              >
                <span className="font-semibold text-white">{faq.q}</span>
                {openIndex === idx ? <Minus className="w-5 h-5 text-purple-400" /> : <Plus className="w-5 h-5 text-purple-400" />}
              </button>
              {openIndex === idx && (
                <div className="px-6 pb-4 text-gray-400">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}






================================================================================
SECTION 6: FOOTER - COMPLETE WITH SCROLL TO TOP
================================================================================

Generate a PREMIUM Footer component at "components/Footer.tsx" with ALL requirements below.

================================================================================
FILE STRUCTURE (MUST FOLLOW EXACTLY):
================================================================================

```tsx
'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { 
  Heart, Mail, Phone, MapPin, Send, 
  Facebook, Twitter, Instagram, Youtube, 
  Sparkles, ArrowUp 
} from 'lucide-react';

export default function Footer() {
  const [email, setEmail] = useState('');
  const [showScrollTop, setShowScrollTop] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 500);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      alert(`Thank you for subscribing with: ${email}`);
      setEmail('');
    }
  };

  const currentYear = new Date().getFullYear();

  return (
    <>
      {/* Scroll to Top Button */}
      {showScrollTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-8 right-8 z-50 w-12 h-12 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30 hover:scale-110 transition-all duration-300 flex items-center justify-center group"
          aria-label="Scroll to top"
        >
          <ArrowUp className="w-5 h-5 group-hover:-translate-y-1 transition-transform" />
        </button>
      )}

      <footer className="relative mt-20 overflow-hidden">
        {/* Decorative top border with gradient */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-purple-500 to-transparent" />
        
        {/* Glowing background orbs */}
        <div className="absolute top-20 -left-20 w-72 h-72 bg-purple-500/20 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-20 -right-20 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '2s' }} />
        
        {/* Subtle grid pattern overlay */}
        <div 
          className="absolute inset-0 opacity-5 pointer-events-none"
          style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(139, 92, 246, 0.3) 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }}
        />
        
        {/* Main Footer Content */}
        <div className="relative z-10 bg-gradient-to-t from-black via-black/95 to-transparent backdrop-blur-sm">
          <div className="container mx-auto px-4 py-12 md:py-16">
            
            {/* 4-Column Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
              
              {/* COLUMN 1: Brand Section */}
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/25">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                      {{PROJECT_NAME}}
                    </h3>
                    <p className="text-[10px] tracking-[0.2em] text-purple-400/60 uppercase">PREMIUM COLLECTION</p>
                  </div>
                </div>
                <p className="text-sm text-gray-400 leading-relaxed">
                  Discover premium quality products crafted with passion, innovation, and attention to detail. Experience excellence in every purchase.
                </p>
                <div className="flex gap-3 pt-2">
                  <a href="#" className="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center hover:bg-purple-600/30 transition-all group">
                    <Facebook className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors" />
                  </a>
                  <a href="#" className="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center hover:bg-purple-600/30 transition-all group">
                    <Twitter className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors" />
                  </a>
                  <a href="#" className="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center hover:bg-purple-600/30 transition-all group">
                    <Instagram className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors" />
                  </a>
                  <a href="#" className="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center hover:bg-purple-600/30 transition-all group">
                    <Youtube className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors" />
                  </a>
                </div>
              </div>
              
              {/* COLUMN 2: Quick Links */}
              <div>
                <h4 className="text-white font-semibold mb-4 text-lg">Quick Links</h4>
                <ul className="space-y-3">
                  <li>
                    <Link href="/shop" className="text-gray-400 hover:text-purple-400 transition-colors text-sm flex items-center gap-2 group">
                      <span className="w-1 h-1 rounded-full bg-purple-400 opacity-0 group-hover:opacity-100 transition-opacity"></span>
                      Shop
                    </Link>
                  </li>
                  <li>
                    <Link href="/catalog" className="text-gray-400 hover:text-purple-400 transition-colors text-sm flex items-center gap-2 group">
                      <span className="w-1 h-1 rounded-full bg-purple-400 opacity-0 group-hover:opacity-100 transition-opacity"></span>
                      Catalog
                    </Link>
                  </li>
                  <li>
                    <Link href="/about" className="text-gray-400 hover:text-purple-400 transition-colors text-sm flex items-center gap-2 group">
                      <span className="w-1 h-1 rounded-full bg-purple-400 opacity-0 group-hover:opacity-100 transition-opacity"></span>
                      About Us
                    </Link>
                  </li>
                  <li>
                    <Link href="/contact" className="text-gray-400 hover:text-purple-400 transition-colors text-sm flex items-center gap-2 group">
                      <span className="w-1 h-1 rounded-full bg-purple-400 opacity-0 group-hover:opacity-100 transition-opacity"></span>
                      Contact
                    </Link>
                  </li>
                </ul>
              </div>
              
              {/* COLUMN 3: Contact Info */}
              <div>
                <h4 className="text-white font-semibold mb-4 text-lg">Contact Info</h4>
                <ul className="space-y-4">
                  <li className="flex items-center gap-3 text-gray-400 text-sm group">
                    <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center group-hover:bg-purple-500/20 transition-colors">
                      <Mail className="w-4 h-4 text-purple-400" />
                    </div>
                    <span>support@{{PROJECT_NAME_LOWER}}.com</span>
                  </li>
                  <li className="flex items-center gap-3 text-gray-400 text-sm group">
                    <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center group-hover:bg-purple-500/20 transition-colors">
                      <Phone className="w-4 h-4 text-purple-400" />
                    </div>
                    <span>+1 (555) 123-4567</span>
                  </li>
                  <li className="flex items-center gap-3 text-gray-400 text-sm group">
                    <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center group-hover:bg-purple-500/20 transition-colors">
                      <MapPin className="w-4 h-4 text-purple-400" />
                    </div>
                    <span>123 Premium Boulevard, New York, NY 10001</span>
                  </li>
                </ul>
              </div>
              
              {/* COLUMN 4: Newsletter Signup */}
              <div>
                <h4 className="text-white font-semibold mb-4 text-lg">Newsletter</h4>
                <p className="text-gray-400 text-sm mb-4">
                  Subscribe to get 10% off your first order and receive exclusive offers!
                </p>
                <form onSubmit={handleSubscribe} className="space-y-3">
                  <div className="relative">
                    <input 
                      type="email" 
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter your email" 
                      required
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all placeholder:text-gray-600"
                    />
                    <Send className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                  </div>
                  <button 
                    type="submit" 
                    className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all duration-300 font-semibold text-sm shadow-lg shadow-purple-500/25"
                  >
                    Subscribe Now
                  </button>
                </form>
              </div>
            </div>
            
            {/* Bottom Bar - Copyright & Legal Links */}
            <div className="border-t border-white/10 mt-12 pt-8">
              <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                <div className="flex gap-6">
                  <Link href="/privacy" className="text-gray-500 hover:text-purple-400 transition-colors text-xs">
                    Privacy Policy
                  </Link>
                  <Link href="/terms" className="text-gray-500 hover:text-purple-400 transition-colors text-xs">
                    Terms of Service
                  </Link>
                  <Link href="/shipping" className="text-gray-500 hover:text-purple-400 transition-colors text-xs">
                    Shipping Info
                  </Link>
                </div>
                <p className="text-gray-500 text-sm flex items-center gap-1">
                  © {currentYear} {{PROJECT_NAME}}. Crafted with 
                  <Heart className="w-3 h-3 text-red-500 inline animate-pulse mx-1" /> 
                  in Nairobi
                </p>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
    
    
    
    
    
    
    
================================================================================
CSS ANIMATIONS NEEDED IN GLOBALS.CSS:
================================================================================


@keyframes pulse-slow {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
.animate-pulse-slow {
  animation: pulse-slow 3s ease-in-out infinite;
}



================================================================================
VERIFICATION BEFORE OUTPUT:
================================================================================

1. Does the home page include all 7 sections with real content?
2. Are all sections styled with gradients, hover effects, and premium design elements?
3. Copyright year updates automatically
4. Social icons have hover effects

































================================================================================
PREMIUM E-COMMERCE HOME PAGE REQUIREMENTS:
================================================================================

Generate app/page.tsx with:

1. **Hero Section**: Full-screen with gradient overlay, brand name, tagline, CTA buttons
2. **Features Section**: 3-4 premium features with icons (e.g., "Free Shipping", "24/7 Support", "Premium Quality")
3. **Featured Products**: Grid of 3-6 products with:
   - Image placeholder (SVG or gradient)
   - Product name, price, short description
   - Hover effect with "Add to Cart" button
4. **Testimonials**: 2-3 customer reviews with avatars (initials in circles)
5. **Newsletter Signup**: Glass card with email input and subscribe button
6. **Stats Section**: 3 stats (e.g., "5000+ Customers", "50+ Countries", "10K+ Products")

Example Featured Products section:
```tsx
<section className="py-20 px-4">
  <div className="container mx-auto">
    <div className="text-center mb-12">
      <span className="text-purple-400 text-sm uppercase tracking-wider">Featured</span>
      <h2 className="text-3xl md:text-4xl font-bold mt-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
        Best Sellers
      </h2>
      <p className="text-gray-400 mt-4">Discover our most popular products</p>
    </div>
    
    <div className="grid md:grid-cols-3 gap-8">
      {[1, 2, 3].map((item) => (
        <div key={item} className="group relative bg-gradient-to-br from-white/5 to-white/3 rounded-2xl p-6 backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300">
          <div className="w-full h-48 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl mb-4 flex items-center justify-center group-hover:scale-105 transition-transform">
            <svg className="w-16 h-16 text-purple-400/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold mb-2">Product Name</h3>
          <p className="text-gray-400 text-sm mb-3">Premium quality product description</p>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-purple-400">$49.99</span>
            <button className="px-4 py-2 bg-purple-600/20 rounded-full text-purple-400 hover:bg-purple-600 hover:text-white transition-all">
              Add to Cart
            </button>
          </div>
        </div>
      ))}
    </div>
  </div>
</section>



























================================================================================
PREMIUM SHOP PAGE (app/shop/page.tsx):
================================================================================

Generate a complete shop page with:

```tsx
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ShoppingBag, Heart, Star } from 'lucide-react';

const products = [
  { id: 1, name: "Premium Hoodie", price: 79.99, rating: 4.8, category: "Apparel" },
  { id: 2, name: "Classic Tee", price: 29.99, rating: 4.5, category: "Apparel" },
  { id: 3, name: "Leather Backpack", price: 129.99, rating: 4.9, category: "Accessories" },
  { id: 4, name: "Wireless Headphones", price: 89.99, rating: 4.7, category: "Electronics" },
  { id: 5, name: "Ceramic Mug", price: 19.99, rating: 4.6, category: "Home" },
  { id: 6, name: "Desk Mat", price: 34.99, rating: 4.4, category: "Office" },
];

export default function ShopPage() {
  const [filter, setFilter] = useState('all');

  const filteredProducts = filter === 'all' ? products : products.filter(p => p.category.toLowerCase() === filter);

  return (
    <div className="min-h-screen pt-20">
      {/* Hero Banner */}
      <div className="relative h-64 md:h-96 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-900/80 to-pink-900/80" />
        <div className="absolute inset-0 bg-[url('/images/image_1.jpg')] bg-cover bg-center mix-blend-overlay" />
        <div className="relative z-10 flex flex-col items-center justify-center h-full text-center px-4">
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-4">Shop Collection</h1>
          <p className="text-lg text-gray-200">Discover premium products crafted for excellence</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="sticky top-16 z-40 bg-black/80 backdrop-blur-xl border-b border-white/10 py-4">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap justify-center gap-3">
            {['all', 'apparel', 'accessories', 'electronics', 'home', 'office'].map((cat) => (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  filter === cat
                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/25'
                    : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'
                }`}
              >
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Products Grid */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredProducts.map((product) => (
            <div key={product.id} className="group relative bg-gradient-to-br from-white/5 to-white/3 rounded-2xl overflow-hidden backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300 hover:-translate-y-1">
              <div className="relative h-64 bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center">
                <ShoppingBag className="w-16 h-16 text-purple-400/50 group-hover:scale-110 transition-transform" />
                <button className="absolute top-3 right-3 p-2 rounded-full bg-black/50 hover:bg-purple-600 transition-colors">
                  <Heart className="w-4 h-4" />
                </button>
              </div>
              <div className="p-5">
                <div className="flex items-center gap-1 mb-2">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className={`w-3 h-3 ${i < Math.floor(product.rating) ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'}`} />
                  ))}
                  <span className="text-xs text-gray-500 ml-1">{product.rating}</span>
                </div>
                <h3 className="text-lg font-bold mb-1">{product.name}</h3>
                <p className="text-sm text-gray-400 mb-3">{product.category}</p>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-purple-400">${product.price}</span>
                  <button className="px-4 py-2 bg-purple-600/20 rounded-full text-purple-400 hover:bg-purple-600 hover:text-white transition-all text-sm">
                    Add to Cart
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}














================================================================================
🚨🚨🚨 CRITICAL: MUST CREATE PAGE FILES FOR EVERY NAVIGATION LINK 🚨🚨🚨
================================================================================

For EVERY link in Navigation.tsx, you MUST create a corresponding page file.

Example:
If Navigation.tsx has: <Link href="/shop">Shop</Link>
You MUST create: app/shop/page.tsx

RULE: 1 navigation link = 1 page file in app/ directory

Required files for a coffee shop website:
- app/page.tsx (home page - ALWAYS required)
- app/shop/page.tsx (products/shop page)
- app/delivery/page.tsx (delivery information)
- app/recipes/page.tsx (recipes/brew guide)
- app/about/page.tsx (about us/our story)
- app/locations/page.tsx (store locations)

FAILURE TO CREATE THESE PAGES WILL CAUSE 404 ERRORS WHEN USERS CLICK NAVIGATION LINKS.












================================================================================
🚨🚨🚨 CRITICAL: JSON OUTPUT FORMAT RULES - MUST FOLLOW 🚨🚨🚨
================================================================================

You are generating RAW JSON that will be parsed by Python's json.loads().
The JSON contains file contents as strings. These strings may contain code.

FORBIDDEN PATTERNS (NEVER output these):

❌ Template literals with backticks: `text` or `${variable}`
❌ JavaScript expressions inside strings: {`"${variable}"`}
❌ Unescaped double quotes inside JSON string values
❌ Trailing commas in objects or arrays
❌ Control characters (\\n, \\t are OK, but raw newlines are NOT)

EXAMPLE - WRONG (causes JSON parse error):
{"file": "page.tsx", "content": "<p>{`\"${testimonial.quote}\"`}</p>"}

EXAMPLE - CORRECT (valid JSON):
{"file": "page.tsx", "content": "<p>{testimonial.quote}</p>"}

SPECIAL RULE FOR STRINGS INSIDE JSON:
- Escape double quotes with \\"
- Escape backslashes with \\\\
- Use \\n for newlines, \\t for tabs
- NEVER use raw newlines inside string values

REMEMBER: You are outputting JSON, not JavaScript. No backticks, no ${} inside strings!

================================================================================

















================================================================================
SPECIAL RULE FOR DYNAMIC CONTENT (testimonials, features, etc.)
================================================================================

When generating JSX with .map() functions, use this pattern:

✅ CORRECT (no template literals):
```jsx
{testimonials.map((testimonial, index) => (
  <div key={index}>
    <p>{testimonial.quote}</p>
    <h4>{testimonial.author}</h4>
  </div>
))}
❌ WRONG (causes JSON parsing errors):
{testimonials.map(testimonial => (
  <div key={testimonial.id}>
    <p>{`"${testimonial.quote}"`}</p>  // ← NEVER use backticks or ${}
  </div>
))}















================================================================================
SPECIFIC RULE FOR app/page.tsx - MUST HAVE 'use client'
================================================================================

STATEMENT: app/page.tsx MUST have 'use client' as the FIRST line because it contains 
images with onError handlers and buttons with onClick handlers.











================================================================================
🚨🚨🚨 THREE MANDATORY RULES FOR ALL GENERATED CODE 🚨🚨🚨
================================================================================

These rules MUST be followed for EVERY file generated. Violations will cause Vercel build failures.

================================================================================
RULE 1: IMAGE ERROR HANDLERS - MUST USE OPTIONAL CHAINING
================================================================================

STATEMENT: When generating any image with an onError handler, you MUST use 
optional chaining (?.) when accessing parentElement.

REQUIREMENT: Replace `parentElement.classList` with `parentElement?.classList`

EXAMPLE - CORRECT:
```tsx
onError={(e) => {
  e.currentTarget.style.display = 'none';
  e.currentTarget.parentElement?.classList.add('bg-gradient-to-br', 'from-purple-950', 'via-zinc-950', 'to-pink-950');
}}







================================================================================
🚨🚨🚨 CRITICAL RULES FOR ALL GENERATED CODE 🚨🚨🚨
================================================================================

RULE 1: IMAGE ERROR HANDLERS - ALWAYS use optional chaining
================================================================================

When generating any image with an onError handler, ALWAYS use this pattern:

✅ CORRECT:
```tsx
onError={(e) => {
  e.currentTarget.style.display = 'none';
  e.currentTarget.parentElement?.classList.add('bg-gradient-to-br', 'from-purple-950', 'via-zinc-950', 'to-pink-950');
}}
❌ WRONG (causes build error):
onError={(e) => {
  e.currentTarget.style.display = 'none';
  e.currentTarget.parentElement.classList.add(...);  // Missing ?.
}}





================================================================================
RULE 2: ALL PAGES WITH EVENT HANDLERS MUST HAVE 'use client'
================================================================================

Any file that contains ANY of the following MUST have 'use client' as the FIRST line:

Event Handlers:
- onError
- onClick
- onSubmit
- onChange
- onMouseEnter
- onMouseLeave
- onFocus
- onBlur
- onKeyDown
- onKeyUp
- onScroll

React Hooks:
- useState
- useEffect
- useCallback
- useMemo
- useRef
- useContext
- useReducer

Next.js Hooks:
- useRouter
- usePathname
- useSearchParams

Browser APIs:
- localStorage
- sessionStorage
- window
- document

✅ CORRECT (this will build successfully):
```tsx
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function MyPage() {
  const [count, setCount] = useState(0);
  const router = useRouter();
  
  return (
    <button onClick={() => setCount(count + 1)}>
      Click me
    </button>
  );
}
❌ WRONG (this will FAIL the Vercel build):
import React, { useState } from 'react';  // Missing 'use client'

export default function MyPage() {
  const [count, setCount] = useState(0);  // ERROR: useState requires 'use client'
  
  return <button onClick={() => setCount(count + 1)}>Click</button>;
}
❌ WRONG (this will also FAIL):
import React from 'react';

export default function MyPage() {
  return (
    <img 
      src="/image.jpg" 
      onError={(e) => {  // ERROR: onError requires 'use client'
        e.currentTarget.style.display = 'none';
      }}
    />
  );
}





















================================================================================
WHICH FILES NEED 'use client'? - COMPLETE LIST
================================================================================

✅ MUST HAVE 'use client' - CLIENT COMPONENTS:

app/page.tsx                    # If it has: onError, onClick, useState, useRouter
app/signup/page.tsx             # Has forms, onSubmit, onChange, useState
app/login/page.tsx              # Has forms, onSubmit, onChange, useState
app/contact/page.tsx            # Has forms, onSubmit, onChange, useState
app/about/page.tsx              # If it has images with onError
app/dashboard/page.tsx          # Usually has client interactions
app/profile/page.tsx            # Has forms, user interactions
app/settings/page.tsx           # Has forms, toggles, switches
app/cart/page.tsx               # Has add/remove buttons
app/checkout/page.tsx           # Has forms, payment interactions
app/search/page.tsx             # Has input, filters
app/blog/[slug]/page.tsx        # If it has comments, likes, shares

components/Navigation.tsx       # Always - has onClick, useState (mobile menu)
components/Footer.tsx           # If it has newsletter form, social links
components/Button.tsx           # Always - has onClick
components/Modal.tsx            # Always - has open/close state
components/Dropdown.tsx         # Always - has toggle state
components/Tabs.tsx             # Always - has active tab state
components/Carousel.tsx         # Always - has next/prev buttons
components/ImageGallery.tsx     # Has onError for images
components/VideoPlayer.tsx      # Has play/pause controls
components/FormInput.tsx        # Has onChange, onBlur
components/FileUploader.tsx     # Has file selection
components/StarRating.tsx       # Has onClick for rating
components/NewsletterSignup.tsx # Has form submission
components/SearchBar.tsx        # Has input, search functionality
components/CartIcon.tsx         # Has onClick for cart
components/UserMenu.tsx         # Has onClick for dropdown
components/MobileMenu.tsx       # Has toggle state
components/DarkModeToggle.tsx   # Has toggle state

hooks/useAuth.ts                # Always - uses useState, useEffect
hooks/useLocalStorage.ts        # Always - uses localStorage
hooks/useMediaQuery.ts          # Always - uses window.matchMedia
hooks/useScrollPosition.ts      # Always - uses window.scroll
hooks/useWindowSize.ts          # Always - uses window resize

context/AuthContext.tsx         # Always - has useState, useEffect
context/ThemeContext.tsx        # Always - has useState
context/CartContext.tsx         # Always - has useState

lib/api-client.ts               # If it uses fetch in browser
lib/storage.ts                  # If it uses localStorage/sessionStorage

================================================================================
❌ DO NOT NEED 'use client' - SERVER COMPONENTS:
================================================================================

app/layout.tsx                  # Can stay Server Component
app/loading.tsx                 # Server Component (loading UI)
app/error.tsx                   # Server Component (error UI)
app/not-found.tsx               # Server Component (404 page)
app/api/*/route.ts              # API routes - run on server only

components/ServerComponent.tsx  # No client interactions
components/MarkdownRenderer.tsx # Pure rendering

lib/db.ts                       # Database utilities - server only
lib/auth-server.ts              # Server-side auth only
lib/email-service.ts            # Email sending - server only

types/index.ts                  # TypeScript types - no runtime code
utils/constants.ts              # Constants - no hooks
utils/helpers.ts                # Pure functions - no hooks

middleware.ts                   # Runs on server
next.config.js                  # Configuration file
tailwind.config.ts              # Configuration file
postcss.config.js               # Configuration file

================================================================================
QUICK CHECKLIST FOR AI:
================================================================================

Ask yourself these questions:

1. Does the file have any event handlers? (onClick, onSubmit, onError, onChange)
   → YES: Add 'use client'

2. Does the file use any React Hooks? (useState, useEffect, useCallback)
   → YES: Add 'use client'

3. Does the file use Next.js client hooks? (useRouter, usePathname, useSearchParams)
   → YES: Add 'use client'

4. Does the file use browser APIs? (localStorage, sessionStorage, window, document)
   → YES: Add 'use client'

5. Is the file a page with forms or user interaction?
   → YES: Add 'use client'

6. Is the file a component that will be interactive?
   → YES: Add 'use client'

If you answered YES to ANY question → ADD 'use client' at the top

================================================================================
EXAMPLES OF CORRECT 'use client' PLACEMENT:
================================================================================

✅ app/signup/page.tsx (needs it - has form):
```tsx
'use client';

import React, { useState } from 'react';
import Link from 'next/link';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  
  return (
    <form onSubmit={...}>
      <input onChange={(e) => setEmail(e.target.value)} />
    </form>
  );
}



















================================================================================
FOOTER GENERATION RULE - DYNAMIC IMPORTS
================================================================================

When generating components/Footer.tsx, the AI MUST:

1. First, write the Footer JSX with all the icons it wants to use
2. Then, look at EVERY icon used in the JSX
3. Finally, add ALL those icons to the import statement

================================================================================
STEP BY STEP PROCESS FOR AI:
================================================================================

STEP 1: Design the Footer JSX with icons
Example:
```tsx
<div>
  <GraduationCap className="w-8 h-8" />
  <Mail className="w-4 h-4" />
  <Phone className="w-4 h-4" />
  <MapPin className="w-4 h-4" />
  <Send className="w-4 h-4" />
  <Facebook className="w-5 h-5" />
  <Twitter className="w-5 h-5" />
  <Instagram className="w-5 h-5" />
  <Heart className="w-3 h-3" />
</div>

















================================================================================
🚨 CRITICAL: HOME PAGE HERO BACKGROUND - ALWAYS USE IMAGE 🚨
================================================================================

When generating `app/page.tsx`, you MUST follow these rules:

1. **HERO BACKGROUND**: ALWAYS use `/images/image_1.jpg` as the full-screen background image

2. **STRUCTURE** - Use this EXACT pattern:
```tsx
<section className="relative h-screen flex items-center justify-center overflow-hidden">
  {/* Background Image */}
  <img 
    src="/images/image_1.jpg" 
    alt="Hero background" 
    className="absolute inset-0 w-full h-full object-cover" 
  />
  {/* Dark Overlay for text readability */}
  <div className="absolute inset-0 bg-black/50" />
  
  {/* Content */}
  <div className="relative z-10 text-center px-4">
    <h1 className="text-6xl md:text-7xl font-bold text-white mb-6">[Brand Name]</h1>
    <p className="text-xl text-gray-200 mb-8 max-w-2xl mx-auto">[Tagline here]</p>
    <Link 
      href="/[first-nav-link]" 
      className="inline-block px-8 py-3 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold hover:from-purple-700 hover:to-pink-700 transition-all"
    >
      [CTA Button Text]
    </Link>
  </div>
</section>










================================================================================
CRITICAL SITE STRUCTURE & NAVIGATION
================================================================================
- SITE SCOPE: You are strictly limited to a 3-page architecture. DO NOT generate additional pages.
- REQUIRED ROUTES:
    1. app/page.tsx (Home/Landing - Bold title, rich content)

- NAVIGATION LOGIC (components/Navigation.tsx):
    1. THE BRAND NAME IS THE HOME LINK: Do not include a separate "Home" text link. The user clicks the Brand Name/Logo to return to "/".
    2. TOTAL LINKS: There should only be [Brand Name (links to /) and other 2.
    3. BRAND ICON: The brand icon MUST be included next to the Brand Name in Navigation.tsx ONLY.
    4. FOOTER ARCHITECTURE (components/Footer.tsx):
       - The Footer must be a separate component included in the root layout.
       - It must contain the Brand Name, a brief description, and a copyright notice with the current year (2026).
       - Should be haivng the social media icons and links
       - Style the footer with a "glass" effect or a clean, dark aesthetic to match the senior designer requirements.
       - ALL Lucide imports MUST be declared at the top
       
       
       
       
       
       
       
       
       
       
       
       

================================================================================
TECHNICAL BUILD RULES — NO EXCEPTIONS
================================================================================
- 'use client' MUST be the absolute first line in any file using hooks (useState, useEffect) or events (onClick).
- EVERY component used (Link, Image, Icons) MUST be imported at the top of the file.
- Use 'lucide-react' for all icons. Example: import { Check, Mail } from 'lucide-react';
- ALL imports must be relative (e.g., ../../components/Footer), NOT using @/ aliases.

================================================================================
OUTPUT FORMAT — RAW JSON ONLY
================================================================================
- Output ONLY raw valid JSON. No markdown, no explanations, no code blocks.
- Keys = file paths (strings), Values = full file content as strings.
- Escape double quotes as \" and newlines as \\n.
- NEVER output raw newlines or unescaped quotes inside JSON string values.








================================================================================
🛠️ THE "ZERO-CRASH" IMPORT PROTOCOL 🛠️
================================================================================
Every file must be "Self-Sufficient." You MUST verify these imports for every string value:

- IF code contains '<Link': MUST import Link from 'next/link';
- IF code contains '<Image': MUST import Image from 'next/image';
- IF code contains Lucide icons (e.g., <Check />, <Mail />): MUST import from 'lucide-react';
- IF code contains hooks (useState, useEffect) or event handlers (onClick, onSubmit): 
    - MUST import { useState/useEffect } from 'react';
    - MUST have 'use client'; as the ABSOLUTE FIRST LINE (Line 1).



================================================================================
🚨 CRITICAL: YOU MUST GENERATE COMPLETE FULL PAGES - NO EXCEPTIONS 🚨
================================================================================

For EVERY navigation link, you MUST create a COMPLETE page file with:


❌ NEVER create empty or placeholder pages:
export default function Courses() { return <div>Courses</div>; }
export default function Shop() { return <div>Shop Page</div>; }
export default function About() { return <div>About Us</div>; }











================================================================================
🚨🚨🚨 CRITICAL: UNIQUE CONTENT FOR EACH PROGRAM/PRODUCT/SERVICE 🚨🚨🚨
================================================================================

When generating arrays of items (programs, courses, products, services, team members):

**YOU MUST generate DIFFERENT content for EACH item - NO duplicate descriptions**

Example - FOR A SCHOOL WEBSITE with 3 programs:

❌ WRONG (same description for all):
```tsx
const programs = [
  { title: "Classical Performance", description: "Master your craft with world-class mentors." },
  { title: "Jazz Studies", description: "Master your craft with world-class mentors." },
  { title: "Music Production", description: "Master your craft with world-class mentors." }
]

✅ CORRECT (unique description for each):
const programs = [
  { 
    title: "Classical Performance", 
    description: "Master classical techniques with world-class mentors. Focus on piano, violin, cello, and orchestral instruments.",
    duration: "4 Years",
    career: "Orchestral Musician, Solo Performer"
  },
  { 
    title: "Jazz Studies", 
    description: "Immerse yourself in improvisation, harmony, and rhythm. Learn from professional jazz musicians.",
    duration: "4 Years",
    career: "Jazz Musician, Composer, Band Leader"
  },
  { 
    title: "Music Production", 
    description: "Learn modern recording techniques, mixing, mastering, and digital audio workstations.",
    duration: "3 Years",
    career: "Music Producer, Sound Engineer"
  }
]


RULES:

   1. Each program MUST have a UNIQUE description (different words, different focus)

   2. Each program MUST have UNIQUE details (duration, career path, requirements)

   3. Each program MUST have UNIQUE icons or visual elements

   4. NEVER repeat the exact same text across multiple items

   5. Vary the length and content of each description

For different project types:

SCHOOL PROGRAMS (vary by):

    Classical vs Modern vs Technology focus

    Different durations (3 years, 4 years, 2 years)

    Different career paths (Performer, Producer, Educator)

    Different prerequisites (Portfolio, Audition, Interview)

COFFEE PRODUCTS (vary by):

    Origin (Ethiopia, Colombia, Brazil)

    Roast level (Light, Medium, Dark)

    Flavor notes (Citrus, Chocolate, Berry)

    Price points ($15, $18, $22)

HOTEL ROOMS (vary by):

    Room type (Standard, Deluxe, Suite)

    View (City, Ocean, Garden)

    Size (300 sq ft, 500 sq ft, 800 sq ft)

    Amenities (Mini-bar, Jacuzzi, Balcony)

GYM CLASSES (vary by):

    Class type (Yoga, HIIT, Pilates)

    Difficulty (Beginner, Intermediate, Advanced)

    Duration (45min, 60min, 90min)

    Instructor specialties

REMEMBER: Each array item = UNIQUE content. No duplicates allowed!
================================================================================
















Generate a COMPLETE Next.js 14 home page (app/page.tsx) for a website based on the user's request.

================================================================================
PROJECT TYPE DETECTION
================================================================================
First, identify the PROJECT TYPE from the user prompt:
- SCHOOL/ACADEMY: Music school, coding bootcamp, university, training center
- COFFEE/ROASTERY: Coffee shop, roastery, cafe
- HOTEL/RESORT: Hotel, lodge, resort, accommodation
- RESTAURANT: Restaurant, bistro, dining, eatery
- GYM/FITNESS: Gym, fitness center, yoga studio
- E-COMMERCE: Online store, shop, marketplace
- PORTFOLIO: Designer, developer, creative agency
- TECH/SAAS: Software company, app, platform

================================================================================
CRITICAL: HOW TO CREATE THE 3 PILLARS/FEATURES SECTION
================================================================================

✅ ALWAYS DO THIS - Define array FIRST, then map:


const pillars = [
  { 
    id: 1, 
    emoji: "🎓", 
    title: "Music Theory & Composition", 
    description: "Master the fundamentals of music theory, harmony, and composition techniques from industry professionals with decades of experience." 
  },
  { 
    id: 2, 
    emoji: "🎛️", 
    title: "Audio Engineering", 
    description: "Learn professional recording, mixing, and mastering using industry-standard equipment in our state-of-the-art studios." 
  },
  { 
    id: 3, 
    emoji: "🎹", 
    title: "Digital Production", 
    description: "Create beats, produce tracks, and master modern production tools like Ableton, Logic Pro, and FL Studio." 
  },









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
- All lucide imports should be at the top.
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
🚨 IMAGE USAGE RULE - ONLY 1 IMAGE TOTAL (HERO ONLY) 🚨(hero is app/page.tsx)
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
   - 3 Collection  → UNIQUE description (different from others)














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
   - Option A: ["Store", "Browse", "Items", "Payment"]
   - Option B: ["Shop", "Catalog", "Cart", "Checkout"]
   - Option C: ["Products", "Collections", "Bag", "Secure Checkout"]
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
- Hero section with gradient title, description,image background and CTA button
- Features section with 2-4 cards (icons, titles, descriptions) with diffrent content
- Stats section with numbers (e.g., "500+ Students", "10 Years Experience")
- Testimonials section with 2-3 customer quotes
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
   </section>




   
   
   
   
   















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



















ALWAYS create COMPLETE pages with:
✅ Minimum 3-4 sections (hero, grid, features, CTA, Footer)
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
- Real data (products, services, team members)
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
- "Admissions" → Use: "Apply", "Join Us", "Enrollment", "Be a Student", "Get Started"
- "Faculty" → Use: "Our Teachers", "Staff", "Mentors", "Instructors", "Academic Team"
-  "Events" → Use: "Calendar", "Activities", "Announcements", "School Life", "News & Events"
-  "Contact" → Use: "Visit Us", "Get in Touch", "Reach Out", "Connect"



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

app/dashboard/            # Route group for protected pages              # Dashboard layout with sidebar
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

components/layout/
  Header.tsx                # Header wrapper
  Container.tsx             # Responsive container
  Section.tsx               # Section with padding and background

lib/
  utils.ts                  # cn utility function for Tailwind merging

hooks/
  useScroll.ts              # Scroll position hook
  useMediaQuery.ts          # Responsive breakpoint hook
  useLocalStorage.ts        # Local storage hook
  useDebounce.ts            # Debounce hook

types/
  index.ts                  # TypeScript interfaces and types

styles/
  globals.css               # Global styles (main file)

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
6. EVERY array .map() Hacing different content for products/Features
7. ALL pages MUST be responsive (mobile-first design)
8. EVERY component MUST have proper TypeScript types
















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
COMPLETE GLOBALS.CSS TEMPLATE
================================================================================

"app/globals.css": "@tailwind base;\\n@tailwind components;\\n@tailwind utilities;\\n\\n@layer base {\\n  :root {\\n    --background: 0 0% 100%;\\n    --foreground: 222.2 84% 4.9%;\\n    --card: 0 0% 100%;\\n    --card-foreground: 222.2 84% 4.9%;\\n    --border: 214.3 31.8% 91.4%;\\n    --ring: 222.2 84% 4.9%;\\n  }\\n\\n  .dark {\\n    --background: 222.2 84% 4.9%;\\n    --foreground: 210 40% 98%;\\n    --card: 222.2 84% 4.9%;\\n    --card-foreground: 210 40% 98%;\\n    --border: 217.2 32.6% 17.5%;\\n    --ring: 212.7 26.8% 83.9%;\\n  }\\n\\n  * {\\n    border-color: hsl(var(--border));\\n  }\\n\\n  body {\\n    @apply bg-zinc-950 text-white antialiased;\\n    font-feature-settings: \\\"rlig\\\" 1, \\\"calt\\\" 1;\\n  }\\n}\\n\\n@layer utilities {\\n  html {\\n    scroll-behavior: smooth;\\n  }\\n\\n  ::-webkit-scrollbar {\\n    width: 10px;\\n    height: 10px;\\n  }\\n\\n  ::-webkit-scrollbar-track {\\n    background: #18181b;\\n    border-radius: 5px;\\n  }\\n\\n  ::-webkit-scrollbar-thumb {\\n    background: linear-gradient(to bottom, #a855f7, #ec4899);\\n    border-radius: 5px;\\n  }\\n\\n  ::-webkit-scrollbar-thumb:hover {\\n    background: linear-gradient(to bottom, #c084fc, #f472b6);\\n  }\\n\\n  ::selection {\\n    @apply bg-purple-500 text-white;\\n  }\\n\\n  *:focus-visible {\\n    @apply outline-none ring-2 ring-purple-500 ring-offset-2 ring-offset-zinc-950;\\n  }\\n}\\n\\n@layer components {\\n  .glass {\\n    @apply bg-white/5 backdrop-blur-md border border-white/10;\\n  }\\n\\n  .glass-hover {\\n    @apply transition-all duration-300 hover:bg-white/10 hover:border-white/20;\\n  }\\n\\n  .gradient-text {\\n    @apply bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent;\\n    background-size: 200% auto;\\n    animation: shimmer 3s ease infinite;\\n  }\\n\\n  .card-hover {\\n    @apply transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl hover:shadow-purple-500/20;\\n  }\\n\\n  .glow {\\n    @apply shadow-lg shadow-purple-500/25;\\n  }\\n\\n  .glow-hover {\\n    @apply transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/40;\\n  }\\n\\n  .hero-gradient {\\n    background: radial-gradient(ellipse at top, #1e1b4b, transparent),\\n                radial-gradient(ellipse at bottom, #4c1d95, transparent);\\n  }\\n\\n  .grid-pattern {\\n    background-image: linear-gradient(to right, #ffffff0a 1px, transparent 1px),\\n                      linear-gradient(to bottom, #ffffff0a 1px, transparent 1px);\\n    background-size: 50px 50px;\\n  }\\n}\\n\\n@keyframes shimmer {\\n  0% { background-position: 0% 50%; }\\n  50% { background-position: 100% 50%; }\\n  100% { background-position: 0% 50%; }\\n}\\n\\n@keyframes float {\\n  0%, 100% { transform: translateY(0px); }\\n  50% { transform: translateY(-20px); }\\n}\\n\\n@keyframes pulse-slow {\\n  0%, 100% { opacity: 0.5; }\\n  50% { opacity: 1; }\\n}\\n\\n@keyframes gradient {\\n  0% { background-position: 0% 50%; }\\n  50% { background-position: 100% 50%; }\\n  100% { background-position: 0% 50%; }\\n}\\n\\n.animate-float {\\n  animation: float 6s ease-in-out infinite;\\n}\\n\\n.animate-pulse-slow {\\n  animation: pulse-slow 3s ease-in-out infinite;\\n}\\n\\n.animate-gradient {\\n  background-size: 200% auto;\\n  animation: gradient 3s ease infinite;\\n}"









================================================================================
NAVIGATION COMPONENT - CRITICAL RULES:
================================================================================


"components/Navigation.tsx": "'use client';\\n\\nimport { useState, useEffect } from 'react';\\nimport Link from 'next/link';\\nimport { ADAPTIVE_ICON, ShoppingBag, Menu, X, Search, User } from 'lucide-react';\\n\\nexport default function Navigation() {\\n  const [isScrolled, setIsScrolled] = useState(false);\\n  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);\\n\\n  useEffect(() => {\\n    const handleScroll = () => {\\n      setIsScrolled(window.scrollY > 50);\\n    };\\n    window.addEventListener('scroll', handleScroll);\\n    return () => window.removeEventListener('scroll', handleScroll);\\n  }, []);\\n\\n  return (\\n    <>\\n      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${\\n        isScrolled \\n          ? 'bg-black/95 backdrop-blur-xl border-b border-white/10 shadow-2xl' \\n          : 'bg-transparent'\\n      }`}>\\n        <div className=\\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8\\">\\n          <div className=\\"flex items-center justify-between h-16 md:h-20\\">\\n            {/* Logo */}\\n            <Link href=\\"/\\" className=\\"flex items-center gap-2 group\\">\\n              <div className=\\"w-8 h-8 md:w-10 md:h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/25 group-hover:scale-110 transition-transform\\">\\n                <ADAPTIVE_ICON className=\\"w-4 h-4 md:w-5 md:h-5 text-white\\" />\\n              </div>\\n              <div className=\\"flex flex-col\\">\\n                <span className=\\"text-lg md:text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent\\">\\n                  {{PROJECT_NAME}}\\n                </span>\\n                <span className=\\"text-[9px] md:text-[10px] tracking-[0.2em] text-purple-400/60 uppercase\\">\\n                  PREMIUM\\n                </span>\\n              </div>\\n            </Link>\\n\\n            {/* Desktop Navigation */}\\n            <div className=\\"hidden md:flex items-center gap-1\\">\\n              <Link href=\\"/shop\\" className=\\"px-4 py-2 text-sm font-medium text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-all\\">\\n                Shop\\n              </Link>\\n              <Link href=\\"/catalog\\" className=\\"px-4 py-2 text-sm font-medium text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-all\\">\\n                Catalog\\n              </Link>\\n              <Link href=\\"/cart\\" className=\\"px-4 py-2 text-sm font-medium text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-all flex items-center gap-1\\">\\n                <ShoppingBag className=\\"w-4 h-4\\" />\\n                Cart\\n                <span className=\\"ml-1 bg-purple-500 text-white text-xs px-1.5 py-0.5 rounded-full\\">0</span>\\n              </Link>\\n            </div>\\n\\n            {/* Desktop Right Icons */}\\n            <div className=\\"hidden md:flex items-center gap-2\\">\\n              <button className=\\"p-2 rounded-lg hover:bg-white/10 transition-colors\\">\\n                <Search className=\\"w-5 h-5 text-gray-300\\" />\\n              </button>\\n              <button className=\\"p-2 rounded-lg hover:bg-white/10 transition-colors\\">\\n                <User className=\\"w-5 h-5 text-gray-300\\" />\\n              </button>\\n            </div>\\n\\n            {/* Mobile Menu Button */}\\n            <button\\n              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}\\n              className=\\"md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors\\"\\n            >\\n              {isMobileMenuOpen ? <X className=\\"w-6 h-6\\" /> : <Menu className=\\"w-6 h-6\\" />}\\n            </button>\\n          </div>\\n        </div>\\n\\n        {/* Mobile Menu */}\\n        <div className={`md:hidden fixed inset-x-0 top-16 bg-black/95 backdrop-blur-xl border-b border-white/10 transition-all duration-300 ${\\n          isMobileMenuOpen ? 'opacity-100 visible' : 'opacity-0 invisible'\\n        }`}>\\n          <div className=\\"px-4 py-4 space-y-2\\">\\n            <Link href=\\"/shop\\" className=\\"block px-4 py-3 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-all\\\" onClick={() => setIsMobileMenuOpen(false)}>\\n              Shop\\n            </Link>\\n            <Link href=\\"/catalog\\" className=\\"block px-4 py-3 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-all\\" onClick={() => setIsMobileMenuOpen(false)}>\\n              Catalog\\n            </Link>\\n            <Link href=\\"/cart\\" className=\\"block px-4 py-3 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-all flex items-center gap-2\\" onClick={() => setIsMobileMenuOpen(false)}>\\n              <ShoppingBag className=\\"w-4 h-4\\" /> Cart\\n            </Link>\\n          </div>\\n        </div>\\n      </nav>\\n      <div className=\\"h-16 md:h-20\\" /> {/* Spacer for fixed header */}\\n    </>\\n  );\\n}"











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
        
        # ✅ OPTIONAL: Add force_new support
        force_new = data.get("force_new", False)
        
        max_retries = 3
        retry_count = 0

        if not user_prompt:
            await websocket.send_json({"type": "error", "message": "Prompt is required"})
            while True:
                await asyncio.sleep(60)
                try:
                    await websocket.send_json({"type": "heartbeat"})
                except:
                    return
            return

        # Generate unique project name
        project_name = name_tracker.generate_unique_name("school", user_prompt)
        project_id = str(uuid.uuid4())  # Generate once at the beginning
  
        # ✅ FIXED: Change "project_name" to "project_id"
        await websocket.send_json({
            "type": "project_id",      # ← CHANGE THIS LINE
            "project_id": project_id,
            "project_name": project_name  # ← Keep this as project_name
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
                    "max_output_tokens": 200000,
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
            for i, term in enumerate(search_terms[:1]):  # Only 2 images
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
                            "max_output_tokens": 8000000,  # ⭐ Increase this
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
                    await websocket.send_json({
                        "type": "status",
                        "message": "⏳ Waiting for images to finish processing..."
                    })
                    
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
                    print(f"⚠️ Initial parse failed: {e1}")
                    
                    # DEBUG: Show problem area
                    if hasattr(e1, 'pos'):
                        pos = e1.pos
                        start = max(0, pos - 200)
                        end = min(len(clean_text), pos + 200)
                        print(f"\n📍 Problem area around position {pos}:")
                        print(clean_text[start:end])
                        print(f"{' ' * (min(200, pos - start))}^--- Error here\n")
                    
                    try:
                        fixed_text = fix_json_errors(clean_text)
                        project_files = json.loads(fixed_text)
                        print(f"✅ JSON fixed and parsed successfully on attempt {retry_count + 1}")
                        break
                        
                    except json.JSONDecodeError as e2:
                        print(f"⚠️ Fixed parse still failed: {e2}")
                        
                        try:
                            print("🛠️ Attempting advanced string repair...")
                            first_brace = clean_text.find('{')
                            last_brace = clean_text.rfind('}')
                            
                            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                                extracted_json = clean_text[first_brace:last_brace + 1]
                                project_files = json.loads(extracted_json)
                                print(f"✅ JSON extracted and parsed successfully!")
                                break
                            else:
                                raise ValueError("No valid JSON object found")
                                
                        except Exception as repair_error:
                            print(f"❌ Repair failed: {repair_error}")
                            
                            # Save to debug file
                            try:
                                with open(f"debug_failed_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w", encoding="utf-8") as f:
                                    f.write(full_response[:20000])
                                print(f"💾 Saved failed response to debug file")
                            except:
                                pass
                            
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
                import traceback
                traceback.print_exc()
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


        print("⏳ Waiting 4s for frontend to process preview...")
        await asyncio.sleep(4)  # Give frontend time to process
 


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



















# ====================== INTELLIGENT AI-DRIVEN EDIT WITH DB INTEGRATION ======================
@app.post("/api/edit-file")
async def edit_file(request: Dict[str, Any]):
    try:
        edit_description: str = request.get("edit_description", "")
        all_files: Dict[str, Any] = request.get("all_files", {})
        existing_preview: str = request.get("existing_preview", "")
        force_regenerate: bool = request.get("force_regenerate", True)
        user_db_connection_string: str = request.get("db_connection_string", "")
        
        # Extract project identifiers for saving preview
        project_id: Optional[str] = request.get("project_id")
        project_name_from_request: str = request.get("project_name", "")













        # ========== ADD THIS BLOCK - LOAD CLOUDINARY URL FROM DATABASE ==========
        original_cloudinary_image_url = None
        
        
        
        if project_id:
            try:
                async with AsyncSessionLocal() as session:
                    stmt = select(Project).where(Project.id == project_id)
                    result = await session.execute(stmt)
                    existing_project = result.scalar_one_or_none()
                    
                    if existing_project and existing_project.cloudinary_image_url:
                        original_cloudinary_image_url = existing_project.cloudinary_image_url
                        print(f"📸 Loaded Cloudinary URL from database: {original_cloudinary_image_url[:80]}...")
                        
                        # Store in all_files for preservation
                        all_files["__original_cloudinary_url__"] = original_cloudinary_image_url
                        
                        if not project_name_from_request:
                            project_name_from_request = existing_project.name
            except Exception as e:
                print(f"⚠️ Could not load existing project: {e}")
        # ========== END OF ADDED BLOCK ==========





        print(f"\n{'='*70}")
        
        
        print(f"🔧 EDIT REQUEST RECEIVED")
        print(f"📝 Description: {edit_description}")
        print(f"📁 Available files: {len(all_files)} files")
        if project_id:
            print(f"🆔 Project ID: {project_id}")
            
            
            
      
        if user_db_connection_string:
            print(f"🗄️ User's Database provided: {user_db_connection_string[:50]}...")
      
        print(f"{'='*70}\n")
        
        
        
        
        
        
        
        
        
        
        

        if not edit_description:
            raise HTTPException(status_code=400, detail="Edit description is required")

        # Initialize updated_files with all_files
        updated_files = {**all_files}


        # ✅ ADD THIS LINE HERE - edit_results initialization at the TOP
        edit_results = []  # <--- ADD THIS RIGHT HERE

        # Helper function to create simple preview after deletion
        def create_simple_preview(files: Dict[str, Any], project_name: str) -> str:
            """Create a simple HTML preview when AI generation fails"""
            nav_links_html = ""
            if "components/Navigation.tsx" in files:
                nav_content = files["components/Navigation.tsx"]
                link_matches = re.findall(r'href="/([^"]+)"[^>]*>([^<]+)</', nav_content)
                for href, text in link_matches:
                    if href not in ['login', 'signup', 'auth']:
                        nav_links_html += f'<a href="#" onclick="showPage(\'{href}\'); return false;" class="nav-link">{text}</a>'
          
            html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);
            color: #e2e8f0;
        }}
        nav {{
            background: rgba(26, 26, 30, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
            padding: 1rem 2rem;
        }}
        .nav-container {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .brand {{
            font-size: 1.5rem;
            font-weight: bold;
            background: linear-gradient(135deg, #c084fc, #f472b6);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-decoration: none;
            cursor: pointer;
        }}
        .nav-link {{
            color: #9ca3af;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            transition: all 0.2s;
        }}
        .nav-link:hover {{ color: #c084fc; background: rgba(192,132,252,0.1); }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .page {{
            display: none;
            padding-top: 80px;
            min-height: 100vh;
        }}
        .page.active {{ display: block; }}
        h1 {{ font-size: 3rem; margin-bottom: 1rem; }}
        .gradient-text {{
            background: linear-gradient(135deg, #c084fc, #f472b6);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }}
        .hero-section {{
            text-align: center;
            padding: 100px 0;
        }}
    </style>
    <script>
        function showPage(pageId) {{
            document.querySelectorAll('.page').forEach(page => {{
                page.classList.remove('active');
            }});
            const target = document.getElementById('page_' + pageId);
            if (target) target.classList.add('active');
            window.scrollTo(0, 0);
        }}
    </script>
</head>
<body>
    <nav>
        <div class="nav-container">
            <a href="#" onclick="showPage('home'); return false;" class="brand">{project_name}</a>
            <div class="nav-links">
                {nav_links_html}
            </div>
        </div>
    </nav>
  
    <div id="page_home" class="page active">
        <div class="container hero-section">
            <h1 class="gradient-text">Welcome to {project_name}</h1>
            <p style="font-size: 1.2rem; color: #9ca3af; margin-top: 1rem;">Your website is ready</p>
        </div>
    </div>
</body>
</html>'''
            return html





















        # ========== STEP 1: CHECK FOR DELETION REQUESTS (HIGHEST PRIORITY) ==========
        deletion_keywords = ['remove', 'delete', 'drop', 'erase', 'get rid of', 'remove the', 'delete the']
        is_deletion_request = any(keyword in edit_description.lower() for keyword in deletion_keywords)
        
        # Also check for package.json specific deletions
        is_package_json_deletion = 'package.json' in edit_description.lower() and any(keyword in edit_description.lower() for keyword in ['remove', 'delete'])
        
        if is_deletion_request or is_package_json_deletion:
            print(f"🤖 AI analyzing deletion request: {edit_description}")
            
            # SPECIAL HANDLE FOR PACKAGE.JSON DELETIONS
            if is_package_json_deletion or '@neondatabase' in edit_description.lower() or 'package.json' in edit_description.lower():
                print(f"📦 Detected package.json modification request")
                
                # Look for package.json file
                package_json_path = "package.json"
                if package_json_path in updated_files:
                    current_package_json = updated_files[package_json_path]
                    
                    # Use the manage_package_json function to remove the dependency
                    updated_content, changes = await manage_package_json(current_package_json, edit_description)
                    
                    if updated_content and changes:
                        # Update the file in memory
                        updated_files[package_json_path] = updated_content
                        
                        # CRITICAL: Add to edit_results so frontend knows file changed
                        edit_results.append({
                            "file_path": package_json_path,
                            "original_content": current_package_json,
                            "updated_content": updated_content,
                            "success": True,
                            "is_new_file": False,
                            "changes": changes
                        })
                        
                        print(f"✅ package.json updated: {changes}")
                        
                        # Regenerate preview
                        new_preview_html = existing_preview
                        try:
                            preview_result = await generate_preview_internal(updated_files, project_name_from_request or "Scorpio Project")
                            if preview_result.get("success"):
                                new_preview_html = preview_result.get("preview_html")
                                updated_files["preview_html"] = new_preview_html
                                await save_regenerated_preview(
                                    preview_html=new_preview_html,
                                    project_name=project_name_from_request or "Scorpio Project",
                                    project_id=project_id
                                )
                        except Exception as preview_error:
                            print(f"⚠️ Preview error: {preview_error}")
                        
                        # Return with the updated file so frontend can apply the change
                        return {
                            "success": True,
                            "deleted_files": [],
                            "removed_links": [],
                            "edits": edit_results,
                            "files_edited": [package_json_path],
                            "updated_files": {
                                package_json_path: updated_content
                            },
                            "preview_html": new_preview_html,
                            "message": f"✅ Updated package.json: {', '.join(changes)}"
                        }
                    else:
                        print(f"⚠️ No changes made to package.json")
                        return {
                            "success": True,
                            "message": "No matching dependencies found to remove",
                            "preview_html": existing_preview
                        }
                else:
                    print(f"⚠️ package.json not found")
                    return {
                        "success": False,
                        "message": "package.json not found in project",
                        "preview_html": existing_preview
                    }
            
            # ========== REGULAR PAGE/FILE DELETION HANDLING ==========
            # Create summary of existing pages for AI
            existing_pages = []
            for file_path in updated_files.keys():
                if "page.tsx" in file_path or "page.jsx" in file_path:
                    parts = file_path.split('/')
                    for i, part in enumerate(parts):
                        if part == 'app' and i+1 < len(parts):
                            page_name = parts[i+1]
                            if page_name not in ['layout.tsx', 'page.tsx', 'loading.tsx', 'error.tsx']:
                                existing_pages.append(page_name)
                        elif 'page.tsx' in part:
                            page_name = parts[-2] if len(parts) > 1 else 'home'
                            if page_name not in ['layout', 'page', 'loading', 'error']:
                                existing_pages.append(page_name)
            
            existing_pages = list(set(existing_pages))
            print(f"📄 Existing pages: {existing_pages}")
            
            # Also check navigation links
            navigation_links = []
            if "components/Navigation.tsx" in updated_files:
                nav_content = updated_files["components/Navigation.tsx"]
                href_matches = re.findall(r'href="/([^"]+)"', nav_content)
                href_matches += re.findall(r"href='/([^']+)'", nav_content)
                navigation_links = list(set(href_matches))
                print(f"🔗 Navigation links: {navigation_links}")
            
            # Let AI decide what to delete
            deletion_prompt = f"""You are an AI code editor. Analyze this deletion request and decide what files/links to remove.
DELETION REQUEST: {edit_description}
EXISTING PAGES: {existing_pages}
NAVIGATION LINKS: {navigation_links}
Based on the request, determine:
1. Which pages/files should be deleted
2. Which navigation links should be removed
3. Any related components or API routes that should be cleaned up
Return ONLY a JSON object with:
{{
  "pages_to_delete": ["page1", "page2"],
  "links_to_remove": ["link1", "link2"],
  "remove_auth_folder": true/false,
  "explanation": "brief explanation"
}}"""
            
            try:
                analysis_text = await model_router.generate_content(
                    prompt=deletion_prompt,
                    config={"temperature": 0.1, "response_mime_type": "application/json"}
                )
                analysis_text = analysis_text.strip()
                analysis_text = clean_json_response(analysis_text)
                deletion_analysis = json.loads(analysis_text)
                print(f"📊 AI Deletion Analysis: {json.dumps(deletion_analysis, indent=2)}")
            except Exception as e:
                print(f"⚠️ AI analysis failed, using fallback: {e}")
                fallback_match = re.search(r'remove\s+(?:the\s+)?(\w+)', edit_description.lower())
                page_to_remove = fallback_match.group(1) if fallback_match else None
                deletion_analysis = {
                    "pages_to_delete": [page_to_remove] if page_to_remove else [],
                    "links_to_remove": [page_to_remove] if page_to_remove else [],
                    "remove_auth_folder": 'auth' in edit_description.lower() or 'login' in edit_description.lower() or 'signup' in edit_description.lower(),
                    "explanation": "Fallback analysis"
                }
            
            pages_to_delete = deletion_analysis.get("pages_to_delete", [])
            links_to_remove = deletion_analysis.get("links_to_remove", [])
            remove_auth_folder = deletion_analysis.get("remove_auth_folder", False)
            
            all_deleted_files = []
            
            # Delete pages identified by AI
            for page_name in pages_to_delete:
                print(f"🗑️ AI decided to delete page: '{page_name}'")
                page_patterns = [
                    rf"app/{page_name}/page\.tsx",
                    rf"app/{page_name}/page\.jsx",
                    rf"app/{page_name}/index\.tsx",
                    rf"app/[^/]+/{page_name}/page\.tsx",
                    rf"pages/{page_name}\.tsx",
                    rf"src/pages/{page_name}\.tsx",
                    rf"app/{page_name}/",
                ]
                for file_path in list(updated_files.keys()):
                    file_lower = file_path.lower()
                    for pattern in page_patterns:
                        if re.search(pattern, file_lower, re.IGNORECASE):
                            del updated_files[file_path]
                            all_deleted_files.append(file_path)
                            print(f"   🗑️ Deleted: {file_path}")
                            break
            
            # Delete auth folder if AI suggests
            if remove_auth_folder:
                print(f"🗑️ AI decided to delete auth folder")
                auth_patterns = [
                    r"app/auth/.*\.tsx", r"app/auth/.*\.jsx", r"app/auth/",
                    r"app/api/auth/.*\.ts", r"app/api/auth/.*\.js",
                    r"components/AuthProvider\.tsx", r"lib/auth\.ts",
                    r"middleware\.ts", r"app/auth/page\.tsx",
                ]
                for file_path in list(updated_files.keys()):
                    file_lower = file_path.lower()
                    for pattern in auth_patterns:
                        if re.search(pattern, file_lower, re.IGNORECASE):
                            del updated_files[file_path]
                            all_deleted_files.append(file_path)
                            print(f"   🗑️ Deleted auth file: {file_path}")
                            break

            # Remove navigation links identified by AI
            new_preview_html = existing_preview
            if "components/Navigation.tsx" in updated_files and links_to_remove:
                nav_content = updated_files["components/Navigation.tsx"]
                print(f"🗑️ AI decided to remove navigation links: {links_to_remove}")
                print(f"📝 Original navigation:\n{nav_content[:500]}")
                
                for link in links_to_remove:
                    link_prompt = f"""Remove the navigation link for '{link}' from this Next.js Navigation component.
Specifically find and remove the Link component that has href="/{link}" (including the opening tag, closing tag, and all content between them).
IMPORTANT - PRESERVE EXACT INDENTATION:
- Keep ALL existing spaces and indentation levels
- Do NOT change the formatting of any other code
- Maintain the exact same indentation pattern as the original
CURRENT NAVIGATION CODE:
{nav_content}
Return ONLY the complete updated component code with the '{link}' link removed.
CRITICAL: Keep ALL indentation exactly as in the original.
The code should be valid TypeScript/JSX with preserved indentation.
UPDATED CODE:"""
                    
                    try:
                        link_response = await model_router.generate_content(
                            prompt=link_prompt,
                            config={"temperature": 0.1, "max_output_tokens": 200000}
                        )
                        new_content = link_response.strip()
                        
                        if new_content.startswith("```"):
                            lines = new_content.split('\n')
                            if lines[0].startswith('```'): 
                                lines = lines[1:]
                            if lines and lines[-1].strip() == '```':
                                lines = lines[:-1]
                            new_content = '\n'.join(lines)
                        
                        if f'href="/{link}"' not in new_content and f"href='/{link}'" not in new_content:
                            nav_content = new_content
                            print(f"   ✅ AI successfully removed '{link}' link")
                        else:
                            print(f"   ⚠️ AI response still has '{link}', using regex")
                            regex_patterns = [
                                rf'<Link\s+[^>]*href="/{link}"[^>]*>.*?</Link>',
                                rf'<Link\s+href="/{link}"[^>]*>.*?</Link>',
                                rf'<Link[^>]*href="/{link}"[^>]*>.*?</Link>',
                            ]
                            for pattern in regex_patterns:
                                nav_content = re.sub(pattern, '', nav_content, flags=re.DOTALL | re.IGNORECASE)
                            print(f"   🔧 Regex removed '{link}'")
                            
                    except Exception as e:
                        print(f"   ⚠️ AI failed: {e}, using regex")
                        regex_patterns = [
                            rf'<Link\s+[^>]*href="/{link}"[^>]*>.*?</Link>',
                            rf'<Link\s+href="/{link}"[^>]*>.*?</Link>',
                            rf'<Link[^>]*href="/{link}"[^>]*>.*?</Link>',
                        ]
                        for pattern in regex_patterns:
                            nav_content = re.sub(pattern, '', nav_content, flags=re.DOTALL | re.IGNORECASE)
                        print(f"   🔧 Regex removed '{link}'")
                
                # Final cleanup
                nav_content = re.sub(r'<div\s+className="flex\s+space-x-6">\s*</div>', '', nav_content)
                nav_content = re.sub(r'<div\s+className="flex\s+space-x-6">\s*$', '', nav_content)
                nav_content = re.sub(r'\n\s*\n', '\n', nav_content)
                nav_content = re.sub(r',\s*,', ',', nav_content)
                nav_content = re.sub(r'\s+', ' ', nav_content)
                nav_content = re.sub(r'>\s+<', '><', nav_content)
                
                updated_files["components/Navigation.tsx"] = nav_content
                print(f"📝 Final navigation:\n{nav_content[:500]}")

            # ✅ ALWAYS REGENERATE PREVIEW - EVEN IF NO LINKS WERE REMOVED
            print(f"\n🔄 Regenerating preview after deletion...")
            try:
                project_name = project_name_from_request or "Scorpio Project"
                nav_file = updated_files.get("components/Navigation.tsx", "")
                if nav_file:
                    brand_match = re.search(r'<Link[^>]*href="/"[^>]*>([^<]+)</Link>', nav_file)
                    if brand_match:
                        project_name = brand_match.group(1).strip()
                
                preview_result = await generate_preview_internal(updated_files, project_name)
                if preview_result.get("success"):
                    new_preview_html = preview_result.get("preview_html")
                    updated_files["preview_html"] = new_preview_html
                    print(f"✅ Preview regenerated! Length: {len(new_preview_html):,} chars")
                    
                    # SAVE REGENERATED PREVIEW TO DISK
                    await save_regenerated_preview(
                        preview_html=new_preview_html,
                        project_name=project_name,
                        project_id=project_id
                    )
                else:
                    new_preview_html = existing_preview
            except Exception as preview_error:
                print(f"⚠️ Preview error: {preview_error}")
                new_preview_html = existing_preview
            
            return {
                "success": True,
                "deleted_files": all_deleted_files,
                "removed_links": links_to_remove,
                "updated_files": {
                    "components/Navigation.tsx": updated_files.get("components/Navigation.tsx", "")
                },
                "preview_html": new_preview_html,
                "message": f"✅ Processed: {edit_description}",
                "files_edited": all_deleted_files
            }
        
















        # ========== INSERT THIS RIGHT HERE (BEFORE STEP 2) ==========
        # Check if this is a package.json edit (skip database modal)
        is_package_json_edit = False
        
        # Check edit description for dependency-related keywords
        if ('dependencies' in edit_description.lower() or 
            'package.json' in edit_description.lower() or 
            '@neondatabase' in edit_description.lower() or
            'jsonwebtoken' in edit_description.lower()):
            is_package_json_edit = True
            print(f"📦 Detected package.json/dependency edit - will skip database modal")
        # ================================================================



















        # ========== STEP 2: CHECK FOR DATABASE REQUESTS ==========
        is_db_request = any(keyword in edit_description.lower() for keyword in [
            'database', 'db', 'postgres', 'neon', 'login', 'signup', 'register',
            'authentication', 'auth', 'user table', 'create table', 'schema',
            'integrating', 'connect to database', 'neon database', 'Implement signup', 'Implement sign up', 'Implement signup'
        ])
      
      
      
        # ✅ ADD THIS RIGHT HERE - Override for package.json edits
        if is_package_json_edit:
            is_db_request = False
            print(f"📦 Package.json edit detected - overriding is_db_request to False")
      
      
      
      
        # ✅ NOW check the condition (after override)
        if is_db_request and not user_db_connection_string:
            print(f"🗄️ Database request detected, asking for connection string...")
            return {
                "success": False,
                "requires_db_connection": True,
                "message": "🔐 This request requires a database. Please provide YOUR Neon PostgreSQL connection string.",
                "instruction": "1. Go to https://console.neon.tech\n2. Create a new project\n3. Copy your connection string",
                "example": "postgresql://username:password@ep-example.neon.tech/dbname?sslmode=require",
                "note": "This database will be used for YOUR project's authentication."
            }
            
            
            
            
            
            
      
      
      
      
        db_schema_created = False
        if is_db_request and user_db_connection_string:
            print(f"🗄️ Setting up schema on USER's Neon database...")
            async def execute_user_db_schema(conn_string: str, schema_sql: str):
                import asyncpg
                try:
                    conn = await asyncpg.connect(conn_string)
                    try:
                        await conn.execute(schema_sql)
                        return True, None
                    finally:
                        await conn.close()
                except Exception as e:
                    return False, str(e)
          
            schema_sql = """
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                token VARCHAR(500) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS user_credits (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
                credits INTEGER DEFAULT 10,
                last_reset DATE DEFAULT CURRENT_DATE
            );
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
            """
          
            try:
                success, error = await execute_user_db_schema(user_db_connection_string, schema_sql)
                if success:
                    print(f"✅ User's database schema created successfully!")
                    db_schema_created = True
                    updated_files["__user_db_connection__"] = user_db_connection_string
                    updated_files["__db_integrated__"] = "true"
                else:
                    return {
                        "success": False,
                        "error": f"Database connection failed: {error}",
                        "requires_db_connection": True
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Database error: {str(e)}",
                    "requires_db_connection": True
                }






























        # ========== STEP 3: CONTINUE WITH NORMAL EDITING ==========
        source_files = {k: v for k, v in all_files.items() if k != "preview_html"}
      
        print(f"📂 Processing normal edit request...")
        
        # ========== NEW: Check if this is a signup/login request ==========
        is_signup_request = any(phrase in edit_description.lower() for phrase in [
            'signup', 'login', 'implement signup', 'implement login', 
            'create signup', 'create login', 'add signup', 'add login',
            'authentication', 'auth', 'sign up', 'log in'
        ])
        
        if is_signup_request:
            print(f"🔐 Signup/Login request detected - layout.tsx will NOT be edited")
      
        # Create summary for AI
        file_summary = []
        for file_path, content in list(source_files.items())[:15]:
            if isinstance(content, str):
                lines = content.split('\n')[:15]
                snippet = '\n'.join(lines)
            else:
                snippet = str(content)[:500]
            file_summary.append(f"File: {file_path}\nFirst lines:\n{snippet}\n")
      
        file_summary_text = "\n---\n".join(file_summary)
        
        # ========== UPDATED PROMPT with instruction for signup ==========
        if is_signup_request:
            analysis_prompt = f"""You are an AI code editor. Analyze this edit request.

⚠️ CRITICAL: This is a SIGNUP/LOGIN implementation request.
- DO NOT edit app/layout.tsx - it should remain unchanged
- ONLY edit files directly related to signup/login functionality

EDIT REQUEST: {edit_description}
AVAILABLE SOURCE FILES:
{file_summary_text}

Return ONLY a JSON object with:
{{
  "files_to_edit": ["app/signup/page.tsx", "app/api/auth/signup/route.ts"],
  "explanation": "brief explanation",
  "what_to_change": "specific elements to modify"
}}"""
        else:
            analysis_prompt = f"""You are an AI code editor. Analyze this edit request.
EDIT REQUEST: {edit_description}
AVAILABLE SOURCE FILES:
{file_summary_text}
Return ONLY a JSON object with:
{{
  "files_to_edit": ["file1.tsx", "file2.tsx"],
  "explanation": "brief explanation",
  "what_to_change": "specific elements to modify"
}}"""
        
        print("🤖 Asking AI to analyze...")
      
        try:
            analysis_text = await model_router.generate_content(
                prompt=analysis_prompt,
                config={"temperature": 0.1, "response_mime_type": "application/json"}
            )
            analysis_text = analysis_text.strip()
            analysis_text = clean_json_response(analysis_text)
            # Use json_module instead of json
            analysis = json_module.loads(analysis_text)
            print(f"✅ AI analysis: {analysis.get('files_to_edit', [])}")
            
            # ========== FILTER OUT layout.tsx for signup requests ==========
            if is_signup_request:
                original_files = analysis.get("files_to_edit", [])
                filtered_files = [f for f in original_files if 'layout.tsx' not in f and 'layout' not in f]
                if len(filtered_files) != len(original_files):
                    print(f"   🚫 Removed layout.tsx from edit list (signup request)")
                    analysis["files_to_edit"] = filtered_files
                    
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            # Fallback: intelligently determine which file to edit
            analysis = {
                "files_to_edit": [],
                "explanation": "Edit request",
                "what_to_change": edit_description
            }
            
            # Intelligent fallback based on edit description
            edit_lower = edit_description.lower()
            
            # ========== UPDATED FALLBACK - NEVER include layout.tsx for signup ==========
            if 'signup' in edit_lower or 'sign up' in edit_lower:
                analysis["files_to_edit"] = ["app/signup/page.tsx"]
                print(f"📂 Signup detected - only editing app/signup/page.tsx (layout.tsx protected)")
            elif 'login' in edit_lower or 'log in' in edit_lower:
                analysis["files_to_edit"] = ["app/login/page.tsx"]
                print(f"📂 Login detected - only editing app/login/page.tsx (layout.tsx protected)")
            elif 'auth' in edit_lower or 'authentication' in edit_lower:
                analysis["files_to_edit"] = ["app/signup/page.tsx", "app/login/page.tsx"]
                print(f"📂 Auth detected - only editing auth pages (layout.tsx protected)")
            elif 'page' in edit_lower or 'home' in edit_lower or 'hero' in edit_lower:
                analysis["files_to_edit"] = ["app/page.tsx"]
            elif 'layout' in edit_lower or 'navigation' in edit_lower or 'nav' in edit_lower:
                analysis["files_to_edit"] = ["app/layout.tsx", "components/Navigation.tsx"]
            elif 'footer' in edit_lower:
                analysis["files_to_edit"] = ["components/Footer.tsx"]
            elif 'contact' in edit_lower:
                analysis["files_to_edit"] = ["app/contact/page.tsx"]
            elif 'about' in edit_lower:
                analysis["files_to_edit"] = ["app/about/page.tsx"]
            else:
                # Default to page.tsx, NOT layout.tsx
                if "app/page.tsx" in source_files:
                    analysis["files_to_edit"] = ["app/page.tsx"]
                elif source_files:
                    analysis["files_to_edit"] = [list(source_files.keys())[0]]
            
            print(f"📂 Fallback files to edit: {analysis['files_to_edit']}")
      
        files_to_edit = analysis.get("files_to_edit", [])
        
        # ========== FINAL SAFETY CHECK - Remove layout.tsx if signup request ==========
        if is_signup_request:
            if 'app/layout.tsx' in files_to_edit:
                files_to_edit.remove('app/layout.tsx')
                print(f"   🛡️ FINAL SAFETY: Removed layout.tsx from edit list")







        # ========== EXCLUDE API ROUTES FROM MAIN EDIT LOOP ==========
        # API routes will be created separately in the auth creation block
        api_routes_removed = [f for f in files_to_edit if "api/" in f or "route.ts" in f]
        if api_routes_removed:
            files_to_edit = [f for f in files_to_edit if "api/" not in f and "route.ts" not in f]
            print(f"   🛡️ REMOVED API routes from main edit loop: {api_routes_removed}")
            print(f"   📂 API routes will be created by auth creation block")





        
        def extract_code_from_response(response: str) -> str:
            if "```" in response:
                lines = response.split('\n')
                in_code_block = False
                code_lines = []
                for line in lines:
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        code_lines.append(line)
                if code_lines:
                    return '\n'.join(code_lines)
            return response.strip()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        def generate_login_page() -> str:
            return '''"use client"

import React, { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"

export default function LoginPage() {
   const router = useRouter()
   const [email, setEmail] = useState("")
   const [password, setPassword] = useState("")
   const [error, setError] = useState("")
   const [loading, setLoading] = useState(false)

   const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault()
      setError("")
      setLoading(true)

      try {
         const response = await fetch(`/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
         })

         const data = await response.json()

         if (data.success) {
            localStorage.setItem("token", data.access_token)
            localStorage.setItem("user", JSON.stringify(data.user))
            router.push("/dashboard")
         } else {
            setError(data.detail || data.error || "Login failed")
         }
      } catch (err) {
         setError("Network error. Please try again.")
      } finally {
         setLoading(false)
      }
   }

   return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-950 via-zinc-950 to-pink-950 py-12 px-4">
         <div className="max-w-md w-full space-y-8 bg-white/5 backdrop-blur-sm p-8 rounded-2xl border border-white/10">
            <div>
               <h2 className="text-center text-3xl font-extrabold text-white">Sign in to your account</h2>
               <p className="mt-2 text-center text-sm text-gray-400">
                  Or <Link href="/signup" className="font-medium text-purple-400 hover:text-purple-300">create a new account</Link>
               </p>
            </div>
            {error && <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded-lg text-sm">{error}</div>}
            <form id="login-form" className="mt-8 space-y-6" onSubmit={handleSubmit}>
               <div className="space-y-4">
                  <div>
                     <input 
                        type="email" 
                        name="email"
                        required 
                        value={email} 
                        onChange={(e) => setEmail(e.target.value)} 
                        className="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent" 
                        placeholder="Email address" 
                     />
                  </div>
                  <div>
                     <input 
                        type="password" 
                        name="password"
                        required 
                        value={password} 
                        onChange={(e) => setPassword(e.target.value)} 
                        className="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent" 
                        placeholder="Password" 
                     />
                  </div>
               </div>
               <button 
                  type="submit" 
                  disabled={loading} 
                  className="w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
               >
                  {loading ? "Signing in..." : "Sign in"}
               </button>
            </form>
         </div>
      </div>
   )
}'''












        def generate_signup_page() -> str:
            return '''"use client"

import React, { useState } from "react"
import Link from "next/link"

export default function SignupPage() {
   const [name, setName] = useState("")
   const [email, setEmail] = useState("")
   const [password, setPassword] = useState("")
   const [confirmPassword, setConfirmPassword] = useState("")
   const [error, setError] = useState("")
   const [loading, setLoading] = useState(false)
   const [showSuccessModal, setShowSuccessModal] = useState(false)

   const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault()
      setError("")
      if (password !== confirmPassword) { 
         setError("Passwords do not match"); 
         return; 
      }
      if (password.length < 6) { 
         setError("Password must be at least 6 characters"); 
         return; 
      }
      setLoading(true)
      try {
         const response = await fetch(`/api/auth/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password }),
         })
         const data = await response.json()
         if (data.success) {
            setShowSuccessModal(true)
            setName("")
            setEmail("")
            setPassword("")
            setConfirmPassword("")
         } else { 
            setError(data.detail || data.error || "Signup failed") 
         }
      } catch (err) { 
         setError("Network error. Please try again.") 
      } finally { 
         setLoading(false) 
      }
   }

   return (
      <>
         {/* Success Modal */}
         {showSuccessModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
               <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setShowSuccessModal(false)} />
               <div className="relative bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl border border-white/10 shadow-2xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center mx-auto mb-4">
                     <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                     </svg>
                  </div>
                  <h3 className="text-xl font-bold text-center text-white mb-2">Account Created!</h3>
                  <p className="text-center text-gray-400 mb-6">
                     Your account has been created successfully. You can now log in.
                  </p>
                  <button
                     onClick={() => setShowSuccessModal(false)}
                     className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold transition-all duration-300"
                  >
                     Close
                  </button>
               </div>
            </div>
         )}

         <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-950 via-zinc-950 to-pink-950 py-12 px-4">
            <div className="max-w-md w-full space-y-8 bg-white/5 backdrop-blur-sm p-8 rounded-2xl border border-white/10">
               <div>
                  <h2 className="text-center text-3xl font-extrabold text-white">Create your account</h2>
                  <p className="mt-2 text-center text-sm text-gray-400">
                     Already have an account? <Link href="/login" className="font-medium text-purple-400 hover:text-purple-300">Sign in</Link>
                  </p>
               </div>
               {error && <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded-lg text-sm">{error}</div>}
               <form id="signup-form" className="mt-8 space-y-6" onSubmit={handleSubmit}>
                  <div className="space-y-4">
                     <div>
                        <input 
                           type="text" 
                           name="name"
                           required 
                           value={name} 
                           onChange={(e) => setName(e.target.value)} 
                           className="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent" 
                           placeholder="Full name" 
                        />
                     </div>
                     <div>
                        <input 
                           type="email" 
                           name="email"
                           required 
                           value={email} 
                           onChange={(e) => setEmail(e.target.value)} 
                           className="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent" 
                           placeholder="Email address" 
                        />
                     </div>
                     <div>
                        <input 
                           type="password" 
                           name="password"
                           required 
                           value={password} 
                           onChange={(e) => setPassword(e.target.value)} 
                           className="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent" 
                           placeholder="Password (min. 6 characters)" 
                        />
                     </div>
                     <div>
                        <input 
                           type="password" 
                           name="confirmPassword"
                           required 
                           value={confirmPassword} 
                           onChange={(e) => setConfirmPassword(e.target.value)} 
                           className="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent" 
                           placeholder="Confirm password" 
                        />
                     </div>
                  </div>
                  <button 
                     type="submit" 
                     disabled={loading} 
                     className="w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                     {loading ? "Creating account..." : "Sign up"}
                  </button>
               </form>
            </div>
         </div>
      </>
   )
}'''























        def generate_signup_api_route() -> str:
            return '''import { NextRequest, NextResponse } from "next/server";
import { hash } from "bcryptjs";
import { sign } from "jsonwebtoken";
import { neon } from '@neondatabase/serverless';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { name, email, password } = body;

        if (!email || !password) {
            return NextResponse.json(
                { success: false, error: "Email and password required" },
                { status: 400 }
            );
        }

        // Use DATABASE_URL from Vercel environment variables
        const DATABASE_URL = process.env.DATABASE_URL;
        
        if (!DATABASE_URL) {
            console.error("DATABASE_URL not configured in environment");
            return NextResponse.json(
                { success: false, error: "Database not configured. Please add DATABASE_URL to your environment variables." },
                { status: 500 }
            );
        }

        const sql = neon(DATABASE_URL);

        await sql`
            CREATE TABLE IF NOT EXISTS users (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        `;

        await sql`
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        `;

        await sql`
            CREATE TABLE IF NOT EXISTS user_credits (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
                credits INTEGER DEFAULT 10,
                daily_credits_used INTEGER DEFAULT 0,
                daily_reset_date DATE DEFAULT CURRENT_DATE,
                monthly_credits_used INTEGER DEFAULT 0,
                monthly_reset_date DATE DEFAULT CURRENT_DATE
            );
        `;

        const existingUser = await sql`
            SELECT id FROM users WHERE email = ${email}
        `;

        if (existingUser.length > 0) {
            return NextResponse.json(
                { success: false, error: "User already exists" },
                { status: 400 }
            );
        }

        const hashedPassword = await hash(password, 10);

        const newUser = await sql`
            INSERT INTO users (email, name, password_hash)
            VALUES (${email}, ${name || ""}, ${hashedPassword})
            RETURNING id, email, name
        `;

        const user = newUser[0];
        const token = sign(
            { userId: user.id, email: user.email },
            process.env.JWT_SECRET || "your-secret-key",
            { expiresIn: "30d" }
        );

        const expiresAt = new Date();
        expiresAt.setDate(expiresAt.getDate() + 30);

        await sql`
            INSERT INTO sessions (user_id, token, expires_at)
            VALUES (${user.id}, ${token}, ${expiresAt.toISOString()})
        `;

        await sql`
            INSERT INTO user_credits (user_id)
            VALUES (${user.id})
            ON CONFLICT (user_id) DO NOTHING
        `;

        return NextResponse.json({
            success: true,
            user: {
                id: user.id,
                email: user.email,
                name: user.name,
            },
            access_token: token,
            token_type: "bearer",
        });
    } catch (error) {
        console.error("Signup error:", error);
        return NextResponse.json(
            { success: false, error: "Internal server error" },
            { status: 500 }
        );
    }
}'''









        def generate_login_api_route() -> str:
            return '''import { NextRequest, NextResponse } from "next/server";
import { compare } from "bcryptjs";
import { sign } from "jsonwebtoken";
import { neon } from '@neondatabase/serverless';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password, db_connection_string } = body;

    if (!email || !password) {
      return NextResponse.json(
        { success: false, error: "Email and password required" },
        { status: 400 }
      );
    }

    if (!db_connection_string) {
      return NextResponse.json(
        { success: false, error: "Database connection required", requires_db: true },
        { status: 400 }
      );
    }

    const sql = neon(db_connection_string);

    const users = await sql`
      SELECT id, email, name, password_hash FROM users WHERE email = ${email}
    `;

    if (users.length === 0) {
      return NextResponse.json(
        { success: false, error: "Invalid credentials" },
        { status: 401 }
      );
    }

    const user = users[0];
    const isValid = await compare(password, user.password_hash);

    if (!isValid) {
      return NextResponse.json(
        { success: false, error: "Invalid credentials" },
        { status: 401 }
      );
    }

    const token = sign(
      { userId: user.id, email: user.email },
      process.env.JWT_SECRET || "your-secret-key",
      { expiresIn: "30d" }
    );

    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + 30);

    await sql`
      INSERT INTO sessions (user_id, token, expires_at)
      VALUES (${user.id}, ${token}, ${expiresAt.toISOString()})
      ON CONFLICT (user_id) DO UPDATE SET token = ${token}, expires_at = ${expiresAt.toISOString()}
    `;

    return NextResponse.json({
      success: true,
      user: { id: user.id, email: user.email, name: user.name },
      access_token: token,
      token_type: "bearer",
    });
  } catch (error) {
    console.error("Login error:", error);
    return NextResponse.json(
      { success: false, error: "Internal server error" },
      { status: 500 }
    );
  }
}'''














































        def generate_new_page_content(file_path: str) -> str:
            """Generate content for new files based on file path"""
            
            # ========== API ROUTE - Return API route code ==========
            if "api/" in file_path and ("signup" in file_path.lower() or "login" in file_path.lower()):
                if "signup" in file_path.lower():
                    print(f"   🔧 Generating API route code for: {file_path}")
                    return generate_signup_api_route()
                elif "login" in file_path.lower():
                    print(f"   🔧 Generating API route code for: {file_path}")
                    return generate_login_api_route()
            
            # ========== PAGE COMPONENT ==========
            page_name = file_path.split('/')[-1].replace('.tsx', '').replace('.jsx', '').replace('.ts', '').replace('.js', '')
            page_title = page_name.replace('-', ' ').title()
            
            if "login" in file_path.lower():
                return generate_login_page()
            elif "signup" in file_path.lower():
                return generate_signup_page()
            else:
                return f'''import React from 'react'

export default function {page_title.replace(' ', '')}Page() {{
   return (
      <div className="py-20 container mx-auto px-4">
         <h1 className="text-4xl font-bold mb-8 text-white">{page_title}</h1>
         <p className="text-gray-300">Welcome to our {page_title.lower()} page.</p>
      </div>
   )
}}
'''










        
        # Edit each file
        edit_results = []
        
        # Track if we created auth pages
        auth_created = False
        
        
        
        
        
        
        
        
        
        
        
        for file_path in files_to_edit:
            current_content = source_files.get(file_path, "")
            is_new_file = file_path not in all_files
            
            if not current_content and any(x in file_path.lower() for x in ['login', 'signup', 'auth']):
                print(f"📝 Creating new auth file: {file_path}")
                current_content = generate_new_page_content(file_path)
                auth_created = True  # ← ADD THIS LINE HERE
                edit_results.append({
                    "file_path": file_path,
                    "original_content": "",
                    "updated_content": current_content,
                    "success": True,
                    "is_new_file": True
                })
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                 # ⭐⭐⭐ ADD THIS - Update Navigation.tsx ⭐⭐⭐
                navigation_path = "components/Navigation.tsx"
                if navigation_path in updated_files:
                    nav_content = updated_files[navigation_path]
                    print(f"  🔧 Original navigation content length: {len(nav_content)}")
                    
                    # Check if signup already exists
                    if 'signup' not in nav_content.lower() and 'Sign Up' not in nav_content:
                        # Find the div with className="hidden md:flex space-x-6"
                        nav_div_pattern = r'(<div className="hidden md:flex space-x-6">)([\s\S]*?)(</div>)'
                        match = re.search(nav_div_pattern, nav_content, re.DOTALL)
                        
                        if match:
                            # Add signup link inside this div
                            signup_link = '''
                                <Link 
                                    href="/signup" 
                                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition ml-4"
                                >
                                    Sign Up
                                </Link>'''
                            
                            new_nav_content = match.group(1) + match.group(2) + signup_link + match.group(3)
                            nav_content = nav_content.replace(match.group(0), new_nav_content)
                            
                            updated_files[navigation_path] = nav_content
                            edit_results.append({
                                "file_path": navigation_path,
                                "original_content": "",
                                "updated_content": nav_content,
                                "success": True,
                                "is_new_file": False,
                                "changes": ["Added Sign Up button to navigation"]
                            })
                            print(f"  ✅ Added Sign Up button to Navigation.tsx")
                            
                            # Debug: Show updated navigation
                            print(f"  🔧 Updated navigation preview: {nav_content[:500]}")
                        else:
                            print(f"  ⚠️ Could not find navigation div with class 'hidden md:flex space-x-6'")
                            print(f"  🔧 Navigation content: {nav_content[:300]}")
                    else:
                        print(f"  ⚠️ Sign Up already exists in navigation")
                else:
                    print(f"  ⚠️ Navigation.tsx not found in updated_files")
                # ⭐⭐⭐ END OF ADDED CODE ⭐⭐⭐
                
                
                
                
                
                continue
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
            
            elif not current_content:
                print(f"⚠️ File not found: {file_path}")
                continue
            
            print(f"\n✏️ Editing: {file_path}")
            
            edit_prompt = f"""FILE: {file_path}
EDIT REQUEST: {edit_description}

CURRENT CODE:
{current_content}

Make the requested change. Return ONLY the updated code, no markdown, no explanations."""

            try:
                response_text = await model_router.generate_content(
                    prompt=edit_prompt,
                    config={"temperature": 0.01, "max_output_tokens": 1019200}
                )
                updated_content = extract_code_from_response(response_text.strip())
                
                if updated_content and len(updated_content) > 50 and updated_content != current_content:
                    edit_results.append({
                        "file_path": file_path,
                        "original_content": current_content,
                        "updated_content": updated_content,
                        "success": True,
                        "is_new_file": False
                    })
                    print(f"✅ Edited {file_path}")
            except Exception as e:
                print(f"❌ Error editing {file_path}: {e}")
        
        if db_schema_created:
            env_content = f'''# Database Configuration
DATABASE_URL={user_db_connection_string}

# JWT Secret
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this

# API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
'''
            updated_files[".env"] = env_content
            print(f"✅ Added .env file")
        
        if not edit_results and not db_schema_created:
            return {
                "success": False,
                "error": "No changes were made. Please be more specific.",
                "message": "Could not apply the requested edit"
            }
        
        for result in edit_results:
            updated_files[result["file_path"]] = result["updated_content"]
            
            
            
            
            
            
        
        
        
        
        
        preview_html = existing_preview
        should_regenerate = force_regenerate or len(edit_results) > 0 or db_schema_created
      
      
      
      
      
      
      
      
      
      
      
      
      
      
      
      
      
        if should_regenerate:
            print(f"🔄 Regenerating preview...")
            try:
                project_name = project_name_from_request or "Scorpio Project"
                for file_path, content in updated_files.items():
                    if "Navigation.tsx" in file_path and isinstance(content, str):
                        brand_match = re.search(r'<Link[^>]*>([^<]+)</Link>', content)
                        if brand_match:
                            project_name = brand_match.group(1).strip()
                        break
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                # ✅ USE THE CLOUDINARY URL ALREADY LOADED FROM DATABASE
                # The variable original_cloudinary_image_url already contains the URL from the database
                # DO NOT overwrite it - only use it if it exists
                
                if original_cloudinary_image_url:
                    print(f"📸 Using Cloudinary URL from database: {original_cloudinary_image_url[:80]}...")
                else:
                    # Only fallback to checking files if database didn't have it
                    if 'preview_url' in updated_files and 'image/upload' in str(updated_files['preview_url']):
                        original_cloudinary_image_url = updated_files['preview_url']
                    elif 'thumbnail_url' in updated_files and 'image/upload' in str(updated_files['thumbnail_url']):
                        original_cloudinary_image_url = updated_files['thumbnail_url']
                    elif 'preview_url' in all_files and 'image/upload' in str(all_files['preview_url']):
                        original_cloudinary_image_url = all_files['preview_url']
                    elif 'thumbnail_url' in all_files and 'image/upload' in str(all_files['thumbnail_url']):
                        original_cloudinary_image_url = all_files['thumbnail_url']
                    
                    if original_cloudinary_image_url:
                        print(f"📸 Found Cloudinary URL in files (fallback): {original_cloudinary_image_url[:80]}...")
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                preview_result = await generate_preview_internal(
                    updated_files,
                    project_name,
                    existing_image_url=original_cloudinary_image_url 
                    )
                if preview_result.get("success"):
                    preview_html = preview_result.get("preview_html")
                    
                    # ✅ PRESERVE CLOUDINARY IMAGE URL IN THE HTML
                    if original_cloudinary_image_url:
                        # Replace local image path with Cloudinary URL
                        preview_html = preview_html.replace('/images/image_1.jpg', original_cloudinary_image_url)
                        preview_html = re.sub(
                            r'src="[^"]*image_1\.jpg[^"]*"',
                            f'src="{original_cloudinary_image_url}"',
                            preview_html
                        )
                        print(f"✅ Restored Cloudinary image URL in preview")
                    
                    # Also call preserve_cloudinary_urls for any other Cloudinary URLs
                    preview_html = preserve_cloudinary_urls(preview_html, updated_files)
                    
                    updated_files["preview_html"] = preview_html
                    print(f"✅ Preview regenerated!")
                    
                    # SAVE TO DISK - Option A
                    await save_regenerated_preview(
                        preview_html=preview_html,
                        project_name=project_name,
                        project_id=project_id
                    )
                else:
                    preview_html = existing_preview
            except Exception as e:
                print(f"⚠️ Preview error: {e}")
                preview_html = existing_preview
                
                
                
                
                
                
                
                
                
                
                
                
                
                
      
        print(f"\n{'='*70}")
        print(f"✅ EDIT COMPLETE: {len(edit_results)} file(s) modified")
        for result in edit_results:
            new_flag = " (NEW)" if result.get("is_new_file") else ""
            print(f"   - {result['file_path']}{new_flag}")
            
        # After creating signup page, create ONLY the corresponding API route
        if auth_created or db_schema_created:
            print(f"\n📡 Creating API route for authentication...")
            
            # Check which auth page was requested and create only that API route
            signup_requested = any("signup" in f for f in files_to_edit)
            login_requested = any("login" in f for f in files_to_edit)
            
            if signup_requested:
                signup_api_path = "app/api/auth/signup/route.ts"
                if signup_api_path not in updated_files:
                    updated_files[signup_api_path] = generate_signup_api_route()
                    edit_results.append({
                        "file_path": signup_api_path,
                        "original_content": "",
                        "updated_content": generate_signup_api_route(),
                        "success": True,
                        "is_new_file": True
                    })
                    print(f"✅ Created signup API route: {signup_api_path}")
                
                # ========== UPDATE package.json WITH REQUIRED DEPENDENCIES ==========
                print(f"\n📦 Managing package.json...")
                
                package_json_path = "package.json"
                current_package_json = updated_files.get(package_json_path, "")
                
                if current_package_json:
                    try:
                        # Use the manage_package_json function
                        updated_content, changes = await manage_package_json(current_package_json, edit_description)
                        
                        if updated_content and changes:
                            updated_files[package_json_path] = updated_content
                            
                            # Add to edit_results
                            edit_results.append({
                                "file_path": package_json_path,
                                "original_content": current_package_json,
                                "updated_content": updated_content,
                                "success": True,
                                "is_new_file": False,
                                "changes": changes
                            })
                            print(f"✅ package.json updated with {len(changes)} change(s)")
                            for change in changes:
                                print(f"   • {change}")
                        else:
                            print(f"✅ No changes needed to package.json")
                    except Exception as e:
                        print(f"⚠️ Failed to update package.json: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"⚠️ package.json not found - cannot manage dependencies")
            
            if login_requested:
                login_api_path = "app/api/auth/login/route.ts"
                if login_api_path not in updated_files:
                    updated_files[login_api_path] = generate_login_api_route()
                    edit_results.append({
                        "file_path": login_api_path,
                        "original_content": "",
                        "updated_content": generate_login_api_route(),
                        "success": True,
                        "is_new_file": True
                    })
                    print(f"✅ Created login API route: {login_api_path}")
        
        if db_schema_created:
            print(f"   - Database schema created on user's Neon DB")
        
        print(f"{'='*70}\n")
      
        return {
            "success": True,
            "edits": edit_results,
            "files_edited": [r["file_path"] for r in edit_results],
            "preview_html": preview_html,
            "database_configured": db_schema_created,
            "message": f"Successfully applied: {edit_description}" + (f" + Neon database configured!" if db_schema_created else "")
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
                "max_output_tokens": 819200,
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
                config={"temperature": 0.2, "max_output_tokens": 819200}
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
            config={"temperature": 0.3, "max_output_tokens": 819200}
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
        
        # ========== DEBUG: CHECK IMAGE FORMATS ==========
        print("\n" + "="*70)
        print("🔍 IMAGE FORMAT DEBUG - Checking what format images are in:")
        print("="*70)
        
        image_files_found = False
        for file_path, content in files.items():
            if file_path.startswith("public/images/"):
                image_files_found = True
                print(f"\n📸 File: {file_path}")
                print(f"   Type: {type(content).__name__}")
                
                if isinstance(content, dict):
                    print(f"   Dict keys: {list(content.keys())}")
                elif isinstance(content, str):
                    print(f"   String length: {len(content)}")
                    print(f"   First 200 chars: {content[:200]}")
                    if content.startswith('{'):
                        try:
                            import json as json_module
                            parsed = json_module.loads(content)
                            print(f"   ✓ String is valid JSON")
                            print(f"   JSON keys: {list(parsed.keys())}")
                        except:
                            print(f"   ✗ String looks like JSON but parse failed")
        
        if not image_files_found:
            print("\n⚠️ No image files found in the project!")
        
        print("="*70 + "\n")
        
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
        uploaded_image_paths = []
        
        for file_path, content in files.items():
            # Skip non-image files
            if not file_path.startswith("public/images/"):
                continue
            
            is_binary_image = False
            base64_data = None
            
            print(f"  📸 Processing: {file_path}")
            
            # Case 1: String that is JSON with __type = "binary_image"
            if isinstance(content, str) and content.startswith('{') and '"__type"' in content:
                try:
                    import json as json_module
                    data_obj = json_module.loads(content)
                    
                    if data_obj.get("__type") == "binary_image":
                        data_content = data_obj.get("data")
                        
                        if isinstance(data_content, dict):
                            # Convert Uint8Array dict to bytes
                            print(f"     Converting Uint8Array dict to bytes...")
                            byte_list = []
                            # Sort keys numerically to ensure correct order
                            for key in sorted(data_content.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                                if key.isdigit():
                                    byte_list.append(data_content[key])
                            
                            binary_bytes = bytes(byte_list)
                            print(f"     Converted {len(binary_bytes)} bytes")
                            
                            # Convert to base64
                            import base64 as b64
                            base64_data = b64.b64encode(binary_bytes).decode('utf-8')
                            is_binary_image = True
                            print(f"     Converted to base64 (length: {len(base64_data)})")
                            
                        elif isinstance(data_content, str):
                            base64_data = data_content
                            is_binary_image = True
                            print(f"     Found string data")
                            
                except Exception as e:
                    print(f"     Error parsing JSON: {e}")
            
            # Case 2: Already a dict (fallback)
            elif isinstance(content, dict) and content.get("__type") == "binary_image":
                data_content = content.get("data")
                if isinstance(data_content, dict):
                    print(f"     Converting Uint8Array dict to bytes...")
                    byte_list = []
                    for key in sorted(data_content.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                        if key.isdigit():
                            byte_list.append(data_content[key])
                    binary_bytes = bytes(byte_list)
                    import base64 as b64
                    base64_data = b64.b64encode(binary_bytes).decode('utf-8')
                    is_binary_image = True
                    print(f"     Converted dict to base64 (length: {len(base64_data)})")
            
            # Case 3: Raw base64 string
            elif isinstance(content, str) and len(content) > 1000 and not content.startswith('<'):
                base64_data = content
                is_binary_image = True
                print(f"     Using as raw base64 (length: {len(base64_data)})")
            
            # Case 4: String with __binary_base64__ prefix
            elif isinstance(content, str) and content.startswith("__binary_base64__"):
                base64_data = content.replace("__binary_base64__", "")
                is_binary_image = True
                print(f"     Found __binary_base64__ prefix (length: {len(base64_data)})")
            
            if is_binary_image and base64_data:
                try:
                    print(f"  ☁️ Uploading to Cloudinary: {file_path}")
                    
                    # Clean base64 data (remove any data:image prefix)
                    if ',' in base64_data and base64_data.startswith('data:'):
                        base64_data = base64_data.split(',')[1]
                    
                    # Also remove any whitespace or newlines
                    base64_data = base64_data.strip().replace('\n', '').replace('\r', '')
                    
                    upload_result = cloudinary.uploader.upload(
                        f"data:image/jpeg;base64,{base64_data}",
                        folder="scorpio_projects",
                        public_id=file_path.replace('/', '_').replace('.', '_'),
                        overwrite=True
                    )
                    
                    image_urls[file_path] = upload_result['secure_url']
                    uploaded_image_paths.append(file_path)
                    print(f"  ✅ Uploaded successfully!")
                    print(f"     URL: {upload_result['secure_url'][:80]}...")
                    image_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Failed to upload {file_path}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"  ⚠️ Could not extract image data from {file_path}")
        
        print(f"\n✅ STEP 1 COMPLETE: Uploaded {image_count} images to Cloudinary\n")
        
        # Log all uploaded URLs
        if image_urls:
            print("📋 CLOUDINARY URLS:")
            for local_path, url in image_urls.items():
                public_path = "/" + local_path.replace("public/", "")
                print(f"  {public_path} -> {url}")
        print()
        
        # ========== STEP 1.5: REMOVE IMAGES FROM DEPLOYMENT FILES ==========
        print("🗑️ STEP 1.5: Removing uploaded images from deployment package...")
        print("-" * 40)
        
        # Create a new files dict WITHOUT the images that were uploaded
        files_without_images = {}
        removed_count = 0
        
        for file_path, content in files.items():
            # Skip ALL image files that were uploaded
            if file_path in uploaded_image_paths:
                print(f"  🗑️ Removing {file_path} from deployment (using Cloudinary URL)")
                removed_count += 1
                continue
            # Also skip any file in public/images/ that might have been missed
            if file_path.startswith("public/images/"):
                print(f"  🗑️ Removing {file_path} from deployment (using Cloudinary URL)")
                removed_count += 1
                continue
            files_without_images[file_path] = content
        
        print(f"  ✅ Removed {removed_count} image files from deployment")
        print(f"  📁 Remaining files: {len(files_without_images)}")
        
        # Use the filtered files for the rest of the deployment
        files = files_without_images
        
        # ========== STEP 2: REPLACE IMAGE PATHS IN ALL FILES ==========
        print("\n🔄 STEP 2: Replacing image paths with Cloudinary URLs...")
        print("-" * 40)
        
        deployment_files = {}
        
        # Create path mapping
        path_to_url = {}
        for local_path, cloudinary_url in image_urls.items():
            public_path = "/" + local_path.replace("public/", "")
            path_to_url[public_path] = cloudinary_url
            print(f"  📋 Mapping: {public_path} -> {cloudinary_url[:60]}...")
        
        replacements_count = 0
        
        for file_path, content in files.items():
            # Skip preview_html and metadata
            if file_path == "preview_html" or file_path == "__image_urls__":
                continue
            
            # For text files, replace image paths
            if isinstance(content, str):
                updated_content = content
                file_replaced = False
                
                for old_path, new_url in path_to_url.items():
                    if old_path in updated_content:
                        updated_content = updated_content.replace(old_path, new_url)
                        file_replaced = True
                        replacements_count += 1
                        print(f"  🔄 {file_path}: '{old_path}' -> Cloudinary URL")
                
                deployment_files[file_path] = updated_content
                if file_replaced:
                    print(f"  ✅ {file_path} updated with Cloudinary URLs")
            else:
                deployment_files[file_path] = content
        
        print(f"\n✅ STEP 2 COMPLETE: Replaced {replacements_count} image references in {len(deployment_files)} files\n")
        
        # ========== STEP 3: CREATE/GET PROJECT AND SET ENV VARS ==========
        print("🌍 STEP 3: Setting up Vercel project and environment variables...")
        print("-" * 40)
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # First, get or create the project
            project_id = None
            
            # Check if project exists
            projects_response = await client.get(
                f"https://api.vercel.com/v9/projects/{project_name}",
                headers={"Authorization": f"Bearer {vercel_token}"}
            )
            
            if projects_response.status_code == 200:
                project_data = projects_response.json()
                project_id = project_data.get("id")
                print(f"📁 Found existing project: {project_id}")
            else:
                # Create new project
                create_response = await client.post(
                    "https://api.vercel.com/v9/projects",
                    headers={"Authorization": f"Bearer {vercel_token}"},
                    json={
                        "name": project_name,
                        "framework": "nextjs"
                    }
                )
                if create_response.status_code in [200, 201]:
                    project_data = create_response.json()
                    project_id = project_data.get("id")
                    print(f"📁 Created new project: {project_id}")
                else:
                    print(f"⚠️ Failed to create project: {create_response.status_code}")
            
            # ========== STEP 4: SET ENVIRONMENT VARIABLES ==========
            if project_id and env_vars:
                print(f"\n🌍 Setting environment variables BEFORE deployment...")
                for key, value in env_vars.items():
                    # First, delete existing variable if exists
                    env_response = await client.get(
                        f"https://api.vercel.com/v1/projects/{project_id}/env",
                        headers={"Authorization": f"Bearer {vercel_token}"}
                    )
                    if env_response.status_code == 200:
                        existing_vars = env_response.json()
                        for var in existing_vars:
                            if var.get("key") == key:
                                await client.delete(
                                    f"https://api.vercel.com/v1/projects/{project_id}/env/{var.get('id')}",
                                    headers={"Authorization": f"Bearer {vercel_token}"}
                                )
                                print(f"  🗑️ Removed existing {key}")
                    
                    # Set new environment variable
                    set_response = await client.post(
                        f"https://api.vercel.com/v1/projects/{project_id}/env",
                        headers={
                            "Authorization": f"Bearer {vercel_token}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "key": key,
                            "value": value,
                            "type": "encrypted",
                            "target": ["production", "preview", "development"]
                        }
                    )
                    if set_response.status_code in [200, 201]:
                        print(f"  ✅ Set {key} environment variable")
                    elif set_response.status_code == 409:
                        print(f"  ✅ {key} already exists")
                    else:
                        print(f"  ⚠️ Failed to set {key}: {set_response.status_code}")
                
                print(f"\n✅ Environment variables configured on Vercel project")
            
            # ========== STEP 5: CREATE DEPLOYMENT ==========
            print(f"\n🚀 STEP 5: Creating deployment...")
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
                
                # Create deployment
                deploy_payload = {
                    "name": project_name,
                    "files": file_list,
                    "projectSettings": {
                        "framework": "nextjs",
                        "buildCommand": "npm run build",
                        "outputDirectory": ".next",
                        "installCommand": "npm install"
                    }
                }
                
                deploy_response = await client.post(
                    "https://api.vercel.com/v13/deployments",
                    headers={
                        "Authorization": f"Bearer {vercel_token}",
                        "Content-Type": "application/json",
                    },
                    json=deploy_payload
                )
                
                if deploy_response.status_code not in [200, 201]:
                    error_data = deploy_response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    print(f"  ❌ Vercel API error: {error_data}")
                    raise Exception(f"Vercel API error: {error_msg}")
                
                deploy_data = deploy_response.json()
                deployment_url = deploy_data.get("url")
                
                print(f"\n{'='*70}")
                print(f"✅ DEPLOYMENT SUCCESSFUL!")
                print(f"🔗 URL: https://{deployment_url}")
                print(f"📁 Project ID: {project_id}")
                print(f"📸 Images uploaded to Cloudinary: {image_count}")
                print(f"{'='*70}\n")
                
                return {
                    "success": True,
                    "message": "Deployed to Vercel successfully!",
                    "deployment_url": f"https://{deployment_url}",
                    "deployment_id": deploy_data.get("id"),
                    "project_id": project_id,
                    "project_name": project_name,
                    "images_uploaded": image_count,
                    "env_vars_set": len(env_vars) if env_vars else 0
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
                        "max_output_tokens": 400000,
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

        # ✅ FIXED: Define BOTH variables
        nav_buttons_html = ""
        mobile_nav_html = ""  # ← THIS WAS MISSING - ADD THIS LINE
        
        for path, label in nav_links:
            nav_buttons_html += f'<button onclick="showPage(\'{path}\')" class="nav-link px-4 py-2 rounded-lg transition-all text-gray-300 hover:text-white hover:bg-purple-500/20">{label}</button>'
            mobile_nav_html += f'<a href="{path}" onclick="showPage(\'{path}\'); return false;" class="block px-4 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-purple-500/20">{label}</a>'

        # Build pages
        pages_html = ""
        page_map = {}
        for path, content in pages_content.items():
            page_id = "page_home" if path == "/" else f"page_{path.lstrip('/').replace('/', '_')}"
            page_map[path] = page_id
            active = 'active' if path == '/' else ''
            pages_html += f'<div id="{page_id}" class="page {active}"><div class="container mx-auto px-4 py-8">{content}</div></div>'

        # Build page map JavaScript
        page_map_js = "{" + ", ".join([f'"{k}": "{v}"' for k, v in page_map.items()]) + "}"

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
        const pageMap = {page_map_js};
        
        function showPage(path) {{
            const pageId = pageMap[path] || 'page_home';
            document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
            const targetPage = document.getElementById(pageId);
            if (targetPage) targetPage.classList.add('active');
            
            document.querySelectorAll('.nav-link').forEach(btn => {{
                btn.classList.remove('active', 'bg-purple-500/20');
                if (btn.getAttribute('onclick')?.includes(path)) {{
                    btn.classList.add('active', 'bg-purple-500/20');
                }}
            }});
            
            window.history.pushState({{}}, '', path);
        }}
        
        // Mobile menu toggle
        const mobileMenuBtn = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenuBtn && mobileMenu) {{
            mobileMenuBtn.addEventListener('click', () => {{
                mobileMenu.classList.toggle('hidden');
            }});
        }}
        
        // Handle popstate (back/forward buttons)
        window.addEventListener('popstate', () => {{
            showPage(window.location.pathname);
        }});
        
        // Initial page load
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
                    "cloudinary_image_url": project.cloudinary_image_url,  # ✅ ADD THIS LINE
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
                Project.files_url,       # Cloudinary URL for ZIP file
                Project.cloudinary_image_url  # ← Make sure this is included!
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
                    "files_url": row[8],        # ← Cloudinary URL (NEW)
                    "cloudinary_image_url": row[9]  # ← Add this line
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
        incoming_project_id = body.get("id")  # ← GET THE INCOMING ID
        
        # ========== EXTRACT BRAND NAME ==========
        extracted_name = extract_brand_name(files)
        if extracted_name:
            name = extracted_name
            print(f"🏷️ Extracted brand name: {name}")
        
        # ========== EXTRACT CLOUDINARY IMAGE URL ==========
        cloudinary_image_url = None
        
        if "__cloudinary_image_url__" in files:
            cloudinary_image_url = files.get("__cloudinary_image_url__")
            print(f"📸 Found Cloudinary image URL in files: {cloudinary_image_url[:80] if cloudinary_image_url else 'None'}...")
        
        if not cloudinary_image_url and "preview_url" in files:
            val = files.get("preview_url")
            if val and "image/upload" in val:
                cloudinary_image_url = val

        if not cloudinary_image_url and "thumbnail_url" in files:
            val = files.get("thumbnail_url")
            if val and "image/upload" in val:
                cloudinary_image_url = val

        if not cloudinary_image_url and preview_html:
            import re
            matches = re.findall(r'https://res\.cloudinary\.com/[^/]+/image/upload/[^"\']+', preview_html)
            if matches:
                cloudinary_image_url = matches[0]
                print(f"📸 Found Cloudinary image URL in preview HTML: {cloudinary_image_url[:80]}...")

        if not cloudinary_image_url and "__image_urls__" in files:
            image_urls = files.get("__image_urls__", {})
            for local_path, url in image_urls.items():
                if "image/upload" in url:
                    cloudinary_image_url = url
                    break

        # ========== AUTH ==========
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "")
        
        if not token:
            return {"success": False, "message": "Authentication required"}
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_email = payload.get('email')
        except Exception as e:
            return {"success": False, "message": "Invalid token"}
        
        async with AsyncSessionLocal() as session:
            # Get user
            user_stmt = select(User).where(User.email == user_email)
            user_result = await session.execute(user_stmt)
            db_user = user_result.scalar_one_or_none()
            
            if not db_user:
                return {"success": False, "message": "User not found"}
            
            user_id = db_user.id
            
            # ========== FIND EXISTING PROJECT - FIXED ==========
            # ONLY match by explicit ID
            # DO NOT match by name or prompt - this was the bug!
            existing_project = None
            
            # Only check by incoming ID if it exists and is not "new"
            if incoming_project_id and incoming_project_id != "new":
                stmt = select(Project).where(
                    Project.id == incoming_project_id,
                    Project.user_id == user_id
                )
                result = await session.execute(stmt)
                existing_project = result.scalar_one_or_none()
                if existing_project:
                    print(f"✅ Found existing project by ID: {incoming_project_id}")
            # ❌ REMOVED: Fall back to name match (this was causing the bug)
            # No more matching by name - each new project gets a fresh ID
            
            # Load Cloudinary image URL from DB if available
            if not cloudinary_image_url and existing_project and existing_project.cloudinary_image_url:
                cloudinary_image_url = existing_project.cloudinary_image_url
                print(f"📸 Loaded Cloudinary image URL from existing project in DB: {cloudinary_image_url[:80]}...")

            # Use existing ID or generate new one
            project_id = existing_project.id if existing_project else incoming_project_id or str(uuid.uuid4())
            
            is_update = existing_project is not None
            
            print(f"{'🔄 Updating' if is_update else '🆕 Creating'} project: {project_id}")
            print(f"📸 Cloudinary image URL: {cloudinary_image_url[:80] if cloudinary_image_url else 'NOT FOUND'}")

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
            
            # ========== UPLOAD TO CLOUDINARY ==========
            preview_url = existing_project.preview_url if existing_project else None
            files_url = existing_project.files_url if existing_project else None
            thumbnail_url = existing_project.thumbnail_url if existing_project else None
            
            # Upload new preview HTML
            if preview_html:
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp:
                        tmp.write(preview_html)
                        tmp_path = tmp.name
                    
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
                    os.unlink(tmp_path)
                except Exception as e:
                    print(f"⚠️ Failed to upload preview: {e}")
            
            # Upload files as ZIP
            if files:
                try:
                    import zipfile
                    from io import BytesIO
                    
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for file_path, content in files.items():
                            if file_path.startswith("__") and file_path.endswith("__"):
                                continue
                            if file_path == "preview_html":
                                continue
                            if isinstance(content, dict):
                                content = json.dumps(content, indent=2)
                            elif not isinstance(content, str):
                                content = str(content)
                            zipf.writestr(file_path, content)
                    
                    zip_buffer.seek(0)
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
            
            # Generate thumbnail
            if preview_html and not thumbnail_url:
                try:
                    thumbnail_local_path = await generate_thumbnail_from_html(preview_html, project_id)
                    if thumbnail_local_path and os.path.exists(thumbnail_local_path):
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
                        print(f"☁️ Thumbnail uploaded: {thumbnail_url[:60]}...")
                        os.unlink(thumbnail_local_path)
                except Exception as e:
                    print(f"⚠️ Failed to upload thumbnail: {e}")
            
            # ========== UPSERT PROJECT ==========
            if is_update:
                # Update existing project
                existing_project.name = name
                existing_project.prompt = prompt
                existing_project.preview_url = preview_url
                existing_project.files_url = files_url
                existing_project.thumbnail_url = thumbnail_url or existing_project.thumbnail_url
                existing_project.cloudinary_image_url = cloudinary_image_url or existing_project.cloudinary_image_url
                existing_project.timestamp = timestamp
                existing_project.project_type = project_type
                existing_project.file_count = len(files)
                existing_project.size_bytes = len(json.dumps(files))
            else:
                # Create new project
                project = Project(
                    id=project_id,
                    name=name,
                    prompt=prompt,
                    user_id=user_id,
                    preview_url=preview_url,
                    thumbnail_url=thumbnail_url,
                    files_url=files_url,
                    cloudinary_image_url=cloudinary_image_url,
                    timestamp=timestamp,
                    project_type=project_type,
                    file_count=len(files),
                    size_bytes=len(json.dumps(files)),
                    is_public=False,
                    version=1
                )
                session.add(project)
            
            await session.flush()
            
            # ========== SAVE FILE METADATA ==========
            # Delete old file records if updating
            if is_update:
                await session.execute(delete(ProjectFile).where(ProjectFile.project_id == project_id))
            
            file_saved_count = 0
            for file_path, content in files.items():
                if file_path.startswith("__") and file_path.endswith("__"):
                    continue
                if file_path == "preview_html":
                    continue
                
                file_type = None
                if '.' in file_path:
                    ext = file_path.split('.')[-1].lower()
                    file_type_map = {
                        'html': 'html', 'htm': 'html', 'css': 'css', 'scss': 'scss',
                        'js': 'javascript', 'ts': 'typescript', 'jsx': 'jsx', 'tsx': 'tsx',
                        'json': 'json', 'md': 'markdown',
                        'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 'svg': 'image'
                    }
                    file_type = file_type_map.get(ext, 'text')
                
                if isinstance(content, dict):
                    content_str = json.dumps(content, indent=2)
                elif not isinstance(content, str):
                    content_str = str(content)
                else:
                    content_str = content
                
                project_file = ProjectFile(
                    project_id=project_id,
                    file_path=file_path,
                    file_type=file_type,
                    size_bytes=len(content_str),
                    cloudinary_url=f"{files_url}/{file_path}" if files_url else None
                )
                session.add(project_file)
                file_saved_count += 1
            
            # Save hero image URL
            if cloudinary_image_url:
                hero_image_file = ProjectFile(
                    project_id=project_id,
                    file_path="__hero_image__",
                    file_type="cloudinary_image",
                    size_bytes=len(cloudinary_image_url),
                    cloudinary_url=cloudinary_image_url
                )
                session.add(hero_image_file)
                print(f"📸 Saved hero image URL to project_files: {cloudinary_image_url[:80]}...")
            else:
                print(f"⚠️ No cloudinary_image_url to save for project {project_id}")
            
            await session.commit()
            await notify_projects_updated(name)
            
            print(f"\n{'='*60}")
            print(f"✅ PROJECT {'UPDATED' if is_update else 'SAVED'} SUCCESSFULLY!")
            print(f"📁 Project ID: {project_id}")
            print(f"🏷️ Project Name: {name}")
            print(f"📸 Cloudinary Image URL: {cloudinary_image_url if cloudinary_image_url else 'NOT SAVED'}")
            print(f"📄 Preview URL: {preview_url[:60] if preview_url else 'NOT SAVED'}...")
            print(f"🖼️ Thumbnail URL: {thumbnail_url[:60] if thumbnail_url else 'NOT SAVED'}...")
            print(f"{'='*60}\n")
            
            return {
                "success": True,
                "id": project_id,
                "name": name,
                "user_email": user_email,
                "file_count": file_saved_count,
                "has_thumbnail": thumbnail_url is not None,
                "thumbnail_url": thumbnail_url,
                "preview_url": preview_url,
                "files_url": files_url,
                "cloudinary_image_url": cloudinary_image_url
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





@app.get("/api/test-all-keys")
async def test_all_keys():
    results = []
    for i, key in enumerate(smart_balancer.api_keys):
        try:
            from google import genai
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents="Say 'OK'",
                config={"max_output_tokens": 5}
            )
            results.append({"key": i+1, "status": "WORKING"})
        except Exception as e:
            results.append({"key": i+1, "status": "ERROR", "error": str(e)[:50]})
    return {"results": results}




@app.get("/api/key-stats")
async def get_key_stats():
    return model_router.get_stats()







# ========== KEEP ALIVE ENDPOINTS (For external uptime monitoring) ==========

@app.get("/api/keep-alive")
async def keep_alive():
    """Simple endpoint to keep the service awake on Render"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Service is running"
    }

@app.get("/api/ping")
async def ping():
    """Ultra-simple ping endpoint for uptime monitoring"""
    return {"pong": True, "timestamp": datetime.now().isoformat()}
























@app.api_route("/api/cron/reset-daily-credits", methods=["GET", "POST"])
async def cron_reset_daily_credits():
    """
    Cron job endpoint to reset daily credits for ALL users directly from database.
    No authentication required - meant for automated cron jobs.
    """
    try:
        print(f"\n{'='*60}")
        print(f"🕐 CRON JOB - RESETTING ALL USER CREDITS")
        print(f"   Time: {datetime.now()}")
        print(f"{'='*60}")
        
        async with AsyncSessionLocal() as session:
            today = date.today()
            
            # Get ALL users before reset (for logging)
            stmt = select(UserCredits)
            result = await session.execute(stmt)
            all_users = result.scalars().all()
            
            print(f"📊 Total users in database: {len(all_users)}")
            
            reset_count = 0
            for user_credits in all_users:
                # Log old values
                old_used = user_credits.daily_credits_used
                old_date = user_credits.daily_reset_date
                
                # Reset to 0 and update date
                user_credits.daily_credits_used = 0
                user_credits.daily_reset_date = today
                reset_count += 1
                
                print(f"  🔄 User {user_credits.user_id[:12]}...: {old_used} credits → 0 (last reset: {old_date})")
            
            # Commit all changes to database
            await session.commit()
            
            print(f"\n✅ DATABASE UPDATE COMPLETE!")
            print(f"   📊 Users reset: {reset_count}")
            print(f"   📅 New reset date: {today}")
            print(f"{'='*60}\n")
            
            return {
                "success": True,
                "message": "Daily credits reset completed for ALL users",
                "users_reset": reset_count,
                "reset_date": today.isoformat(),
                "reset_time": datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"❌ Cron reset failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}



















@app.post("/api/auth/login")
async def login(request: Request):
    """User login endpoint"""
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        db_connection_string = data.get("db_connection_string", "")  # Direct connection string
        
        if not email or not password:
            return {"success": False, "error": "Email and password required"}
        
        if not db_connection_string:
            return {"success": False, "error": "Database connection required", "requires_db": True}
        
        import asyncpg
        import hashlib
        import secrets
        
        conn = await asyncpg.connect(db_connection_string)  # Use directly
        
        try:
            user = await conn.fetchrow("""
                SELECT id, email, name, password_hash
                FROM users
                WHERE email = $1
            """, email)
            
            if not user:
                await conn.close()
                return {"success": False, "error": "Invalid credentials"}
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if password_hash != user['password_hash']:
                await conn.close()
                return {"success": False, "error": "Invalid credentials"}
            
            # Create session token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=30)
            
            await conn.execute("""
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE SET token = $2, expires_at = $3
            """, user['id'], token, expires_at)
            
            await conn.close()
            
            return {
                "success": True,
                "user": {
                    "id": str(user['id']),
                    "email": user['email'],
                    "name": user['name']
                },
                "access_token": token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            await conn.close()
            raise e
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return {"success": False, "error": str(e)}






















@app.get("/api/check-db-config")
async def check_db_config(request: Request):
    """Check if database is configured"""
    # Check session first
    db_connection = request.session.get("db_connection_string", "")
    
    # Also check for connection_id in headers
    connection_id = request.headers.get("X-Connection-ID", "")
    if not db_connection and connection_id and connection_id in db_connections:
        db_connection = db_connections[connection_id]
    
    return {"configured": bool(db_connection)}

















@app.post("/api/auth/signup")
async def signup(request: Request):
    """User registration endpoint"""
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        name = data.get("name", "")
        db_connection_string = data.get("db_connection_string", "")  # Only this now
        
        if not email or not password:
            return {"success": False, "error": "Email and password required"}
        
        # Use direct connection string
        if not db_connection_string:
            return {"success": False, "error": "Database connection required", "requires_db": True}
        
        import asyncpg
        import hashlib
        import secrets
        
        try:
            conn = await asyncpg.connect(db_connection_string)  # Use directly
            
            # Create tables if not exist
            await conn.execute("""
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                
                CREATE TABLE IF NOT EXISTS users (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255),
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS sessions (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(500) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS user_credits (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
                    credits INTEGER DEFAULT 10,
                    daily_credits_used INTEGER DEFAULT 0,
                    daily_reset_date DATE DEFAULT CURRENT_DATE,
                    monthly_credits_used INTEGER DEFAULT 0,
                    monthly_reset_date DATE DEFAULT CURRENT_DATE
                );
            """)
            
            # Check if user exists
            existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
            if existing:
                await conn.close()
                return {"success": False, "error": "User already exists"}
            
            # Hash password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Insert user
            user_id = await conn.fetchval("""
                INSERT INTO users (email, name, password_hash)
                VALUES ($1, $2, $3)
                RETURNING id
            """, email, name, password_hash)
            
            # Create session token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=30)
            
            await conn.execute("""
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES ($1, $2, $3)
            """, user_id, token, expires_at)
            
            # Create credits record
            await conn.execute("""
                INSERT INTO user_credits (user_id)
                VALUES ($1)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id)
            
            await conn.close()
            
            return {
                "success": True,
                "user": {
                    "id": str(user_id),
                    "email": email,
                    "name": name
                },
                "access_token": token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            await conn.close()
            raise e
            
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return {"success": False, "error": str(e)}


















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
