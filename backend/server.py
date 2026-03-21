from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Query, Header, Response, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import requests
import hashlib
import secrets

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Object Storage Configuration
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "tratorshop"
storage_key = None

def init_storage():
    """Initialize storage and get reusable storage_key"""
    global storage_key
    if storage_key:
        return storage_key
    if not EMERGENT_KEY:
        logging.warning("EMERGENT_LLM_KEY not set - file uploads disabled")
        return None
    try:
        resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
        resp.raise_for_status()
        storage_key = resp.json()["storage_key"]
        return storage_key
    except Exception as e:
        logging.error(f"Storage init failed: {e}")
        return None

def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Upload file to object storage"""
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not available")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str) -> tuple:
    """Download file from object storage"""
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not available")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# Create the main app
app = FastAPI(title="TratorShop API", description="Agricultural Machinery Marketplace")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class UserBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    is_admin: bool = False
    created_at: str

class UserCreate(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None

class ListingBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    listing_id: str
    user_id: str
    title: str
    description: str
    category: str
    price: float
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    hours_used: Optional[int] = None
    condition: str
    city: str
    state: str = "MS"
    whatsapp: str
    images: List[str] = []
    status: str = "pending"  # pending, approved, rejected, expired
    is_featured: bool = False
    views: int = 0
    whatsapp_clicks: int = 0
    created_at: str
    approved_at: Optional[str] = None
    expires_at: Optional[str] = None

class ListingCreate(BaseModel):
    title: str
    description: str
    category: str
    price: float
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    hours_used: Optional[int] = None
    condition: str
    city: str
    whatsapp: str

class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    hours_used: Optional[int] = None
    condition: Optional[str] = None
    city: Optional[str] = None
    whatsapp: Optional[str] = None

class WhatsAppClick(BaseModel):
    model_config = ConfigDict(extra="ignore")
    click_id: str
    listing_id: str
    clicked_at: str
    user_agent: Optional[str] = None

class SessionData(BaseModel):
    user_id: str
    session_token: str
    expires_at: str
    created_at: str

# User Email/Password Auth Models
class UserRegister(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

# Admin Models
class AdminLogin(BaseModel):
    email: str
    password: str

class AdminCreate(BaseModel):
    email: str
    password: str
    name: str

class AdminChangePassword(BaseModel):
    current_password: str
    new_password: str

class PromoteToAdmin(BaseModel):
    user_email: str

# Dealer Models
class DealerProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    store_name: str
    store_slug: str
    store_logo: Optional[str] = None
    whatsapp: str
    city: str
    description: Optional[str] = None
    max_listings: int = 20
    is_active: bool = True
    created_at: str

class DealerProfileCreate(BaseModel):
    store_name: str
    whatsapp: str
    city: str
    description: Optional[str] = None

class DealerProfileUpdate(BaseModel):
    store_name: Optional[str] = None
    whatsapp: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None

class PromoteToDealer(BaseModel):
    user_email: str
    store_name: str
    max_listings: int = 20

class SetDealerLimit(BaseModel):
    max_listings: int

# User Onboarding Models
class UserOnboarding(BaseModel):
    account_type: str  # "individual" or "dealer"
    store_name: Optional[str] = None  # Required if dealer

# Admin User Management Models
class AdminUpdateUser(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    is_admin: Optional[bool] = None
    role: Optional[str] = None
    max_listings: Optional[int] = None

class AdminUpdateListing(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    hours_used: Optional[int] = None
    condition: Optional[str] = None
    city: Optional[str] = None
    whatsapp: Optional[str] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None

# Password hashing utilities
def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt, hashed = stored_hash.split(':')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return new_hash.hex() == hashed
    except:
        return False

# MS Cities for dropdown
MS_CITIES = [
    "Campo Grande", "Dourados", "Três Lagoas", "Corumbá", "Ponta Porã",
    "Naviraí", "Nova Andradina", "Aquidauana", "Sidrolândia", "Paranaíba",
    "Maracaju", "Coxim", "Amambai", "Rio Brilhante", "Cassilândia",
    "Chapadão do Sul", "Costa Rica", "São Gabriel do Oeste", "Jardim", "Bonito"
]

CATEGORIES = ["tratores", "implementos", "colheitadeiras", "pecas"]

# =============================================================================
# AUTH ROUTES
# =============================================================================

async def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from session token (cookie or header)"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        return None
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        return None
    
    # Check expiration
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user

async def require_user(request: Request) -> dict:
    """Require authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

async def require_admin(request: Request) -> dict:
    """Require admin user"""
    user = await require_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@api_router.post("/auth/session")
