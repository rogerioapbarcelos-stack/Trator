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
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie(key="session_token", path="/")
    return response

# =============================================================================
# LISTING ROUTES
# =============================================================================

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
    logger.info("Database indexes created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
