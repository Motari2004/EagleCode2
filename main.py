import json
import os
import re
import io
import asyncio

# Then import and initialize auth router
from routes.auth import router as auth_router, init_oauth

from starlette.middleware.sessions import SessionMiddleware

from typing import Dict, Any, List, Set
# Add these with your other imports
import cloudinary
import cloudinary.uploader
from contextlib import asynccontextmanager

from sqlalchemy import Date  # ← Add this import


from datetime import datetime, date

# Add these imports at the top if not already there

import uuid


from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, Index, select, desc, func, delete, text






import uvicorn
from fastapi import FastAPI, WebSocket, HTTPException, Request
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

class GeminiModelRouter:
    def __init__(self, client):
        self.client = client
        # Priority order - try models with highest quotas first
        self.model_order = [
            AVAILABLE_MODELS["flash_25"],            # Gemini 2.5 Flash
            AVAILABLE_MODELS["flash_lite_25"],       # Gemini 2.5 Flash Lite
            AVAILABLE_MODELS["flash_lite_latest"],   # Highest quota (free tier)
            AVAILABLE_MODELS["flash_latest"],        # Latest flash
        ]
    
    async def generate_stream(self, prompt: str, config: dict):
        """Stream generation with automatic fallback"""
        last_error = None
        
        for model in self.model_order:
            try:
                print(f"📡 Trying model: {model}")
                
                response = self.client.models.generate_content_stream(
                    model=model,
                    contents=prompt,
                    config=config
                )
                
                # Test first chunk
                first_chunk = None
                for chunk in response:  # Use regular for loop
                    if first_chunk is None:
                        first_chunk = chunk
                        print(f"✅ Model {model} working")
                    yield chunk
                
                if first_chunk:
                    model_usage[model]["success"] += 1
                    return
                    
            except Exception as e:
                error_msg = str(e)
                
                # Handle rate limit (429)
                if "429" in error_msg:
                    print(f"⚠️ Model {model} rate limited (quota exceeded)")
                elif "404" in error_msg:
                    print(f"⚠️ Model {model} not found, skipping")
                else:
                    print(f"⚠️ Model {model} failed: {error_msg[:100]}")
                
                model_usage[model]["fail"] += 1
                model_usage[model]["last_fail"] = error_msg
                last_error = e
                continue
        
        raise Exception(f"All models failed. Last error: {last_error}")
    
    async def generate_content(self, prompt: str, config: dict):
        """Non-streaming generation with fallback"""
        last_error = None
        
        for model in self.model_order:
            try:
                print(f"🤖 Trying model: {model}")
                
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                )
                
                model_usage[model]["success"] += 1
                print(f"✅ Model {model} succeeded")
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                
                if "429" in error_msg:
                    print(f"⚠️ Model {model} rate limited (quota exceeded)")
                elif "404" in error_msg:
                    print(f"⚠️ Model {model} not found, skipping")
                else:
                    print(f"⚠️ Model {model} failed: {error_msg[:100]}")
                
                model_usage[model]["fail"] += 1
                model_usage[model]["last_fail"] = error_msg
                last_error = e
                continue
        
        raise Exception(f"All models failed. Last error: {last_error}")
    
    def get_stats(self):
        """Get model usage statistics"""
        return model_usage
    






    async def generate_stream(self, prompt: str, config: dict):
        """Stream generation with automatic fallback"""
        last_error = None
        
        for model in self.model_order:
            try:
                print(f"📡 Trying model: {model}")
                
                response = self.client.models.generate_content_stream(
                    model=model,
                    contents=prompt,
                    config=config
                )
                
                # Test first chunk - use regular for loop, NOT async for
                first_chunk = None
                for chunk in response:  # Changed from async for to for
                    if first_chunk is None:
                        first_chunk = chunk
                        print(f"✅ Model {model} working")
                    yield chunk
                
                if first_chunk:
                    model_usage[model]["success"] += 1
                    return
                    
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Model {model} failed: {error_msg[:100]}")
                model_usage[model]["fail"] += 1
                model_usage[model]["last_fail"] = error_msg
                last_error = e
                continue
        
        raise Exception(f"All models failed. Last error: {last_error}")
    
    async def generate_content(self, prompt: str, config: dict):
        """Non-streaming generation with fallback"""
        last_error = None
        
        for model in self.model_order:
            try:
                print(f"🤖 Trying model: {model}")
                
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                )
                
                model_usage[model]["success"] += 1
                print(f"✅ Model {model} succeeded")
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Model {model} failed: {error_msg[:100]}")
                model_usage[model]["fail"] += 1
                model_usage[model]["last_fail"] = error_msg
                last_error = e
                continue
        
        raise Exception(f"All models failed. Last error: {last_error}")
    
    def get_stats(self):
        """Get model usage statistics"""
        return model_usage