async def exchange_session(request: Request):
    """Exchange session_id from Emergent Auth for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Get session data from Emergent Auth
    try:
        resp = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id},
            timeout=30
        )
        resp.raise_for_status()
        auth_data = resp.json()
    except Exception as e:
        logger.error(f"Auth session exchange failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid session")
    
    email = auth_data.get("email")
    name = auth_data.get("name")
    picture = auth_data.get("picture")
    session_token = auth_data.get("session_token")
    
    # Find or create user
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update user data
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "picture": picture}}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "is_admin": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
    
    # Store session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Get full user data
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    
    response = JSONResponse(content=user)
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    return response

@api_router.get("/auth/me")
async def get_current_user_route(request: Request):
    """Get current authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@api_router.post("/auth/logout")
async def logout(request: Request):
    """Logout and clear session"""
    session_token = request.cookies.get("session_token")
    admin_token = request.cookies.get("admin_token")
    
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    if admin_token:
        await db.admin_sessions.delete_one({"session_token": admin_token})
    
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie(key="session_token", path="/")
    response.delete_cookie(key="admin_token", path="/")
    return response

@api_router.post("/auth/register")
async def register_user(data: UserRegister):
    """Register new user with email and password"""
    import re
    
    # Validate email format
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, data.email):
        raise HTTPException(status_code=400, detail="Email inválido")
    
    # Check if email already exists
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        # Check if user has password (registered with email) or only Google
        if existing.get("password_hash"):
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        else:
            # User exists from Google, add password to account
            password_hash = hash_password(data.password)
            await db.users.update_one(
                {"email": data.email.lower()},
                {"$set": {"password_hash": password_hash, "name": data.name}}
            )
            user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0, "password_hash": 0})
            return {"message": "Senha adicionada à conta existente", "user": user}
    
    # Validate password
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 6 caracteres")
    
    # Create new user
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": data.email.lower(),
        "name": data.name,
        "password_hash": hash_password(data.password),
        "picture": None,
        "is_admin": False,
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # Return user without password_hash and _id
    response_user = {
        "user_id": user_id,
        "email": user_doc["email"],
        "name": user_doc["name"],
        "picture": None,
        "is_admin": False,
        "role": "user",
        "created_at": user_doc["created_at"]
    }
    
    return {"message": "Cadastro realizado com sucesso", "user": response_user}

