from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
import jwt
from datetime import datetime, timedelta
import os
import uvicorn
from dotenv import load_dotenv


from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select
from datetime import datetime, date
import uuid









# Load environment variables
load_dotenv()





app = FastAPI()




# Add SessionMiddleware (REQUIRED for OAuth)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "session-secret-key-change-this"))

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this")
SESSION_SECRET = os.getenv("SESSION_SECRET", "session-secret-key-change-this-too")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")










# ========== DATABASE SETUP FOR AUTH.PY ==========
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, select, text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta, date
import uuid

Base = declarative_base()

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Define User model
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

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
    print("✅ Database configured in auth.py")
    
    # Create tables if they don't exist
    async def init_auth_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Auth database tables verified")
else:
    AsyncSessionLocal = None
    print("⚠️ DATABASE_URL not found in auth.py")
















# Initialize OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# In-memory user store (replace with database later)
users_db = {}

# Store projects in memory (replace with database later)
projects_db = []


# ============ USER HELPER FUNCTIONS ============

async def check_user_exists(email: str) -> bool:
    """Check if user exists in database"""
    return email in users_db

async def get_user_by_email(email: str):
    """Get user by email"""
    return users_db.get(email)

async def create_user(user_info: dict) -> dict:
    """Create a new user"""
    email = user_info.get('email')
    user_id = str(len(users_db) + 1)
    
    user_data = {
        'user_id': user_id,
        'email': email,
        'name': user_info.get('name', ''),
        'picture': user_info.get('picture', ''),
        'created_at': datetime.utcnow().isoformat()
    }
    users_db[email] = user_data
    print(f"✅ Created new user: {email}")
    return user_data


# ============ AUTH ENDPOINTS ============

@app.get("/")
async def root():
    return {"message": "EagleCode API is running", "status": "ok"}

@app.get("/api/auth/google/signup")
async def google_signup(request: Request):
    """Initiate Google OAuth for SIGNUP only"""
    print(f"🔐 Starting Google OAuth SIGNUP")
    redirect_uri = f"{BACKEND_URL}/api/auth/google/callback?mode=signup"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/api/auth/google/signin")
async def google_signin(request: Request):
    """Initiate Google OAuth for SIGNIN only"""
    print(f"🔐 Starting Google OAuth SIGNIN")
    redirect_uri = f"{BACKEND_URL}/api/auth/google/callback?mode=signin"
    return await oauth.google.authorize_redirect(request, redirect_uri)