load_dotenv()





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









DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    # Remove all query parameters (anything after ?)
    clean_url = DATABASE_URL.split('?')[0]
    
    # Also remove any trailing parameters
    clean_url = clean_url.rstrip('/')
    
    print(f"🔗 Connecting to Neon database...")
    print(f"   Clean URL: {clean_url[:50]}...")
    
    # Convert to asyncpg format
    ASYNC_DATABASE_URL = clean_url.replace("postgresql://", "postgresql+asyncpg://")
    
    try:
        engine = create_async_engine(
            ASYNC_DATABASE_URL, 
            echo=False,
            pool_pre_ping=True,
            connect_args={
                "ssl": True,  # Neon requires SSL
                "server_settings": {
                    "application_name": "scorpio_backend",
                }
            }
        )
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        Base = declarative_base()
        
        # ========== DEFINE ALL TABLES ==========
        
        # Projects table (metadata only)
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
        
        # Project Files table (stores individual files separately)
        class ProjectFile(Base):
            __tablename__ = "project_files"
            id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
            project_id = Column(String, nullable=False, index=True)
            file_path = Column(String, nullable=False)
            content = Column(Text, nullable=False)  # File content as TEXT
            file_type = Column(String, nullable=True)  # html, css, js, tsx, json, etc.
            size_bytes = Column(Integer, default=0)
            created_at = Column(DateTime, nullable=False, default=datetime.now)
            updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
            
            __table_args__ = (
                # Composite index for faster lookups by project and file path
                Index('idx_project_file_path', 'project_id', 'file_path', unique=True),
            )
        
        # Users table (for future authentication)
        class User(Base):
            __tablename__ = "users"
            id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
            email = Column(String, unique=True, nullable=False)
            username = Column(String, unique=True, nullable=False)
            password_hash = Column(String, nullable=False)
            avatar_url = Column(String, nullable=True)
            created_at = Column(DateTime, nullable=False, default=datetime.now)
            updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
        
        # Sessions table (for login sessions)
        class Session(Base):
            __tablename__ = "sessions"
            id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
            user_id = Column(String, nullable=False, index=True)
            token = Column(String, unique=True, nullable=False, index=True)
            expires_at = Column(DateTime, nullable=False)
            created_at = Column(DateTime, nullable=False, default=datetime.now)
            ip_address = Column(String, nullable=True)
            user_agent = Column(String, nullable=True)
        
        # API Keys table (for external access)
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
        







        class UserCredits(Base):
            __tablename__ = "user_credits"
            id = Column(Integer, primary_key=True, autoincrement=True)
            user_id = Column(String, nullable=False, unique=True, index=True)
            plan = Column(String, default="free")
            daily_credits_used = Column(Integer, default=0)
            daily_reset_date = Column(Date, nullable=False)
            monthly_credits_used = Column(Integer, default=0)
            monthly_reset_date = Column(Date, nullable=False)
            created_at = Column(DateTime, default=datetime.now)
            updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)










        
        # Templates table (for saved templates)
        class Template(Base):
            __tablename__ = "templates"
            id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
            name = Column(String, nullable=False)
            description = Column(Text, nullable=True)
            category = Column(String, nullable=False, index=True)
            files = Column(Text, nullable=False)  # JSON string of template files
            preview_html = Column(Text, nullable=True)
            icon = Column(String, nullable=True)
            created_at = Column(DateTime, nullable=False, default=datetime.now)
            user_id = Column(String, default="default")
            usage_count = Column(Integer, default=0)
        
        async def init_db():
            try:
                async with engine.begin() as conn:
                    # ONLY create tables if they don't exist - NO DROPPING
                    await conn.run_sync(Base.metadata.create_all)
                    print("✅ All tables verified/created successfully!")
                    