@api_router.post("/auth/login")
async def login_user(data: UserLogin):
    """Login user with email and password"""
    user = await db.users.find_one({"email": data.email.lower()})
    
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Check if user has password
    if not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Use o login com Google para esta conta")
    
    # Verify password
    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Generate session token
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session_doc = {
        "user_id": user["user_id"],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Prepare user data (without password_hash)
    user_data = {k: v for k, v in user.items() if k not in ["_id", "password_hash"]}
    
    response = JSONResponse(content=user_data)
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    return response

# =============================================================================
# ADMIN AUTH ROUTES
# =============================================================================

async def get_current_admin(request: Request) -> Optional[dict]:
    """Get current admin from admin_token cookie or header"""
    admin_token = request.cookies.get("admin_token")
    if not admin_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            admin_token = auth_header.split(" ")[1]
    
    if not admin_token:
        return None
    
    session = await db.admin_sessions.find_one({"session_token": admin_token}, {"_id": 0})
    if not session:
        return None
    
    # Check expiration
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    admin = await db.admins.find_one({"admin_id": session["admin_id"]}, {"_id": 0, "password_hash": 0})
    return admin

async def require_admin(request: Request) -> dict:
    """Require authenticated admin"""
    admin = await get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    return admin

@api_router.post("/admin/auth/login")
async def admin_login(credentials: AdminLogin):
    """Admin login with email and password"""
    admin = await db.admins.find_one({"email": credentials.email.lower()})
    
    if not admin:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    if not verify_password(credentials.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # Generate session token
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
    
    session_doc = {
        "admin_id": admin["admin_id"],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_sessions.insert_one(session_doc)
    
    # Return admin data without password
    admin_data = {
        "admin_id": admin["admin_id"],
        "email": admin["email"],
        "name": admin["name"],
        "role": admin.get("role", "admin"),
        "must_change_password": admin.get("must_change_password", False)
    }
    
    response = JSONResponse(content=admin_data)
    response.set_cookie(
        key="admin_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=12 * 60 * 60  # 12 hours
    )
    return response

@api_router.get("/admin/auth/me")
async def get_current_admin_route(request: Request):
    """Get current authenticated admin"""
    admin = await get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Not authenticated as admin")
    return admin

@api_router.post("/admin/auth/logout")
async def admin_logout(request: Request):
    """Admin logout"""
    admin_token = request.cookies.get("admin_token")
    if admin_token:
        await db.admin_sessions.delete_one({"session_token": admin_token})
    
    response = JSONResponse(content={"message": "Admin logged out"})
    response.delete_cookie(key="admin_token", path="/")
    return response

@api_router.post("/admin/auth/change-password")
async def admin_change_password(data: AdminChangePassword, request: Request):
    """Change admin password"""
    admin = await require_admin(request)
    
    # Get admin with password hash
    admin_full = await db.admins.find_one({"admin_id": admin["admin_id"]})
    
    if not verify_password(data.current_password, admin_full["password_hash"]):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    
    # Validate new password
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Nova senha deve ter pelo menos 8 caracteres")
    
    # Update password
    new_hash = hash_password(data.new_password)
    await db.admins.update_one(
        {"admin_id": admin["admin_id"]},
        {"$set": {"password_hash": new_hash, "must_change_password": False}}
    )
    
    return {"message": "Senha alterada com sucesso"}

@api_router.post("/admin/auth/create-admin")
async def create_admin(data: AdminCreate, request: Request):
    """Create new admin (requires existing admin)"""
    await require_admin(request)
    
    # Check if email already exists
    existing = await db.admins.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    admin_id = f"admin_{uuid.uuid4().hex[:12]}"
    admin_doc = {
        "admin_id": admin_id,
        "email": data.email.lower(),
        "name": data.name,
        "password_hash": hash_password(data.password),
        "role": "admin",
        "must_change_password": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.admins.insert_one(admin_doc)
    
    return {"message": "Admin criado com sucesso", "admin_id": admin_id}

@api_router.post("/admin/promote-user")
async def promote_user_to_admin(data: PromoteToAdmin, request: Request):
    """Promote a regular user to have admin-like privileges in users collection"""
    await require_admin(request)
    
    user = await db.users.find_one({"email": data.user_email.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    await db.users.update_one(
        {"email": data.user_email.lower()},
        {"$set": {"is_admin": True}}
    )
    
    return {"message": f"Usuário {user['name']} promovido com sucesso"}

@api_router.get("/admin/users")
async def list_users(request: Request):
    """List all users (admin only)"""
    await require_admin(request)
    
    users = await db.users.find({}, {"_id": 0}).to_list(500)
    return users

# =============================================================================
# DEALER ROUTES
# =============================================================================

def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from store name"""
    import re
    slug = name.lower()
    slug = re.sub(r'[àáâãäå]', 'a', slug)
    slug = re.sub(r'[èéêë]', 'e', slug)
    slug = re.sub(r'[ìíîï]', 'i', slug)
    slug = re.sub(r'[òóôõö]', 'o', slug)
    slug = re.sub(r'[ùúûü]', 'u', slug)
    slug = re.sub(r'[ç]', 'c', slug)
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug

@api_router.get("/dealers")
async def list_public_dealers():
    """List all active dealers (public)"""
    dealers = await db.users.find(
        {"role": "dealer", "dealer_profile.is_active": True},
        {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "dealer_profile": 1}
    ).to_list(100)
    
    # Add listing counts for each dealer
    result = []
    for dealer in dealers:
        active_count = await db.listings.count_documents({
            "user_id": dealer["user_id"],
            "status": "approved"
        })
        result.append({
            "user_id": dealer["user_id"],
            "name": dealer["name"],
            "picture": dealer.get("picture"),
            "store_name": dealer.get("dealer_profile", {}).get("store_name"),
            "store_slug": dealer.get("dealer_profile", {}).get("store_slug"),
            "store_logo": dealer.get("dealer_profile", {}).get("store_logo"),
            "city": dealer.get("dealer_profile", {}).get("city"),
            "description": dealer.get("dealer_profile", {}).get("description"),
            "active_listings": active_count
        })
    
    return result

# =============================================================================
# USER ONBOARDING ROUTES
# =============================================================================

@api_router.get("/user/profile")
async def get_user_profile(request: Request):
    """Get current user's profile with limits"""
    user = await require_user(request)
    
    # Count active listings
    active_count = await db.listings.count_documents({
        "user_id": user["user_id"],
        "status": {"$in": ["approved", "pending"]}
    })
    
    # Get max listings based on account type
    if user.get("role") == "dealer":
        max_listings = user.get("dealer_profile", {}).get("max_listings", 20)
    else:
        max_listings = user.get("max_listings", 3)  # Default 3 for individuals
    
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "role": user.get("role", "user"),
        "account_type": user.get("account_type"),  # "individual" or "dealer"
        "onboarding_complete": user.get("onboarding_complete", False),
        "is_admin": user.get("is_admin", False),
        "max_listings": max_listings,
        "active_listings": active_count,
        "dealer_profile": user.get("dealer_profile") if user.get("role") == "dealer" else None
    }

@api_router.post("/user/onboarding")
async def complete_onboarding(data: UserOnboarding, request: Request):
    """Complete user onboarding - select account type"""
    user = await require_user(request)
    
    if data.account_type not in ["individual", "dealer"]:
        raise HTTPException(status_code=400, detail="Tipo de conta inválido")
    
    update_data = {
        "account_type": data.account_type,
        "onboarding_complete": True
    }
    
    if data.account_type == "individual":
        update_data["role"] = "user"
        update_data["max_listings"] = 3  # Individual sellers get 3 listings
    elif data.account_type == "dealer":
        if not data.store_name:
            raise HTTPException(status_code=400, detail="Nome da loja é obrigatório para Dealers")
        
        # Generate slug
        slug = generate_slug(data.store_name)
        existing = await db.users.find_one({"dealer_profile.store_slug": slug})
        if existing:
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        
        update_data["role"] = "dealer"
        update_data["dealer_profile"] = {
            "store_name": data.store_name,
            "store_slug": slug,
            "store_logo": None,
            "whatsapp": "",
            "city": "",
            "description": "",
            "max_listings": 10,  # Dealers start with 10 listings
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": update_data})
    
    # Return updated user
    updated_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0, "password_hash": 0})
    return updated_user

@api_router.get("/dealers/{slug}")
async def get_dealer_public(slug: str):
    """Get dealer public profile by slug"""
    user = await db.users.find_one(
        {"dealer_profile.store_slug": slug, "role": "dealer"},
        {"_id": 0, "password_hash": 0}
    )
    if not user:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    
    # Count active listings
    active_count = await db.listings.count_documents({
        "user_id": user["user_id"],
        "status": "approved"
    })
    
    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "picture": user.get("picture"),
        "dealer_profile": user["dealer_profile"],
        "active_listings": active_count
    }

@api_router.get("/dealers/{slug}/listings")
async def get_dealer_listings(
    slug: str,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """Get dealer's approved listings"""
    user = await db.users.find_one(
        {"dealer_profile.store_slug": slug, "role": "dealer"},
        {"_id": 0}
    )
    if not user:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    
    query = {"user_id": user["user_id"], "status": "approved"}
    if category:
        query["category"] = category.lower()
    
    skip = (page - 1) * limit
    listings = await db.listings.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.listings.count_documents(query)
    
    return {
        "listings": listings,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@api_router.get("/dealer/profile")
async def get_dealer_profile(request: Request):
    """Get current user's dealer profile"""
    user = await require_user(request)
    
    if user.get("role") != "dealer":
        raise HTTPException(status_code=403, detail="Você não é um dealer")
    
    # Count active listings
    active_count = await db.listings.count_documents({
        "user_id": user["user_id"],
        "status": "approved"
    })
    
    pending_count = await db.listings.count_documents({
        "user_id": user["user_id"],
        "status": "pending"
    })
    
    return {
        "dealer_profile": user.get("dealer_profile"),
        "active_listings": active_count,
        "pending_listings": pending_count,
        "max_listings": user.get("dealer_profile", {}).get("max_listings", 20)
    }

@api_router.put("/dealer/profile")
async def update_dealer_profile(data: DealerProfileUpdate, request: Request):
    """Update dealer profile (dealer only)"""
    user = await require_user(request)
    
    if user.get("role") != "dealer":
        raise HTTPException(status_code=403, detail="Você não é um dealer")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    # If store name changed, update slug
    if "store_name" in update_data:
        new_slug = generate_slug(update_data["store_name"])
        # Check if slug already exists
        existing = await db.users.find_one({
            "dealer_profile.store_slug": new_slug,
            "user_id": {"$ne": user["user_id"]}
        })
        if existing:
            new_slug = f"{new_slug}-{uuid.uuid4().hex[:6]}"
        update_data["store_slug"] = new_slug
    
    if update_data:
        update_fields = {f"dealer_profile.{k}": v for k, v in update_data.items()}
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": update_fields})
    
    updated_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return updated_user.get("dealer_profile")

@api_router.post("/dealer/logo")
async def upload_dealer_logo(file: UploadFile = File(...), request: Request = None):
    """Upload dealer logo"""
    user = await require_user(request)
    
    if user.get("role") != "dealer":
        raise HTTPException(status_code=403, detail="Você não é um dealer")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Apenas JPEG, PNG, WEBP permitidos")
    
    # Upload to storage
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    path = f"{APP_NAME}/dealers/{user['user_id']}/logo.{ext}"
    data = await file.read()
    
    result = put_object(path, data, file.content_type)
    
    # Update user profile
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"dealer_profile.store_logo": result["path"]}}
    )
    
    return {"path": result["path"], "message": "Logo atualizado"}

# =============================================================================
# ADMIN SUPER ROUTES (Statistics & Management)
# =============================================================================

@api_router.get("/admin/stats")
async def get_admin_stats(request: Request):
    """Get admin dashboard statistics"""
    await require_admin(request)
    
    # Count users
    total_users = await db.users.count_documents({})
    total_dealers = await db.users.count_documents({"role": "dealer"})
    total_individuals = await db.users.count_documents({"role": {"$ne": "dealer"}})
    
    # Count listings
    total_listings = await db.listings.count_documents({})
    pending_listings = await db.listings.count_documents({"status": "pending"})
    approved_listings = await db.listings.count_documents({"status": "approved"})
    rejected_listings = await db.listings.count_documents({"status": "rejected"})
    featured_listings = await db.listings.count_documents({"is_featured": True, "status": "approved"})
    
    # Count by category
    categories = {}
    for cat in ["tratores", "implementos", "colheitadeiras", "pecas"]:
        categories[cat] = await db.listings.count_documents({"category": cat, "status": "approved"})
    
    # Recent activity (last 7 days)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    new_users_week = await db.users.count_documents({"created_at": {"$gte": week_ago}})
    new_listings_week = await db.listings.count_documents({"created_at": {"$gte": week_ago}})
    
    return {
        "users": {
            "total": total_users,
            "dealers": total_dealers,
            "individuals": total_individuals,
            "new_this_week": new_users_week
        },
        "listings": {
            "total": total_listings,
            "pending": pending_listings,
            "approved": approved_listings,
            "rejected": rejected_listings,
            "featured": featured_listings,
            "new_this_week": new_listings_week
        },
        "categories": categories
    }

@api_router.put("/admin/users/{user_id}")
async def admin_update_user(user_id: str, data: AdminUpdateUser, request: Request):
    """Admin update user details"""
    await require_admin(request)
    
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    if update_data:
        await db.users.update_one({"user_id": user_id}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    return updated_user

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str, request: Request):
    """Admin delete user and their listings"""
    await require_admin(request)
    
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Delete user's listings
    deleted_listings = await db.listings.delete_many({"user_id": user_id})
    
    # Delete user
    await db.users.delete_one({"user_id": user_id})
    
    return {
        "message": f"Usuário {user['name']} removido",
        "deleted_listings": deleted_listings.deleted_count
    }

@api_router.put("/admin/users/{user_id}/limit")
async def admin_set_user_limit(user_id: str, data: SetDealerLimit, request: Request):
    """Set listing limit for any user (not just dealers)"""
    await require_admin(request)
    
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if user.get("role") == "dealer":
        # Update dealer profile limit
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"dealer_profile.max_listings": data.max_listings}}
        )
    else:
        # Update individual user limit
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"max_listings": data.max_listings}}
        )
    
    return {"message": f"Limite atualizado para {data.max_listings} anúncios"}