@app.get("/api/auth/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback"""
    try:
        mode = request.query_params.get("mode", "signup")
        print(f"📞 Mode: {mode}")
        
        # Get access token
        token = await oauth.google.authorize_access_token(request)
        print(f"✅ Got access token")
        
        # Get user info
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        google_id = user_info.get('sub', '')
        
        print(f"👤 User: {email}")
        
        # ========== CREATE OR GET USER FROM DATABASE ==========
        async with AsyncSessionLocal() as session:
            # Check if user exists
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                # Create new user
                user_id = str(uuid.uuid4())
                db_user = User(
                    id=user_id,
                    email=email,
                    username=name.replace(' ', '_').lower()[:50],
                    password_hash="oauth_google",  # Placeholder for OAuth users
                    avatar_url=picture,
                    created_at=datetime.now()
                )
                session.add(db_user)
                await session.commit()
                print(f"✅ Created new user in database: {user_id}")
                
                # ========== CREATE CREDITS RECORD FOR THE USER ==========
                today = datetime.now().date()
                # Check if credits table exists and create record
                try:
                    # First check if user_credits table exists
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS user_credits (
                            id SERIAL PRIMARY KEY,
                            user_id VARCHAR(255) NOT NULL UNIQUE,
                            plan VARCHAR(50) DEFAULT 'free',
                            daily_credits_used INT DEFAULT 0,
                            daily_reset_date DATE NOT NULL,
                            monthly_credits_used INT DEFAULT 0,
                            monthly_reset_date DATE NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    await session.commit()
                    
                    # Create credits record
                    await session.execute(text("""
                        INSERT INTO user_credits (user_id, daily_reset_date, monthly_reset_date)
                        VALUES (:user_id, :today, :today)
                        ON CONFLICT (user_id) DO NOTHING
                    """), {"user_id": user_id, "today": today})
                    await session.commit()
                    print(f"✅ Created credits record for user: {user_id}")
                except Exception as e:
                    print(f"⚠️ Credits creation error: {e}")
            else:
                user_id = db_user.id
                print(f"✅ Existing user found: {user_id}")
        
        # Create JWT token with user_id from database
        jwt_token = jwt.encode(
            {
                'user_id': user_id,  # Use database UUID, not Google's sub
                'email': email,
                'name': name,
                'picture': picture,
                'exp': datetime.utcnow() + timedelta(days=7)
            },
            SECRET_KEY,
            algorithm='HS256'
        )
        
        print(f"🎫 JWT token created for user: {user_id}")
        
        # Redirect back to frontend with token
        return RedirectResponse(url=f"{FRONTEND_URL}/oauth-callback?token={jwt_token}")
        
    except Exception as e:
        print(f"❌ OAuth error: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url=f"{FRONTEND_URL}/oauth-callback?error={str(e)}")















# ============ PROJECT ENDPOINTS ============

@app.get("/api/get-projects")
async def get_projects(request: Request, user_id: str = None, limit: int = 11):
    """Get projects for a user"""
    # Try to get user_id from token if not provided
    if not user_id:
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "")
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
            except:
                user_id = "default"
        else:
            user_id = "default"
    
    print(f"📚 Getting projects for user: {user_id}")
    
    # Filter projects by user_id
    user_projects = [p for p in projects_db if p.get('user_id') == user_id]
    
    # Remove files from response to keep it light
    light_projects = []
    for project in user_projects[:limit]:
        light_projects.append({
            'id': project.get('id'),
            'name': project.get('name'),
            'prompt': project.get('prompt', '')[:80],
            'timestamp': project.get('timestamp'),
            'preview_html': project.get('preview_html', '')
        })
    
    return {"success": True, "projects": light_projects}






@app.post("/api/save-project")
async def save_project(request: Request):
    """Save a project"""
    try:
        project_data = await request.json()
        print(f"💾 Saving project: {project_data.get('name')}")
        
        # Get user_id from token
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "")
        user_id = "default"
        
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
            except:
                pass
        
        # Add user_id to project
        project_data['user_id'] = user_id
        
        # Check if project exists
        existing_index = next((i for i, p in enumerate(projects_db) if p.get('id') == project_data.get('id') and p.get('user_id') == user_id), None)
        
        if existing_index is not None:
            projects_db[existing_index] = project_data
        else:
            projects_db.insert(0, project_data)
        
        # Keep only last 20 projects per user
        user_projects = [p for p in projects_db if p.get('user_id') == user_id]
        while len(user_projects) > 20:
            to_remove = user_projects.pop()
            projects_db.remove(to_remove)
        
        return {"success": True, "message": "Project saved", "id": project_data.get('id')}
    except Exception as e:
        print(f"❌ Error saving project: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/get-project/{project_id}")
async def get_project(project_id: str, request: Request):
    """Get a specific project"""
    # Get user_id from token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    user_id = "default"
    
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
        except:
            pass
    
    project = next((p for p in projects_db if p.get('id') == project_id and p.get('user_id') == user_id), None)
    
    if project:
        return {"success": True, "project": project, "files": project.get('files', {})}
    return {"success": False, "message": "Project not found"}

@app.delete("/api/delete-project/{project_id}")
async def delete_project(project_id: str, request: Request):
    """Delete a project"""
    global projects_db
    
    # Get user_id from token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    user_id = "default"
    
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
        except:
            pass
    
    original_count = len(projects_db)
    projects_db = [p for p in projects_db if not (p.get('id') == project_id and p.get('user_id') == user_id)]
    
    if len(projects_db) < original_count:
        return {"success": True, "message": "Project deleted"}
    return {"success": False, "message": "Project not found"}


# ============ RUN SERVER ============

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Starting EagleCode Backend Server...")
    print(f"📍 Frontend URL: {FRONTEND_URL}")
    print(f"📍 Backend URL: {BACKEND_URL}")
    print(f"🔑 Google OAuth: {'✅ Configured' if GOOGLE_CLIENT_ID else '❌ Missing'}")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)