# Skip verbose table logging for faster startup
# result = await conn.execute(...) etc.




                    # List all tables
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
                    else:
                        print("\n📚 No tables found, they will be created as needed")
                        
            except Exception as e:
                print(f"❌ Database initialization error: {e}")
                raise
        
        print("✅ Neon database configured successfully")
        
    except Exception as e:
        print(f"❌ Failed to configure Neon: {e}")
        engine = None
        AsyncSessionLocal = None
        Base = None
        Project = None
        ProjectFile = None
        User = None
        Session = None
        ApiKey = None
        Template = None
        async def init_db():
            print("⚠️ Database not available")
else:
    print("⚠️ DATABASE_URL not found in environment")
    engine = None
    AsyncSessionLocal = None
    Base = None
    Project = None
    ProjectFile = None
    User = None
    Session = None
    ApiKey = None
    Template = None
    async def init_db():
        print("⚠️ Database not configured")









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



















# Initialize Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Initialize the router AFTER client is created
model_router = GeminiModelRouter(client)








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
        "https://eaglecode2.onrender.com",          # Your backend itself
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)







# Image cache for storing downloaded images to avoid duplicate downloads
IMAGE_CACHE = {}




async def search_free_images(query: str, count: int = 3) -> List[Dict]:
    """
    Search for free-to-use images using Pexels API (primary) with fallback to web scraping
    Returns a list of image URLs with attribution information
    """
    # Try Pexels API first
    api_key = os.environ.get("PEXELS_API_KEY")
    if api_key:
        try:
            headers = {"Authorization": api_key}
            params = {"query": query, "per_page": count, "page": 1}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.pexels.com/v1/search",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for photo in data.get("photos", []):
                        # Use large2x image for high quality
                        img_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large")
                        
                        results.append({
                            "url": img_url,
                            "source": "Pexels",
                            "attribution": f"Photo by {photo.get('photographer', 'Unknown')} on Pexels",
                            "license": "Free to use under Pexels License",
                            "photographer_url": photo.get("photographer_url"),
                            "alt": photo.get("alt", query)
                        })
                    
                    if results:
                        print(f"✅ Found {len(results)} images via Pexels API for '{query}'")
                        return results[:count]
                        
        except Exception as e:
            print(f"⚠️ Pexels API error: {e}, falling back to web scraping")
    
    # Fallback to web scraping if API fails or no API key
    print(f"🔍 Falling back to web scraping for '{query}'")
    return await search_free_images_fallback(query, count)

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
    """Generate fully interactive HTML preview using AI after Next.js files are created"""
    try:
        print(f"🤖 AI generating full equivalent HTML preview for: {project_name}")

        # ========== COLLECT KEY FILES FOR AI ==========
        nav_content = files.get("components/Navigation.tsx", "")
        if not nav_content:
            for fp, content in files.items():
                if "Navigation" in fp and fp.endswith((".tsx", ".jsx")):
                    nav_content = content
                    break

        # Extract brand and links
        brand_name = project_name
        nav_links = []
        if nav_content:
            brand_match = re.search(r'bg-gradient-to-r[^>]*>([^<]+)</', nav_content) or \
                          re.search(r'<Link[^>]*href="/"[^>]*>.*?<[^>]+>([^<]+)</', nav_content, re.DOTALL)
            if brand_match:
                brand_name = brand_match.group(1).strip()

            link_pattern = r'<Link\s+href="([^"]+)"[^>]*>([^<]+)</Link>'
            matches = re.findall(link_pattern, nav_content)
            for href, text in matches:
                text = text.strip()
                if href != "/" and text and len(text) < 50 and text != brand_name:
                    if (href, text) not in nav_links:
                        nav_links.append((href, text))

        # Prepare pages for AI
        page_contents = {}
        for file_path, content in files.items():
            if file_path.endswith(("page.tsx", "page.jsx")):
                route = file_path.replace("app/", "").replace("/page.tsx", "").replace("/page.jsx", "").strip("/")
                route_name = route if route else "home"
                # Clean for AI
                clean = re.sub(r'import .*?from .*?;', '', content, flags=re.DOTALL)
                clean = re.sub(r'export default function .*?\{', '', clean)
                page_contents[route_name] = clean[:3500]  # Limit size

        # Global CSS
        global_css = files.get("app/globals.css", "")[:2500]

        # Build AI prompt
        prompt = f"""You are an expert frontend developer. Create a **complete, beautiful, fully interactive standalone HTML preview** that is equivalent to this Next.js 14 project.

Project Name: {brand_name}

Navigation:
Brand: {brand_name}
Links: {json.dumps(nav_links)}

Pages:
{json.dumps(page_contents, indent=2)}

Global CSS (use these styles):
{global_css}

CRITICAL INSTRUCTIONS:
- Output ONLY a complete single HTML file starting with <!DOCTYPE html>
- Use Tailwind CSS via CDN and Inter font
- Dark premium theme with purple-pink gradients
- Sticky navigation bar with brand on left and all links
- Mobile hamburger menu
- Multiple page sections (one per nav link) with ids like page_home, page_about
- Home page active by default
- Use actual content from the pages above (headings, text, buttons, cards)
- Make all buttons interactive with click feedback
- Smooth page switching via JavaScript
- Replace any /images/... paths with base64 if available (see below)
- Beautiful animations, glassmorphism, hover effects

Available Images (use as src or background):
{ [f for f in files.keys() if f.startswith("public/images/")] }

Return ONLY the full HTML. No explanations."""

        # Generate with AI
        response_text = await model_router.generate_content(
            prompt=prompt,
            config={
                "temperature": 0.12,
                "max_output_tokens": 48000,
            }
        )

        preview_html = clean_html_response(response_text)

        # Ensure proper structure
        if not preview_html.lower().startswith("<!doctype"):
            preview_html = "<!DOCTYPE html>\n" + preview_html

        # ========== INJECT BASE64 IMAGES ==========
        for file_key, content in files.items():
            if not file_key.startswith("public/images/") or not isinstance(content, str):
                continue
            if not content.startswith("__binary_base64__"):
                continue
            public_path = "/" + file_key[len("public/"):]
            raw_b64 = content[len("__binary_base64__"):]
            data_uri = f"data:image/jpeg;base64,{raw_b64}"

            preview_html = preview_html.replace(f'src="{public_path}"', f'src="{data_uri}"')
            preview_html = preview_html.replace(f"src='{public_path}'", f'src="{data_uri}"')
            preview_html = preview_html.replace(public_path, data_uri)

        print(f"✅ AI full preview generated! Length: {len(preview_html):,} chars")
        return {"success": True, "preview_html": preview_html, "preview_type": "ai_full"}

    except Exception as e:
        print(f"❌ AI Preview Error: {e}")
        import traceback
        traceback.print_exc()

        # Fallback to old rule-based preview if AI fails
        print("Falling back to rule-based preview...")
        # You can keep your original rule-based code here as fallback
        # For now, returning a simple fallback
        fallback = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-white min-h-screen flex items-center justify-center">
    <div class="text-center">
        <h1 class="text-5xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            {project_name}
        </h1>
        <p class="mt-6 text-gray-400">Interactive preview generated successfully.</p>
    </div>