@api_router.put("/admin/listings/{listing_id}")
async def admin_update_listing(listing_id: str, data: AdminUpdateListing, request: Request):
    """Admin update any listing"""
    await require_admin(request)
    
    listing = await db.listings.find_one({"listing_id": listing_id})
    if not listing:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    # If changing status to approved, set approval date and expiry
    if update_data.get("status") == "approved" and listing.get("status") != "approved":
        now = datetime.now(timezone.utc)
        update_data["approved_at"] = now.isoformat()
        update_data["expires_at"] = (now + timedelta(days=90)).isoformat()
    
    if update_data:
        await db.listings.update_one({"listing_id": listing_id}, {"$set": update_data})
    
    updated_listing = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    return updated_listing

@api_router.delete("/admin/listings/{listing_id}")
async def admin_delete_listing(listing_id: str, request: Request):
    """Admin delete any listing"""
    await require_admin(request)
    
    listing = await db.listings.find_one({"listing_id": listing_id})
    if not listing:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    
    await db.listings.delete_one({"listing_id": listing_id})
    
    return {"message": "Anúncio removido com sucesso"}

# =============================================================================
# ADMIN DEALER ROUTES
# =============================================================================

@api_router.get("/admin/dealers")
async def list_dealers(request: Request):
    """List all dealers (admin only)"""
    await require_admin(request)
    
    dealers = await db.users.find({"role": "dealer"}, {"_id": 0, "password_hash": 0}).to_list(500)
    
    # Add listing counts for each dealer
    for dealer in dealers:
        dealer["active_listings"] = await db.listings.count_documents({
            "user_id": dealer["user_id"],
            "status": "approved"
        })
        dealer["pending_listings"] = await db.listings.count_documents({
            "user_id": dealer["user_id"],
            "status": "pending"
        })
        dealer["total_listings"] = await db.listings.count_documents({
            "user_id": dealer["user_id"]
        })
    
    return dealers

