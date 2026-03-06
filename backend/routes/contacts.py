"""
BetterMind CRM - Contact Routes
CRUD operations for contacts, bulk updates, and tag management.
"""
from datetime import datetime
from typing import Optional

import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException, Query

from auth import require_auth
from models import ContactCreate, ContactUpdate, BulkContactUpdate, TagCreate

router = APIRouter(prefix="/api", tags=["contacts"])


def _db():
    from main import db
    return db


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row._mapping)


def _rows_to_list(rows):
    return [dict(r._mapping) for r in rows]


@router.get("/contacts")
def list_contacts(
    auth=Depends(require_auth),
    category: Optional[str] = None,
    status: Optional[str] = None,
    tier: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = Query(default=200, le=500),
    offset: int = 0,
):
    """List contacts with optional filtering by category, status, tier, and full-text search."""
    with _db()() as conn:
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
        return _rows_to_list(conn.execute(sqlalchemy.text(query), params).fetchall())


@router.get("/contacts/{contact_id}")
def get_contact(contact_id: int, auth=Depends(require_auth)):
    """Get a single contact with their interactions and deals."""
    with _db()() as conn:
        row = conn.execute(sqlalchemy.text("""
            SELECT c.*, o.name as organization_name
            FROM contacts c
            LEFT JOIN organizations o ON c.organization_id = o.id
            WHERE c.id = :cid
        """), {"cid": contact_id}).fetchone()
        if not row:
            raise HTTPException(404, "Contact not found")
        contact = _row_to_dict(row)
        contact["interactions"] = _rows_to_list(
            conn.execute(sqlalchemy.text("SELECT * FROM interactions WHERE contact_id = :cid ORDER BY date DESC"), {"cid": contact_id}).fetchall()
        )
        contact["deals"] = _rows_to_list(
            conn.execute(sqlalchemy.text("""SELECT d.*, o.name as org_name FROM deals d
                LEFT JOIN organizations o ON d.organization_id = o.id
                WHERE d.contact_id = :cid"""), {"cid": contact_id}).fetchall()
        )
        return contact


@router.post("/contacts", status_code=201)
def create_contact(data: ContactCreate, auth=Depends(require_auth)):
    """Create a new contact."""
    with _db()() as conn:
        row = conn.execute(sqlalchemy.text("""
            INSERT INTO contacts (first_name,last_name,email,email_secondary,phone,phone_secondary,
                linkedin_url,organization_id,title,category,subcategory,status,tier,
                last_contact_date,next_action,next_action_date,notes,
                address_line1,address_line2,city,state,zip,country,website,twitter_url)
            VALUES (:a,:b,:c,:d,:e,:f,:g,:h,:i,:j,:k,:l,:m,:n,:o,:p,:q,
                :r,:s,:t,:u,:v,:w,:x,:y)
            RETURNING id
        """), {"a":data.first_name,"b":data.last_name,"c":data.email,"d":data.email_secondary,
              "e":data.phone,"f":data.phone_secondary,"g":data.linkedin_url,"h":data.organization_id,
              "i":data.title,"j":data.category,"k":data.subcategory,"l":data.status,"m":data.tier,
              "n":data.last_contact_date,"o":data.next_action,"p":data.next_action_date,"q":data.notes,
              "r":data.address_line1,"s":data.address_line2,"t":data.city,"u":data.state,
              "v":data.zip,"w":data.country,"x":data.website,"y":data.twitter_url}).fetchone()
        conn.commit()
        return {"id": row[0]}


@router.put("/contacts/{contact_id}")
def update_contact(contact_id: int, data: ContactUpdate, auth=Depends(require_auth)):
    """Update a contact. Include only the fields you want to change."""
    with _db()() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT * FROM contacts WHERE id = :cid"), {"cid": contact_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Contact not found")
        ALLOWED_COLUMNS = {
            "first_name", "last_name", "email", "email_secondary",
            "phone", "phone_secondary", "linkedin_url",
            "organization_id", "title", "category", "subcategory", "status",
            "tier", "last_contact_date", "next_action", "next_action_date", "notes",
            "address_line1", "address_line2", "city", "state", "zip",
            "country", "website", "twitter_url",
        }
        updates = {k: v for k, v in data.dict(exclude_unset=True).items() if k in ALLOWED_COLUMNS}
        if not updates:
            return _row_to_dict(existing)
        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = :val_{k}" for k in updates.keys())
        params = {f"val_{k}": v for k, v in updates.items()}
        params["cid"] = contact_id
        conn.execute(sqlalchemy.text(f"UPDATE contacts SET {set_clause} WHERE id = :cid"), params)
        conn.commit()
        return _row_to_dict(conn.execute(sqlalchemy.text("SELECT * FROM contacts WHERE id = :cid"), {"cid": contact_id}).fetchone())


@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, auth=Depends(require_auth)):
    """Delete a contact."""
    with _db()() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT id FROM contacts WHERE id = :cid"), {"cid": contact_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Contact not found")
        conn.execute(sqlalchemy.text("DELETE FROM contacts WHERE id = :cid"), {"cid": contact_id})
        conn.commit()
        return {"deleted": contact_id}