</body>
</html>"""
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
- The home page should ONLY have the title text, not a duplicate icon
- Only modify the specific files needed for the request
- Every website to be generated should have brand icon in the Navigation.tsx and a clean, bold title on the home page (app/page.tsx)









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



















================================================================================
CRITICAL STYLING RULES - MUST FOLLOW:
================================================================================

1. **GRADIENTS (USE THESE EXACTLY)**:
   - Button / CTA Gradient: `bg-gradient-to-r from-purple-600 via-fuchsia-600 to-pink-600 hover:from-purple-700 hover:via-fuchsia-700 hover:to-pink-700`
   - Text / Heading Gradient: `bg-gradient-to-r from-purple-400 via-pink-400 to-violet-400 bg-clip-text text-transparent animate-gradient`
   - Hero / Section Background: `bg-gradient-to-br from-purple-950/40 via-zinc-950 to-pink-950/30`
   - Subtle Accent Gradient: `bg-gradient-to-r from-purple-500/10 via-transparent to-pink-500/10`
   - Border Gradient (Hover): `border border-transparent bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-border`

2. **CONTAINERS**:
   - Standard: `container mx-auto px-4 sm:px-6 lg:px-8`
   - Wide / Full-width: `max-w-7xl mx-auto`

3. **RESPONSIVE DESIGN**:
   - Mobile-first: `text-sm md:text-base lg:text-lg`
   - Grid system: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8`

4. **BACKGROUND RULE**:
   - NO WHITE BACKGROUNDS — All backgrounds must use elegant dark tones with rich purple-pink gradient depth for a premium, modern look.

================================================================================








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
PREMIUM GRADIENT PATTERNS - USE THESE:
================================================================================

1. **Primary Gradient** (Buttons, CTAs):
   `bg-gradient-to-r from-purple-600 via-fuchsia-600 to-pink-600 hover:from-purple-700 hover:via-fuchsia-700 hover:to-pink-700 transition-all duration-300`

2. **Secondary Gradient** (Cards, Sections):
   `bg-gradient-to-br from-purple-950/40 via-transparent to-pink-950/30`

3. **Text Gradient** (Headings):
   `bg-gradient-to-r from-purple-400 via-pink-400 to-violet-400 bg-clip-text text-transparent animate-gradient`

4. **Border Gradient** (Cards on hover):
   `border border-transparent bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-border`

5. **Background Gradient** (Hero & Section backgrounds):
   `bg-gradient-to-br from-purple-950/40 via-zinc-950 to-pink-950/30`

6. **Animated Gradient** (Shimmer / Dynamic effects):
   `bg-gradient-to-r from-purple-500 via-pink-500 to-purple-500 bg-[length:200%_auto] animate-gradient`

   




================================================================================
COMPLETE GLOBALS.CSS TEMPLATE - COPY EXACTLY:
================================================================================

"app/globals.css": "@tailwind base;\\n@tailwind components;\\n@tailwind utilities;\\n\\n@layer base {\\n  :root {\\n    --background: 0 0% 100%;\\n    --foreground: 222.2 84% 4.9%;\\n    --card: 0 0% 100%;\\n    --card-foreground: 222.2 84% 4.9%;\\n    --border: 214.3 31.8% 91.4%;\\n    --ring: 222.2 84% 4.9%;\\n  }\\n\\n  .dark {\\n    --background: 222.2 84% 4.9%;\\n    --foreground: 210 40% 98%;\\n    --card: 222.2 84% 4.9%;\\n    --card-foreground: 210 40% 98%;\\n    --border: 217.2 32.6% 17.5%;\\n    --ring: 212.7 26.8% 83.9%;\\n  }\\n\\n  * {\\n    border-color: hsl(var(--border));\\n  }\\n\\n  body {\\n    @apply bg-zinc-950 text-white antialiased;\\n    font-feature-settings: \\\"rlig\\\" 1, \\\"calt\\\" 1;\\n  }\\n}\\n\\n@layer utilities {\\n  html {\\n    scroll-behavior: smooth;\\n  }\\n\\n  ::-webkit-scrollbar {\\n    width: 10px;\\n    height: 10px;\\n  }\\n\\n  ::-webkit-scrollbar-track {\\n    background: #18181b;\\n    border-radius: 5px;\\n  }\\n\\n  ::-webkit-scrollbar-thumb {\\n    background: linear-gradient(to bottom, #a855f7, #ec4899);\\n    border-radius: 5px;\\n  }\\n\\n  ::-webkit-scrollbar-thumb:hover {\\n    background: linear-gradient(to bottom, #c084fc, #f472b6);\\n  }\\n\\n  ::selection {\\n    @apply bg-purple-500 text-white;\\n  }\\n\\n  *:focus-visible {\\n    @apply outline-none ring-2 ring-purple-500 ring-offset-2 ring-offset-zinc-950;\\n  }\\n}\\n\\n@layer components {\\n  .glass {\\n    @apply bg-white/5 backdrop-blur-md border border-white/10;\\n  }\\n\\n  .glass-hover {\\n    @apply transition-all duration-300 hover:bg-white/10 hover:border-white/20;\\n  }\\n\\n  .gradient-text {\\n    @apply bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent;\\n    background-size: 200% auto;\\n    animation: shimmer 3s ease infinite;\\n  }\\n\\n  .card-hover {\\n    @apply transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl hover:shadow-purple-500/20;\\n  }\\n\\n  .glow {\\n    @apply shadow-lg shadow-purple-500/25;\\n  }\\n\\n  .glow-hover {\\n    @apply transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/40;\\n  }\\n\\n  .hero-gradient {\\n    background: radial-gradient(ellipse at top, #1e1b4b, transparent),\\n                radial-gradient(ellipse at bottom, #4c1d95, transparent);\\n  }\\n\\n  .grid-pattern {\\n    background-image: linear-gradient(to right, #ffffff0a 1px, transparent 1px),\\n                      linear-gradient(to bottom, #ffffff0a 1px, transparent 1px);\\n    background-size: 50px 50px;\\n  }\\n}\\n\\n@keyframes shimmer {\\n  0% { background-position: 0% 50%; }\\n  50% { background-position: 100% 50%; }\\n  100% { background-position: 0% 50%; }\\n}\\n\\n@keyframes float {\\n  0%, 100% { transform: translateY(0px); }\\n  50% { transform: translateY(-20px); }\\n}\\n\\n@keyframes pulse-slow {\\n  0%, 100% { opacity: 0.5; }\\n  50% { opacity: 1; }\\n}\\n\\n@keyframes gradient {\\n  0% { background-position: 0% 50%; }\\n  50% { background-position: 100% 50%; }\\n  100% { background-position: 0% 50%; }\\n}\\n\\n.animate-float {\\n  animation: float 6s ease-in-out infinite;\\n}\\n\\n.animate-pulse-slow {\\n  animation: pulse-slow 3s ease-in-out infinite;\\n}\\n\\n.animate-gradient {\\n  background-size: 200% auto;\\n  animation: gradient 3s ease infinite;\\n}"










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
  page.tsx                  # Dynamic home page (USE RELATIVE IMPORTS)
  globals.css               # Premium styles with animations
  loading.tsx               # Loading skeleton
  error.tsx                 # Error boundary (with "use client")
  not-found.tsx             # 404 page
  [ALL_NAVIGATION_PAGES]/   # CREATE PAGE FOR EVERY NAVIGATION LINK

components/
  Navigation.tsx            # Dynamic navigation with creative labels
  ui/
    Button.tsx              # Reusable button component

lib/
  utils.ts                  # cn utility function






  
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













        for i, term in enumerate(search_terms[:3]):
            try:
                images = await search_free_images(term, 1)
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
                        await websocket.send_json({
                            "type": "status",
                            "message": f"✅ Found image for '{term}'"
                        })
                    else:
                        image_data[f"image_{i+1}"] = ""
                        image_metadata[f"image_{i+1}"] = {
                            "term": term, "source": "placeholder",
                            "attribution": "", "license": ""
                        }
                else:
                    image_data[f"image_{i+1}"] = ""
                    image_metadata[f"image_{i+1}"] = {
                        "term": term, "source": "placeholder",
                        "attribution": "", "license": ""
                    }
            except Exception as e:
                print(f"Error searching images for {term}: {e}")
                image_data[f"image_{i+1}"] = ""
                image_metadata[f"image_{i+1}"] = {
                    "term": term, "source": "placeholder",
                    "attribution": "", "license": ""
                }

        # ========== RETRY LOOP ==========
        while retry_count < max_retries:
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

                image_lines = []
                for key, meta in image_metadata.items():
                    image_lines.append(
                        f"  - {key} → src=\"/images/{key}.jpg\"  (subject: {meta['term']})"
                    )
                image_list_str = "\n".join(image_lines)

                if _is_hotel:
                    hero_hint = """\
