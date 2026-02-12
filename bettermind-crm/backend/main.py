"""
BetterMind CRM — FastAPI Backend
Serves REST API + static React frontend
"""
import os
import hashlib
import hmac
import secrets
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import sqlalchemy

from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import get_engine, get_connection, init_schema, seed_data

AUTH_EMAIL = os.environ.get("AUTH_EMAIL", "jess@clinicianassist.ai")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "Onelongpassword!")
TOKEN_SECRET = os.environ.get("TOKEN_SECRET", secrets.token_hex(32))
TOKEN_TTL = 86400 * 7  # 7 days


def _make_token():
    ts = str(int(time.time()))
    sig = hmac.new(TOKEN_SECRET.encode(), ts.encode(), hashlib.sha256).hexdigest()
    return f"{ts}.{sig}"


def _verify_token(token: str) -> bool:
    try:
        ts, sig = token.split(".", 1)
        expected = hmac.new(TOKEN_SECRET.encode(), ts.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False
        if time.time() - int(ts) > TOKEN_TTL:
            return False
        return True
    except Exception:
        return False


def require_auth(request: Request):
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and _verify_token(auth[7:]):
        return True
    raise HTTPException(401, "Unauthorized")

app = FastAPI(
    title="BetterMind CRM API",
    description="Contact management, investor pipeline, and program tracking for BetterMind.Space",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@contextmanager
def db():
    conn = get_engine().connect()
    try:
        yield conn
    finally:
        conn.close()


def row_to_dict(row):
    if row is None:
        return None
    return dict(row._mapping)


def rows_to_list(rows):
    return [dict(r._mapping) for r in rows]


# ==================== STARTUP ====================

@app.on_event("startup")
def startup():
    engine = get_engine()
    with engine.connect() as conn:
        init_schema(conn)
        seed_data(conn)


# ==================== AUTH ====================

class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/login")
def login(data: LoginRequest):
    if data.email == AUTH_EMAIL and data.password == AUTH_PASSWORD:
        return {"token": _make_token(), "email": data.email}
    raise HTTPException(401, "Invalid credentials")


@app.get("/api/me")
def me(auth=Depends(require_auth)):
    return {"email": AUTH_EMAIL}


# ==================== MODELS ====================

class ContactCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    email_secondary: Optional[str] = None
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None
    linkedin_url: Optional[str] = None
    organization_id: Optional[int] = None
    title: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    status: str
    tier: Optional[int] = None
    last_contact_date: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[str] = None
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    organization_id: Optional[int] = None
    title: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    status: Optional[str] = None
    tier: Optional[int] = None
    last_contact_date: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[str] = None
    notes: Optional[str] = None


class InteractionCreate(BaseModel):
    contact_id: int
    type: str
    channel: Optional[str] = None
    subject: Optional[str] = None
    summary: Optional[str] = None
    date: str


class DealCreate(BaseModel):
    contact_id: Optional[int] = None
    organization_id: Optional[int] = None
    deal_name: str
    stage: str
    amount: Optional[str] = None
    probability: Optional[int] = None
    notes: Optional[str] = None


# ==================== CONTACTS ====================

@app.get("/api/contacts")
def list_contacts(
    auth=Depends(require_auth),
    category: Optional[str] = None,
    status: Optional[str] = None,
    tier: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = Query(default=200, le=500),
    offset: int = 0,
):
    with db() as conn:
        query = """
            SELECT c.*, o.name as organization_name
            FROM contacts c
            LEFT JOIN organizations o ON c.organization_id = o.id
            WHERE 1=1
        """
        params = {}
        if category:
            query += " AND c.category = :category"
            params["category"] = category
        if status:
            query += " AND c.status = :status"
            params["status"] = status
        if tier:
            query += " AND c.tier = :tier"
            params["tier"] = tier
        if search:
            query += """ AND (c.first_name || ' ' || COALESCE(c.last_name, '') LIKE :search
                OR c.email LIKE :search OR c.title LIKE :search OR c.notes LIKE :search
                OR o.name LIKE :search)"""
            params["search"] = f"%{search}%"
        query += " ORDER BY c.tier ASC, c.last_contact_date DESC LIMIT :lim OFFSET :off"
        params["lim"] = limit
        params["off"] = offset
        return rows_to_list(conn.execute(sqlalchemy.text(query), params).fetchall())


@app.get("/api/contacts/{contact_id}")
def get_contact(contact_id: int, auth=Depends(require_auth)):
    with db() as conn:
        row = conn.execute(sqlalchemy.text("""
            SELECT c.*, o.name as organization_name
            FROM contacts c
            LEFT JOIN organizations o ON c.organization_id = o.id
            WHERE c.id = :cid
        """), {"cid": contact_id}).fetchone()
        if not row:
            raise HTTPException(404, "Contact not found")
        contact = row_to_dict(row)
        contact["interactions"] = rows_to_list(
            conn.execute(sqlalchemy.text("SELECT * FROM interactions WHERE contact_id = :cid ORDER BY date DESC"), {"cid": contact_id}).fetchall()
        )
        contact["deals"] = rows_to_list(
            conn.execute(sqlalchemy.text("""SELECT d.*, o.name as org_name FROM deals d
                LEFT JOIN organizations o ON d.organization_id = o.id
                WHERE d.contact_id = :cid"""), {"cid": contact_id}).fetchall()
        )
        return contact


@app.post("/api/contacts", status_code=201)
def create_contact(data: ContactCreate, auth=Depends(require_auth)):
    with db() as conn:
        row = conn.execute(sqlalchemy.text("""
            INSERT INTO contacts (first_name,last_name,email,email_secondary,phone,phone_secondary,
                linkedin_url,organization_id,title,category,subcategory,status,tier,
                last_contact_date,next_action,next_action_date,notes)
            VALUES (:a,:b,:c,:d,:e,:f,:g,:h,:i,:j,:k,:l,:m,:n,:o,:p,:q)
            RETURNING id
        """), {"a":data.first_name,"b":data.last_name,"c":data.email,"d":data.email_secondary,
              "e":data.phone,"f":data.phone_secondary,"g":data.linkedin_url,"h":data.organization_id,
              "i":data.title,"j":data.category,"k":data.subcategory,"l":data.status,"m":data.tier,
              "n":data.last_contact_date,"o":data.next_action,"p":data.next_action_date,"q":data.notes}).fetchone()
        conn.commit()
        return {"id": row[0]}


@app.put("/api/contacts/{contact_id}")
def update_contact(contact_id: int, data: ContactUpdate, auth=Depends(require_auth)):
    with db() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT * FROM contacts WHERE id = :cid"), {"cid": contact_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Contact not found")
        updates = {k: v for k, v in data.dict().items() if v is not None}
        if not updates:
            return row_to_dict(existing)
        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = :val_{k}" for k in updates.keys())
        params = {f"val_{k}": v for k, v in updates.items()}
        params["cid"] = contact_id
        conn.execute(sqlalchemy.text(f"UPDATE contacts SET {set_clause} WHERE id = :cid"), params)
        conn.commit()
        return row_to_dict(conn.execute(sqlalchemy.text("SELECT * FROM contacts WHERE id = :cid"), {"cid": contact_id}).fetchone())


@app.delete("/api/contacts/{contact_id}")
def delete_contact(contact_id: int, auth=Depends(require_auth)):
    with db() as conn:
        conn.execute(sqlalchemy.text("DELETE FROM contacts WHERE id = :cid"), {"cid": contact_id})
        conn.commit()
        return {"deleted": contact_id}


# ==================== ORGANIZATIONS ====================

@app.get("/api/organizations")
def list_organizations(auth=Depends(require_auth)):
    with db() as conn:
        return rows_to_list(conn.execute(sqlalchemy.text("SELECT * FROM organizations ORDER BY name")).fetchall())


@app.get("/api/organizations/{org_id}")
def get_organization(org_id: int, auth=Depends(require_auth)):
    with db() as conn:
        org = conn.execute(sqlalchemy.text("SELECT * FROM organizations WHERE id = :oid"), {"oid": org_id}).fetchone()
        if not org:
            raise HTTPException(404, "Organization not found")
        result = row_to_dict(org)
        result["contacts"] = rows_to_list(
            conn.execute(sqlalchemy.text("SELECT * FROM contacts WHERE organization_id = :oid ORDER BY category, status"), {"oid": org_id}).fetchall()
        )
        return result


# ==================== INTERACTIONS ====================

@app.get("/api/interactions")
def list_interactions(contact_id: Optional[int] = None, limit: int = 50, auth=Depends(require_auth)):
    with db() as conn:
        if contact_id:
            return rows_to_list(conn.execute(sqlalchemy.text(
                "SELECT * FROM interactions WHERE contact_id = :cid ORDER BY date DESC LIMIT :lim"),
                {"cid": contact_id, "lim": limit}).fetchall())
        return rows_to_list(conn.execute(sqlalchemy.text(
            """SELECT i.*, c.first_name || ' ' || COALESCE(c.last_name, '') as contact_name
            FROM interactions i JOIN contacts c ON i.contact_id = c.id
            ORDER BY i.date DESC LIMIT :lim"""), {"lim": limit}).fetchall())


@app.post("/api/interactions", status_code=201)
def create_interaction(data: InteractionCreate, auth=Depends(require_auth)):
    with db() as conn:
        row = conn.execute(sqlalchemy.text("""INSERT INTO interactions (contact_id,type,channel,subject,summary,date)
            VALUES (:a,:b,:c,:d,:e,:f) RETURNING id"""),
            {"a":data.contact_id,"b":data.type,"c":data.channel,"d":data.subject,"e":data.summary,"f":data.date}).fetchone()
        conn.execute(sqlalchemy.text("UPDATE contacts SET last_contact_date = :dt, updated_at = :ua WHERE id = :cid"),
                     {"dt":data.date,"ua":datetime.now().isoformat(),"cid":data.contact_id})
        conn.commit()
        return {"id": row[0]}


# ==================== DEALS ====================

@app.get("/api/deals")
def list_deals(auth=Depends(require_auth)):
    with db() as conn:
        return rows_to_list(conn.execute(sqlalchemy.text("""
            SELECT d.*, c.first_name || ' ' || COALESCE(c.last_name, '') as contact_name,
                   o.name as org_name
            FROM deals d
            LEFT JOIN contacts c ON d.contact_id = c.id
            LEFT JOIN organizations o ON d.organization_id = o.id
            ORDER BY d.probability DESC
        """)).fetchall())


@app.post("/api/deals", status_code=201)
def create_deal(data: DealCreate, auth=Depends(require_auth)):
    with db() as conn:
        row = conn.execute(sqlalchemy.text("""INSERT INTO deals (contact_id,organization_id,deal_name,stage,amount,probability,notes)
            VALUES (:a,:b,:c,:d,:e,:f,:g) RETURNING id"""),
            {"a":data.contact_id,"b":data.organization_id,"c":data.deal_name,"d":data.stage,
             "e":data.amount,"f":data.probability,"g":data.notes}).fetchone()
        conn.commit()
        return {"id": row[0]}


# ==================== PROGRAMS ====================

@app.get("/api/programs")
def list_programs(auth=Depends(require_auth)):
    with db() as conn:
        return rows_to_list(conn.execute(sqlalchemy.text("""
            SELECT p.*, o.name as org_name,
                   c.first_name || ' ' || COALESCE(c.last_name, '') as contact_name
            FROM programs p
            LEFT JOIN organizations o ON p.organization_id = o.id
            LEFT JOIN contacts c ON p.primary_contact_id = c.id
            ORDER BY p.status, p.name
        """)).fetchall())


# ==================== STATS ====================

@app.get("/api/stats")
def get_stats(auth=Depends(require_auth)):
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


# ==================== STATIC FRONTEND ====================

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
