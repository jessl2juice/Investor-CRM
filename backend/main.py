"""
BetterMind CRM - FastAPI Backend
Serves REST API + static React frontend.
Routes are organized into modules under routes/.
"""
import logging
import os
from contextlib import asynccontextmanager, contextmanager

import sqlalchemy

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import get_engine, get_connection, init_schema, seed_data, seed_users, _hash_password, _verify_password
from auth import make_token, require_auth, require_admin
from models import LoginRequest, UserCreate, PasswordUpdate

from routes.contacts import router as contacts_router
from routes.organizations import router as organizations_router
from routes.interactions import router as interactions_router
from routes.deals import router as deals_router
from routes.programs import router as programs_router

logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",")
if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == [""]:
    ALLOWED_ORIGINS = [
        "https://bettermind-crm-340933752067.us-west1.run.app",
        "https://bettermind.buzz",
        "http://localhost:5173",
        "http://localhost:8080",
    ]


@asynccontextmanager
async def lifespan(app):
    """Initialize database schema and seed data on startup."""
    engine = get_engine()
    with engine.connect() as conn:
        init_schema(conn)
        seed_data(conn)
        seed_users(conn)
    yield


app = FastAPI(
    title="BetterMind CRM API",
    description="Contact management, investor pipeline, and program tracking for startups.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== DB HELPERS ====================

@contextmanager
def db():
    """Database connection context manager with rollback on error."""
    conn = get_engine().connect()
    try:
        yield conn
    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def row_to_dict(row):
    """Convert a SQLAlchemy row to a dict."""
    if row is None:
        return None
    return dict(row._mapping)


def rows_to_list(rows):
    """Convert SQLAlchemy result rows to a list of dicts."""
    return [dict(r._mapping) for r in rows]


# ==================== AUTH ROUTES ====================

@app.post("/api/login")
def login(data: LoginRequest):
    """Authenticate with email/password and receive a token."""
    with db() as conn:
        row = conn.execute(sqlalchemy.text(
            "SELECT id, email, password_hash, password_salt, name, role FROM users WHERE email = :e"
        ), {"e": data.email}).fetchone()
        if not row:
            raise HTTPException(401, "Invalid credentials")
        user = dict(row._mapping)
        if not _verify_password(data.password, user["password_hash"], user["password_salt"]):
            raise HTTPException(401, "Invalid credentials")
        return {"token": make_token(user["email"], user["role"]), "email": user["email"], "name": user["name"], "role": user["role"]}


@app.get("/api/me")
def me(auth=Depends(require_auth)):
    """Get current user info from token."""
    return {"email": auth["email"], "role": auth["role"]}


# ==================== USER MANAGEMENT ====================

@app.get("/api/users")
def list_users(auth=Depends(require_admin)):
    """List all users (admin only)."""
    with db() as conn:
        return rows_to_list(conn.execute(sqlalchemy.text(
            "SELECT id, email, name, role, created_at FROM users ORDER BY id"
        )).fetchall())


@app.post("/api/users", status_code=201)
def create_user(data: UserCreate, auth=Depends(require_admin)):
    """Create a new user (admin only)."""
    pw_hash, pw_salt = _hash_password(data.password)
    with db() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT id FROM users WHERE email = :e"), {"e": data.email}).fetchone()
        if existing:
            raise HTTPException(409, "User with this email already exists")
        row = conn.execute(sqlalchemy.text(
            "INSERT INTO users (email, password_hash, password_salt, name, role) VALUES (:e, :h, :s, :n, :r) RETURNING id"
        ), {"e": data.email, "h": pw_hash, "s": pw_salt, "n": data.name, "r": data.role}).fetchone()
        conn.commit()
        return {"id": row[0], "email": data.email, "name": data.name, "role": data.role}


@app.put("/api/users/{user_id}/password")
def update_password(user_id: int, data: PasswordUpdate, auth=Depends(require_auth)):
    """Change a user's password. Users can change their own; admins can change any."""
    with db() as conn:
        user = conn.execute(sqlalchemy.text("SELECT id, email, role FROM users WHERE id = :uid"), {"uid": user_id}).fetchone()
        if not user:
            raise HTTPException(404, "User not found")
        user_dict = dict(user._mapping)
        if auth["role"] != "admin" and auth["email"] != user_dict["email"]:
            raise HTTPException(403, "Can only change your own password")
        pw_hash, pw_salt = _hash_password(data.password)
        conn.execute(sqlalchemy.text(
            "UPDATE users SET password_hash = :h, password_salt = :s WHERE id = :uid"
        ), {"h": pw_hash, "s": pw_salt, "uid": user_id})
        conn.commit()
        return {"ok": True}


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, auth=Depends(require_admin)):
    """Delete a user (admin only). Cannot delete yourself."""
    with db() as conn:
        user = conn.execute(sqlalchemy.text("SELECT email FROM users WHERE id = :uid"), {"uid": user_id}).fetchone()
        if not user:
            raise HTTPException(404, "User not found")
        if dict(user._mapping)["email"] == auth["email"]:
            raise HTTPException(400, "Cannot delete yourself")
        conn.execute(sqlalchemy.text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
        conn.commit()
        return {"deleted": user_id}


# ==================== INCLUDE ROUTE MODULES ====================

app.include_router(contacts_router)
app.include_router(organizations_router)
app.include_router(interactions_router)
app.include_router(deals_router)
app.include_router(programs_router)


# ==================== STATS ====================

@app.get("/api/stats")
def get_stats(auth=Depends(require_auth)):
    """Dashboard statistics: counts by category, status, pipeline, etc."""
    with db() as conn:
        stats = {}
        stats["total_contacts"] = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM contacts")).fetchone()[0]
        stats["by_category"] = {r[0]: r[1] for r in conn.execute(sqlalchemy.text("SELECT category, COUNT(*) FROM contacts GROUP BY category")).fetchall()}
        stats["by_status"] = {r[0]: r[1] for r in conn.execute(sqlalchemy.text("SELECT status, COUNT(*) FROM contacts GROUP BY status")).fetchall()}
        stats["active_investors"] = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM contacts WHERE category='investor' AND status NOT IN ('passed','cold')")).fetchone()[0]
        stats["pipeline_probability"] = conn.execute(sqlalchemy.text("SELECT SUM(probability) FROM deals")).fetchone()[0] or 0
        stats["active_deals"] = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM deals WHERE stage NOT IN ('passed','dead','closed')")).fetchone()[0]
        stats["total_interactions"] = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM interactions")).fetchone()[0]
        stats["total_organizations"] = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM organizations")).fetchone()[0]
        return stats


# ==================== HELP ====================

@app.get("/api/help")
def get_help():
    """Return the user manual content for the in-app help viewer."""
    manual_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "USER_MANUAL.md")
    if not os.path.isfile(manual_path):
        raise HTTPException(404, "User manual not found")
    with open(manual_path, "r", encoding="utf-8") as f:
        return {"content": f.read()}


# ==================== STATIC FRONTEND ====================

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """Serve the React SPA. Serves static files if they exist, otherwise index.html."""
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