FOR THIS HOTEL/RESORT SITE — use image_1.jpg as a FULL-PAGE hero background:

  <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
    <img src="/images/image_1.jpg" alt="Hero background" className="absolute inset-0 w-full h-full object-cover" />
    <div className="absolute inset-0 bg-black/55" />
    <div className="relative z-10 text-center text-white px-6">{/* hero content */}</div>
  </section>

Use image_2.jpg and image_3.jpg in a Rooms / Gallery section as card thumbnails."""
                elif _is_coffee:
                    hero_hint = """\
FOR THIS COFFEE SITE — use image_1.jpg as a moody full-width hero:

  <section className="relative h-[90vh] flex items-center overflow-hidden">
    <img src="/images/image_1.jpg" alt="Coffee hero" className="absolute inset-0 w-full h-full object-cover" />
    <div className="absolute inset-0 bg-black/60" />
    <div className="relative z-10 px-8">{/* headline + CTA */}</div>
  </section>

Use image_2.jpg / image_3.jpg as product or process photos in content sections."""
                elif _is_school:
                    hero_hint = """\
FOR THIS SCHOOL SITE — use image_1.jpg as a bright campus hero:

  <section className="relative h-[80vh] flex items-center overflow-hidden">
    <img src="/images/image_1.jpg" alt="Campus hero" className="absolute inset-0 w-full h-full object-cover" />
    <div className="absolute inset-0 bg-indigo-900/50" />
    <div className="relative z-10 container mx-auto px-6">{/* headline + apply button */}</div>
  </section>