@api_router.post("/admin/dealers/promote")
async def promote_to_dealer(data: PromoteToDealer, request: Request):
    """Promote user to dealer (admin only)"""
    await require_admin(request)
    
    user = await db.users.find_one({"email": data.user_email.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if user.get("role") == "dealer":
        raise HTTPException(status_code=400, detail="Usuário já é um dealer")
    
    # Generate slug
    slug = generate_slug(data.store_name)
    existing = await db.users.find_one({"dealer_profile.store_slug": slug})
    if existing:
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
    
    dealer_profile = {
        "store_name": data.store_name,
        "store_slug": slug,
        "store_logo": None,
        "whatsapp": "",
        "city": "",
        "description": "",
        "max_listings": data.max_listings,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.update_one(
        {"email": data.user_email.lower()},
        {"$set": {"role": "dealer", "dealer_profile": dealer_profile}}
    )
    
    return {"message": f"Usuário {user['name']} promovido a dealer", "store_slug": slug}

@api_router.put("/admin/dealers/{user_id}/limit")
async def set_dealer_limit(user_id: str, data: SetDealerLimit, request: Request):
    """Set dealer listing limit (admin only)"""
    await require_admin(request)
    
    user = await db.users.find_one({"user_id": user_id, "role": "dealer"})
    if not user:
        raise HTTPException(status_code=404, detail="Dealer não encontrado")
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"dealer_profile.max_listings": data.max_listings}}
    )
    
    return {"message": f"Limite atualizado para {data.max_listings} anúncios"}