# ==================== BULK ====================

@router.put("/bulk/contacts")
def bulk_update_contacts(data: BulkContactUpdate, auth=Depends(require_auth)):
    """Bulk update status, category, or tier for multiple contacts."""
    if not data.contact_ids:
        raise HTTPException(400, "contact_ids must not be empty")
    updates = {}
    if data.status is not None:
        updates["status"] = data.status
    if data.category is not None:
        updates["category"] = data.category
    if data.tier is not None:
        updates["tier"] = data.tier
    if not updates:
        raise HTTPException(400, "No fields to update")
    updates["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k} = :val_{k}" for k in updates.keys())
    params = {f"val_{k}": v for k, v in updates.items()}
    with _db()() as conn:
        placeholders = ", ".join(f":id_{i}" for i in range(len(data.contact_ids)))
        for i, cid in enumerate(data.contact_ids):
            params[f"id_{i}"] = cid
        result = conn.execute(sqlalchemy.text(
            f"UPDATE contacts SET {set_clause} WHERE id IN ({placeholders})"), params)
        conn.commit()
        return {"updated": result.rowcount, "contact_ids": data.contact_ids}


# ==================== TAGS ====================

@router.get("/tags")
def list_tags(auth=Depends(require_auth)):
    """List all tags."""
    with _db()() as conn:
        return _rows_to_list(conn.execute(sqlalchemy.text("SELECT * FROM tags ORDER BY name")).fetchall())


@router.post("/tags", status_code=201)
def create_tag(data: TagCreate, auth=Depends(require_auth)):
    """Create a new tag."""
    with _db()() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT id FROM tags WHERE name = :name"), {"name": data.name}).fetchone()
        if existing:
            raise HTTPException(409, "Tag already exists")
        row = conn.execute(sqlalchemy.text("INSERT INTO tags (name) VALUES (:name) RETURNING id"), {"name": data.name}).fetchone()
        conn.commit()
        return {"id": row[0], "name": data.name}


@router.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, auth=Depends(require_auth)):
    """Delete a tag and remove it from all contacts."""
    with _db()() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT id FROM tags WHERE id = :tid"), {"tid": tag_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Tag not found")
        conn.execute(sqlalchemy.text("DELETE FROM contact_tags WHERE tag_id = :tid"), {"tid": tag_id})
        conn.execute(sqlalchemy.text("DELETE FROM tags WHERE id = :tid"), {"tid": tag_id})
        conn.commit()
        return {"deleted": tag_id}


@router.get("/contacts/{contact_id}/tags")
def get_contact_tags(contact_id: int, auth=Depends(require_auth)):
    """Get all tags for a contact."""
    with _db()() as conn:
        contact = conn.execute(sqlalchemy.text("SELECT id FROM contacts WHERE id = :cid"), {"cid": contact_id}).fetchone()
        if not contact:
            raise HTTPException(404, "Contact not found")
        return _rows_to_list(conn.execute(sqlalchemy.text(
            "SELECT t.* FROM tags t JOIN contact_tags ct ON t.id = ct.tag_id WHERE ct.contact_id = :cid ORDER BY t.name"),
            {"cid": contact_id}).fetchall())


@router.post("/contacts/{contact_id}/tags/{tag_id}", status_code=201)
def add_tag_to_contact(contact_id: int, tag_id: int, auth=Depends(require_auth)):
    """Assign a tag to a contact."""
    with _db()() as conn:
        contact = conn.execute(sqlalchemy.text("SELECT id FROM contacts WHERE id = :cid"), {"cid": contact_id}).fetchone()
        if not contact:
            raise HTTPException(404, "Contact not found")
        tag = conn.execute(sqlalchemy.text("SELECT id FROM tags WHERE id = :tid"), {"tid": tag_id}).fetchone()
        if not tag:
            raise HTTPException(404, "Tag not found")
        existing = conn.execute(sqlalchemy.text(
            "SELECT 1 FROM contact_tags WHERE contact_id = :cid AND tag_id = :tid"),
            {"cid": contact_id, "tid": tag_id}).fetchone()
        if existing:
            return {"contact_id": contact_id, "tag_id": tag_id, "status": "already_assigned"}
        conn.execute(sqlalchemy.text(
            "INSERT INTO contact_tags (contact_id, tag_id) VALUES (:cid, :tid)"),
            {"cid": contact_id, "tid": tag_id})
        conn.commit()
        return {"contact_id": contact_id, "tag_id": tag_id, "status": "assigned"}


@router.delete("/contacts/{contact_id}/tags/{tag_id}")
def remove_tag_from_contact(contact_id: int, tag_id: int, auth=Depends(require_auth)):
    """Remove a tag from a contact."""
    with _db()() as conn:
        deleted = conn.execute(sqlalchemy.text(
            "DELETE FROM contact_tags WHERE contact_id = :cid AND tag_id = :tid RETURNING contact_id"),
            {"cid": contact_id, "tid": tag_id}).fetchone()
        if not deleted:
            raise HTTPException(404, "Tag not assigned to this contact")
        conn.commit()
        return {"contact_id": contact_id, "tag_id": tag_id, "status": "removed"}