Use image_2.jpg / image_3.jpg in the About or Programs section."""
                elif _is_gym:
                    hero_hint = """\
FOR THIS GYM/FITNESS SITE — use image_1.jpg as an energetic full-bleed hero:

  <section className="relative min-h-screen flex items-end overflow-hidden">
    <img src="/images/image_1.jpg" alt="Gym hero" className="absolute inset-0 w-full h-full object-cover" />
    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />
    <div className="relative z-10 container mx-auto px-6 pb-20">{/* headline + join button */}</div>
  </section>

Use image_2.jpg / image_3.jpg in the Classes or Trainers section."""
                elif _is_restaurant:
                    hero_hint = """\
FOR THIS RESTAURANT SITE — use image_1.jpg as a full-screen food/ambiance hero:

  <section className="relative h-screen flex items-center justify-center overflow-hidden">
    <img src="/images/image_1.jpg" alt="Restaurant hero" className="absolute inset-0 w-full h-full object-cover" />
    <div className="absolute inset-0 bg-black/50" />
    <div className="relative z-10 text-center text-white px-6">{/* name + reserve button */}</div>
  </section>

Use image_2.jpg / image_3.jpg in the Menu or Gallery section."""
                elif _is_ecommerce:
                    hero_hint = """\
FOR THIS STORE SITE — use image_1.jpg as a lifestyle hero banner:

  <section className="relative h-[70vh] flex items-center overflow-hidden rounded-2xl mx-4 mt-4">
    <img src="/images/image_1.jpg" alt="Store hero" className="absolute inset-0 w-full h-full object-cover" />
    <div className="absolute inset-0 bg-black/40" />
    <div className="relative z-10 px-10">{/* tagline + shop now button */}</div>
  </section>