@api_router.post("/admin/dealers/{user_id}/toggle-active")
async def toggle_dealer_active(user_id: str, request: Request):
    """Toggle dealer active status (admin only)"""
    await require_admin(request)
    
    user = await db.users.find_one({"user_id": user_id, "role": "dealer"}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Dealer não encontrado")
    
    new_status = not user.get("dealer_profile", {}).get("is_active", True)
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"dealer_profile.is_active": new_status}}
    )
    
    return {"message": f"Dealer {'ativado' if new_status else 'desativado'}", "is_active": new_status}

@api_router.delete("/admin/dealers/{user_id}")
async def demote_dealer(user_id: str, request: Request):
    """Remove dealer status from user (admin only)"""
    await require_admin(request)
    
    user = await db.users.find_one({"user_id": user_id, "role": "dealer"})
    if not user:
        raise HTTPException(status_code=404, detail="Dealer não encontrado")
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"role": "user"}, "$unset": {"dealer_profile": ""}}
    )
    
    return {"message": "Status de dealer removido"}

@api_router.get("/listings")
async def get_listings(
    category: Optional[str] = None,
    city: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    featured: Optional[bool] = None,
    page: int = 1,
    limit: int = 20
):
    """Get approved listings with filters"""
    query = {"status": "approved"}
    
    if category:
        query["category"] = category.lower()
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
            {"model": {"$regex": search, "$options": "i"}}
        ]
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price", {})["$lte"] = max_price
    if featured:
        query["is_featured"] = True
    
    # Check for expired listings and update status
    now = datetime.now(timezone.utc).isoformat()
    await db.listings.update_many(
        {"status": "approved", "expires_at": {"$lt": now}},
        {"$set": {"status": "expired"}}
    )
    
    skip = (page - 1) * limit
    sort = [("is_featured", -1), ("created_at", -1)]
    
    listings = await db.listings.find(query, {"_id": 0}).sort(sort).skip(skip).limit(limit).to_list(limit)
    total = await db.listings.count_documents(query)
    
    return {
        "listings": listings,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@api_router.get("/listings/featured")
async def get_featured_listings(limit: int = 8):
    """Get featured approved listings"""
    query = {"status": "approved", "is_featured": True}
    listings = await db.listings.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return listings

@api_router.get("/listings/{listing_id}")
async def get_listing(listing_id: str):
    """Get single listing by ID"""
    listing = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Increment views
    await db.listings.update_one({"listing_id": listing_id}, {"$inc": {"views": 1}})
    listing["views"] = listing.get("views", 0) + 1
    
    # Get seller info
    seller = await db.users.find_one({"user_id": listing["user_id"]}, {"_id": 0, "user_id": 1, "name": 1, "picture": 1})
    listing["seller"] = seller
    
    return listing

@api_router.post("/listings")
async def create_listing(listing: ListingCreate, request: Request):
    """Create new listing (requires auth)"""
    user = await require_user(request)
    
    # Check listing limit based on user type
    current_count = await db.listings.count_documents({
        "user_id": user["user_id"],
        "status": {"$in": ["pending", "approved"]}
    })
    
    if user.get("role") == "dealer":
        max_listings = user.get("dealer_profile", {}).get("max_listings", 20)
    else:
        max_listings = user.get("max_listings", 3)  # Default 3 for individuals
    
    if current_count >= max_listings:
        raise HTTPException(
            status_code=400, 
            detail=f"Limite de {max_listings} anúncios ativos atingido. Entre em contato com o administrador para aumentar seu limite."
        )
    
    listing_id = f"listing_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    listing_doc = {
        "listing_id": listing_id,
        "user_id": user["user_id"],
        "title": listing.title,
        "description": listing.description,
        "category": listing.category.lower(),
        "price": listing.price,
        "brand": listing.brand,
        "model": listing.model,
        "year": listing.year,
        "hours_used": listing.hours_used,
        "condition": listing.condition,
        "city": listing.city,
        "state": "MS",
        "whatsapp": listing.whatsapp,
        "images": [],
        "status": "pending",
        "is_featured": False,
        "views": 0,
        "whatsapp_clicks": 0,
        "created_at": now.isoformat(),
        "approved_at": None,
        "expires_at": None
    }
    
    await db.listings.insert_one(listing_doc)
    return {"listing_id": listing_id, "message": "Anúncio criado e aguardando aprovação"}

