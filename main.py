import json
import os
import re
import io
import jwt  # noqa
import asyncio
from html2image import Html2Image



from build_prompts import MASTER_BUILD_PROMPT





from pathlib import Path

from preview_generator import generate_preview_internal, clean_html_response 


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
            <h1 class="text-5xl md:text-7xl font-bold mb-4" style="color: transparent; -webkit-text-stroke: 2px #d8a219; text-stroke: 2px #d8a219;">
    {project_name}
</h1>
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
                    "max_output_tokens": 50000,
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
                            "temperature": 0.2 if stream_retry_count == 0 else 0.01,
                            "max_output_tokens": 500000,  # ⭐ Increase this
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











            try:
                clean_text = clean_json_response(full_response)

                try:
                    project_files: Dict[str, str] = json.loads(clean_text)
                    print(f"✅ JSON parsed successfully on attempt {retry_count + 1}")
                    
                    # FIX: Convert list to dict if needed
                    if isinstance(project_files, list):
                        print(f"⚠️ AI returned LIST instead of dict")
                        if project_files and isinstance(project_files[0], (list, tuple)) and len(project_files[0]) == 2:
                            project_files = dict(project_files)
                            print(f"✅ Converted list to dict")
                    
                    # WAIT FOR IMAGES
                    await websocket.send_json({
                        "type": "status",
                        "message": "⏳ Waiting for images..."
                    })
                    
                    try:
                        await asyncio.wait_for(background_image_task, timeout=15)
                        print(f"✅ Images ready: {len([k for k in image_data if image_data[k]])}/2")
                        await websocket.send_json({
                            "type": "status",
                            "message": f"✅ Images ready! Found {len([k for k in image_data if image_data[k]])}/2 images"
                        })
                    except asyncio.TimeoutError:
                        print("⚠️ Image search timeout")
                        await websocket.send_json({
                            "type": "status",
                            "message": "⚠️ Image timeout, using gradients"
                        })
                    except Exception as e:
                        print(f"⚠️ Image error: {e}")
                    
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















        # ========== ENSURE project_files IS A DICT ==========
        if isinstance(project_files, list):
                print(f"⚠️ project_files is a list after retry loop — converting...")
                converted = {}
                for item in project_files:
                        if isinstance(item, (list, tuple)) and len(item) == 2:
                                converted[item[0]] = item[1]
                        elif isinstance(item, dict):
                                converted.update(item)
                project_files = converted
                print(f"✅ Converted list to dict with {len(project_files)} entries")
        
        if not isinstance(project_files, dict):
                print(f"❌ project_files is unexpected type: {type(project_files)}")
                await websocket.send_json({
                        "type": "error",
                        "message": "Generated project has invalid format. Please try again."
                })
                return
        
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
                preview_result = await generate_preview_internal(
            project_files,
            user_prompt,
            model_router=model_router,
            get_cloudinary_url_for_preview=get_cloudinary_url_for_preview
        )
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
                            preview_result = await generate_preview_internal(
                                updated_files,
                                project_name_from_request or "Scorpio Project",
                                model_router=model_router,
                                get_cloudinary_url_for_preview=get_cloudinary_url_for_preview
                            )
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
                            config={"temperature": 0.1, "max_output_tokens": 150000}
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
                
                preview_result = await generate_preview_internal(
                    updated_files,
                    project_name,
                    model_router=model_router,
                    get_cloudinary_url_for_preview=get_cloudinary_url_for_preview
                )
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
                    config={"temperature": 0.01, "max_output_tokens": 150000}
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
                    existing_image_url=original_cloudinary_image_url,
                    model_router=model_router,
                    get_cloudinary_url_for_preview=get_cloudinary_url_for_preview
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
                "max_output_tokens": 150000,
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
                config={"temperature": 0.2, "max_output_tokens": 150000}
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
            config={"temperature": 0.3, "max_output_tokens": 150000}
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
                        "max_output_tokens": 150000,
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