Use image_2.jpg / image_3.jpg as product card thumbnails in the catalog."""
                else:
                    hero_hint = """\
Use image_1.jpg as a full-width hero background with a dark overlay.
Use image_2.jpg / image_3.jpg in content / gallery sections."""

                image_instructions = f"""
================================================================================
IMAGE ASSETS — DOWNLOADED TO /public/images/ — USE THEM IN YOUR CODE
================================================================================

The following real photos are already saved in the Next.js public folder.
Reference them DIRECTLY with their public path — NO import, NO base64.

Available images:
{image_list_str}

HOW TO USE (copy these patterns exactly):

{hero_hint}

GENERAL RULES:
1. NEVER use placeholder colors or gradients where a real image is available.
2. ALWAYS use the exact src path shown above (e.g. src="/images/image_1.jpg").
3. Add className="object-cover w-full h-full" to every background image.
4. Add a semi-transparent overlay div (bg-black/40 to bg-black/60) over every
   full-bleed hero image so text stays readable.
5. Use Next.js <Image> component OR plain <img> — both work with /public paths.
6. Show at least ONE image on the home page hero and at least one more
   in a secondary section (gallery, rooms, products, about, etc.).

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
                    break
                except json.JSONDecodeError as e1:
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
                await websocket.send_json({
                    "type": "preview",
                    "html": preview_result.get("preview_html"),
                    "preview_type": "dynamic"
                })
                print("✅ Preview generated and sent")
            else:
                print(f"⚠️ Preview generation failed: {preview_result.get('error')}")
        except Exception as preview_error:
            print(f"⚠️ Preview error: {preview_error}")
            fallback_html = f"""<!DOCTYPE html>
<html><head><title>Preview</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-zinc-950 text-white">
<div class="container mx-auto px-4 py-20 text-center">
<h1 class="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">{user_prompt or 'Project'}</h1>
<p class="text-gray-400 mt-4">✨ Project generated successfully!</p>
</div></body></html>"""
            await websocket.send_json({
                "type": "preview",
                "html": fallback_html,
                "preview_type": "fallback"
            })

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
                {''.join([f'<button onclick="showPage(\'{path}\')" class="block w-full text-left px-4 py-2 rounded-lg hover:bg-white/10 text-gray-300 hover:text-white">{label}</button>' for path, label in nav_links])}
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























