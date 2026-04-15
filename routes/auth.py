from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import jwt
from datetime import datetime, timedelta
import os
import uuid
from sqlalchemy import select, text
from datetime import date
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Initialize OAuth (this needs to be done AFTER app is created)
# We'll create a function to initialize it
oauth = None

def init_oauth(app):
    global oauth
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
    return oauth

@router.get("/google/signup")
async def google_signup(request: Request):
    """Initiate Google OAuth for SIGNUP only"""
    global oauth
    if oauth is None:
        raise HTTPException(status_code=500, detail="OAuth not initialized")
    
    print(f"🔐 Starting Google OAuth SIGNUP")
    redirect_uri = f"{BACKEND_URL}/api/auth/google/callback?mode=signup"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/signin")
async def google_signin(request: Request):
    """Initiate Google OAuth for SIGNIN only"""
    global oauth
    if oauth is None:
        raise HTTPException(status_code=500, detail="OAuth not initialized")
    
    print(f"🔐 Starting Google OAuth SIGNIN")
    redirect_uri = f"{BACKEND_URL}/api/auth/google/callback?mode=signin"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback"""
    global oauth
    if oauth is None:
        raise HTTPException(status_code=500, detail="OAuth not initialized")
    
    try:
        mode = request.query_params.get("mode", "signup")
        print(f"📞 Mode: {mode}")
        
        token = await oauth.google.authorize_access_token(request)
        print(f"✅ Got access token")
        
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        
        print(f"👤 User: {email}")
        
        # Import your database session and models
        from main import AsyncSessionLocal
        from models import User, UserCredits  # You'll need to create models.py
        
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                user_id = str(uuid.uuid4())
                db_user = User(
                    id=user_id,
                    email=email,
                    username=name.replace(' ', '_').lower()[:50],
                    password_hash="oauth_google",
                    avatar_url=picture,
                    created_at=datetime.now()
                )
                session.add(db_user)
                await session.commit()
                print(f"✅ Created new user in database: {user_id}")
                
                today = datetime.now().date()
                try:
                    user_credits = UserCredits(
                        user_id=user_id,
                        daily_reset_date=today,
                        monthly_reset_date=today
                    )
                    session.add(user_credits)
                    await session.commit()
                    print(f"✅ Created credits record for user: {user_id}")
                except Exception as e:
                    print(f"⚠️ Credits creation error: {e}")
            else:
                user_id = db_user.id
                print(f"✅ Existing user found: {user_id}")
        
        jwt_token = jwt.encode(
            {
                'user_id': user_id,
                'email': email,
                'name': name,
                'picture': picture,
                'exp': datetime.utcnow() + timedelta(days=7)
            },
            SECRET_KEY,
            algorithm='HS256'
        )
        
        print(f"🎫 JWT token created for user: {user_id}")
        
        return RedirectResponse(url=f"{FRONTEND_URL}/oauth-callback?token={jwt_token}")
        
    except Exception as e:
        print(f"❌ OAuth error: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url=f"{FRONTEND_URL}/oauth-callback?error={str(e)}")