@api_router.put("/listings/{listing_id}")
async def update_listing(listing_id: str, listing: ListingUpdate, request: Request):
    """Update listing (owner only)"""
    user = await require_user(request)
    
    existing = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if existing["user_id"] != user["user_id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in listing.model_dump().items() if v is not None}
    if update_data:
        # Reset to pending if content changed
        if not user.get("is_admin"):
            update_data["status"] = "pending"
        await db.listings.update_one({"listing_id": listing_id}, {"$set": update_data})
    
    updated = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    return updated

@api_router.delete("/listings/{listing_id}")
async def delete_listing(listing_id: str, request: Request):
    """Delete listing (owner or admin)"""
    user = await require_user(request)
    
    existing = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if existing["user_id"] != user["user_id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.listings.delete_one({"listing_id": listing_id})
    return {"message": "Listing deleted"}

@api_router.get("/my-listings")
async def get_my_listings(request: Request):
    """Get current user's listings"""
    user = await require_user(request)
    listings = await db.listings.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return listings

# =============================================================================
# FILE UPLOAD ROUTES
# =============================================================================

@api_router.post("/listings/{listing_id}/images")
async def upload_listing_image(listing_id: str, file: UploadFile = File(...), request: Request = None):
    """Upload image to listing"""
    user = await require_user(request)
    
    listing = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing["user_id"] != user["user_id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WEBP images allowed")
    
    # Upload to storage
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    path = f"{APP_NAME}/listings/{listing_id}/{uuid.uuid4()}.{ext}"
    data = await file.read()
    
    result = put_object(path, data, file.content_type)
    
    # Add to listing images
    await db.listings.update_one(
        {"listing_id": listing_id},
        {"$push": {"images": result["path"]}}
    )
    
    return {"path": result["path"], "message": "Image uploaded"}

@api_router.get("/files/{path:path}")
async def get_file(path: str):
    """Serve file from object storage"""
    try:
        data, content_type = get_object(path)
        return Response(content=data, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")

# =============================================================================
# WHATSAPP TRACKING
# =============================================================================

@api_router.post("/listings/{listing_id}/whatsapp-click")
async def track_whatsapp_click(listing_id: str, request: Request):
    """Track WhatsApp button click"""
    listing = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    user_agent = request.headers.get("User-Agent")
    click_doc = {
        "click_id": f"click_{uuid.uuid4().hex[:12]}",
        "listing_id": listing_id,
        "clicked_at": datetime.now(timezone.utc).isoformat(),
        "user_agent": user_agent
    }
    await db.whatsapp_clicks.insert_one(click_doc)
    
    # Increment counter
    await db.listings.update_one({"listing_id": listing_id}, {"$inc": {"whatsapp_clicks": 1}})
    
    return {"message": "Click tracked"}

# =============================================================================
# ADMIN ROUTES
# =============================================================================

@api_router.get("/admin/listings")
async def admin_get_listings(
    status: Optional[str] = None,
    request: Request = None
):
    """Get all listings for admin"""
    await require_admin(request)
    
    query = {}
    if status:
        query["status"] = status
    
    listings = await db.listings.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Add seller info
    for listing in listings:
        seller = await db.users.find_one({"user_id": listing["user_id"]}, {"_id": 0, "name": 1, "email": 1})
        listing["seller"] = seller
    
    return listings

@api_router.post("/admin/listings/{listing_id}/approve")
async def approve_listing(listing_id: str, request: Request):
    """Approve a listing"""
    await require_admin(request)
    
    listing = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=90)
    
    await db.listings.update_one(
        {"listing_id": listing_id},
        {"$set": {
            "status": "approved",
            "approved_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
        }}
    )
    
    return {"message": "Listing approved", "expires_at": expires_at.isoformat()}

@api_router.post("/admin/listings/{listing_id}/reject")
async def reject_listing(listing_id: str, request: Request):
    """Reject a listing"""
    await require_admin(request)
    
    await db.listings.update_one(
        {"listing_id": listing_id},
        {"$set": {"status": "rejected"}}
    )
    
    return {"message": "Listing rejected"}

@api_router.post("/admin/listings/{listing_id}/feature")
async def toggle_featured(listing_id: str, featured: bool = True, request: Request = None):
    """Toggle featured status"""
    await require_admin(request)
    
    await db.listings.update_one(
        {"listing_id": listing_id},
        {"$set": {"is_featured": featured}}
    )
    
    return {"message": f"Listing {'featured' if featured else 'unfeatured'}"}

@api_router.post("/admin/make-admin/{user_id}")
async def make_admin(user_id: str, request: Request):
    """Make a user admin (for setup)"""
    # Check if any admin exists
    admin_exists = await db.users.find_one({"is_admin": True}, {"_id": 0})
    
    # If admin exists, require admin auth
    if admin_exists:
        await require_admin(request)
    
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_admin": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User is now admin"}

# =============================================================================
# UTILITY ROUTES
# =============================================================================

@api_router.get("/categories")
async def get_categories():
    """Get available categories"""
    return [
        {"id": "tratores", "name": "Tratores", "icon": "tractor"},
        {"id": "implementos", "name": "Implementos", "icon": "wrench"},
        {"id": "colheitadeiras", "name": "Colheitadeiras", "icon": "combine"},
        {"id": "pecas", "name": "Peças", "icon": "cog"}
    ]

@api_router.get("/cities")
async def get_cities():
    """Get MS cities"""
    return MS_CITIES

@api_router.get("/stats")
async def get_stats():
    """Get marketplace stats"""
    total_listings = await db.listings.count_documents({"status": "approved"})
    total_users = await db.users.count_documents({})
    total_clicks = await db.whatsapp_clicks.count_documents({})
    
    return {
        "total_listings": total_listings,
        "total_users": total_users,
        "total_whatsapp_clicks": total_clicks
    }

@api_router.get("/")
async def root():
    return {"message": "TratorShop API", "version": "1.0.0"}

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    try:
        init_storage()
        logger.info("Storage initialized")
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
    
    # Create indexes
    await db.listings.create_index([("status", 1), ("is_featured", -1), ("created_at", -1)])
    await db.listings.create_index([("user_id", 1)])
    await db.listings.create_index([("category", 1)])
    await db.listings.create_index([("city", 1)])
    await db.users.create_index([("email", 1)], unique=True)
    await db.user_sessions.create_index([("session_token", 1)], unique=True)
    await db.admins.create_index([("email", 1)], unique=True)
    await db.admin_sessions.create_index([("session_token", 1)], unique=True)
    
    # Create default admin if not exists
    default_admin = await db.admins.find_one({"email": "admin@tratorshop.com"})
    if not default_admin:
        admin_doc = {
            "admin_id": f"admin_{uuid.uuid4().hex[:12]}",
            "email": "admin@tratorshop.com",
            "name": "Administrador",
            "password_hash": hash_password("Admin@123"),
            "role": "super_admin",
            "must_change_password": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.admins.insert_one(admin_doc)
        logger.info("Default admin account created: admin@tratorshop.com")
    
    logger.info("Database indexes created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