@app.post("/api/save-project")
async def save_project(request: Dict[str, Any]):
    try:
        name = request.get("name", "")
        prompt = request.get("prompt", "")
        files = request.get("files", {})
        preview_html = request.get("preview_html", "")
        user_id = request.get("user_id", "default")
        
        print(f"💾 Saving project: {name}")
        print(f"   Files count: {len(files)}")
        
        # Handle timestamp safely
        timestamp_raw = request.get("timestamp")
        if timestamp_raw and isinstance(timestamp_raw, str):
            # Parse ISO format string
            from datetime import datetime
            # Remove timezone info if present
            if '+' in timestamp_raw or timestamp_raw.endswith('Z'):
                timestamp_raw = timestamp_raw.replace('Z', '').split('+')[0]
            timestamp = datetime.fromisoformat(timestamp_raw)
        else:
            # Use current time
            timestamp = datetime.now()
        
        print(f"   Timestamp: {timestamp}")
        
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
        
        async with AsyncSessionLocal() as session:
            # Create project metadata
            project = Project(
                name=name,
                prompt=prompt,
                preview_html=preview_html,
                timestamp=timestamp,
                user_id=user_id,
                project_type=project_type,
                file_count=len(files),
                size_bytes=len(json.dumps(files)),
                is_public=False,
                version=1
            )
            session.add(project)
            await session.flush()  # Get the project ID without committing yet
            
            # Save each file separately
            file_saved_count = 0
            for file_path, content in files.items():
                # Skip preview_html as it's stored separately
                if file_path == "preview_html":
                    continue
                
                # Determine file type from extension
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
                
                # Convert content to string if needed
                if isinstance(content, dict):
                    content = json.dumps(content, indent=2)
                elif not isinstance(content, str):
                    content = str(content)
                
                # Skip very large binary content (images)
                if file_type == 'image' and len(content) > 100000:
                    print(f"   ⚠️ Skipping large image: {file_path} ({len(content)} bytes)")
                    continue
                
                project_file = ProjectFile(
                    project_id=project.id,
                    file_path=file_path,
                    content=content[:1000000],  # Limit to 1MB per file
                    file_type=file_type,
                    size_bytes=len(content)
                )
                session.add(project_file)
                file_saved_count += 1
            
            await session.commit()
            await session.refresh(project)
            
            print(f"✅ Saved project: {name} with ID: {project.id}")
            print(f"   Files saved: {file_saved_count}/{len(files)}")
            
            return {
                "success": True, 
                "id": project.id, 
                "name": name,
                "file_count": file_saved_count,
                "message": "Project saved successfully"
            }
            
    except Exception as e:
        print(f"❌ Save failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))






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
            
            # Get all files for this project
            stmt = select(ProjectFile).where(ProjectFile.project_id == project_id)
            result = await session.execute(stmt)
            files = result.scalars().all()
            
            # Reconstruct files dictionary
            files_dict = {}
            for file in files:
                files_dict[file.file_path] = file.content
            
            # Add preview_html if it exists
            if project.preview_html:
                files_dict["preview_html"] = project.preview_html
            
            return {
                "success": True,
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "prompt": project.prompt,
                    "preview_html": project.preview_html,
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












@app.get("/api/get-projects")
async def get_projects(user_id: str = "default", limit: int = 50, offset: int = 0):
    try:
        async with AsyncSessionLocal() as session:
            # Get total count for pagination
            count_stmt = select(func.count()).select_from(Project).where(Project.user_id == user_id)
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar() or 0
            
            # Get paginated projects with offset
            stmt = select(Project).where(Project.user_id == user_id).order_by(desc(Project.timestamp)).offset(offset).limit(limit)
            result = await session.execute(stmt)
            projects = result.scalars().all()
            
            project_list = []
            for p in projects:
                project_list.append({
                    "id": p.id,
                    "name": p.name,
                    "prompt": p.prompt[:150] + "..." if len(p.prompt) > 150 else p.prompt,
                    "preview_html": "",
                    "timestamp": p.timestamp.isoformat(),
                    "project_type": p.project_type,
                    "file_count": p.file_count,
                })
            
            has_more = (offset + len(project_list)) < total_count
            
            print(f"📚 Loaded {len(project_list)} projects (offset={offset}, total={total_count}, has_more={has_more})")
            
            return {
                "success": True,
                "projects": project_list,
                "count": len(project_list),
                "total": total_count,
                "has_more": has_more
            }
            
    except Exception as e:
        print(f"❌ Load failed: {e}")
        # Return empty list instead of throwing error to prevent frontend crashes
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
    uvicorn.run(
        "main:app",  # ✅ Change from 'app' to 'main:app' (string format)
        host="0.0.0.0",
        port=8000,
        reload=True  # ✅ This enables auto-reload
    )