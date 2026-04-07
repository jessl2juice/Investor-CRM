"""
BetterMind CRM - Contact Routes
CRUD operations for contacts, bulk updates, and tag management.
"""
from datetime import datetime
from typing import Optional

import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException, Query

from auth import require_auth
from deps import db, row_to_dict, rows_to_list
from models import ContactCreate, ContactUpdate, BulkContactUpdate, TagCreate

router = APIRouter(prefix="/api", tags=["contacts"])


def _validate_category_subcategory(conn, category, subcategory=None):
    """Validate category/subcategory against the categories and subcategories tables."""
    if category is not None:
        cat_row = conn.execute(sqlalchemy.text(
            "SELECT id, name FROM categories WHERE name = :n"
        ), {"n": category}).fetchone()
        if not cat_row:
            valid = [r[0] for r in conn.execute(sqlalchemy.text(
                "SELECT name FROM categories ORDER BY sort_order"
            )).fetchall()]
            raise HTTPException(
                422, f"Invalid category '{category}'. Valid categories: {', '.join(valid)}"
            )
        if subcategory is not None:
            cat_id = cat_row[0]
            sub_row = conn.execute(sqlalchemy.text(
                "SELECT id FROM subcategories WHERE category_id = :cid AND name = :n"
            ), {"cid": cat_id, "n": subcategory}).fetchone()
            if not sub_row:
                valid_subs = [r[0] for r in conn.execute(sqlalchemy.text(
                    "SELECT name FROM subcategories WHERE category_id = :cid ORDER BY sort_order"
                ), {"cid": cat_id}).fetchall()]
                if valid_subs:
                    raise HTTPException(
                        422, f"Invalid subcategory '{subcategory}' for category '{category}'. "
                             f"Valid subcategories: {', '.join(valid_subs)}"
                    )
                else:
                    raise HTTPException(
                        422, f"Invalid subcategory '{subcategory}' for category '{category}'. "
                             f"This category has no defined subcategories."
                    )


CONTACT_COLUMNS = frozenset({
    "first_name", "last_name", "email", "email_secondary",
    "phone", "phone_secondary", "linkedin_url",
    "organization_id", "title", "category", "subcategory", "status",
    "tier", "last_contact_date", "next_action", "next_action_date", "notes",
    "address_line1", "address_line2", "city", "state", "zip",
    "country", "website", "twitter_url",
})


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
            query += """ AND (LOWER(c.first_name || ' ' || COALESCE(c.last_name, '')) LIKE :search
                OR LOWER(c.email) LIKE :search OR LOWER(c.title) LIKE :search
                OR LOWER(c.notes) LIKE :search OR LOWER(o.name) LIKE :search)"""
            params["search"] = f"%{search.lower()}%"
        query += " ORDER BY c.tier ASC, c.last_contact_date DESC LIMIT :lim OFFSET :off"
        params["lim"] = limit
        params["off"] = offset
        return rows_to_list(conn.execute(sqlalchemy.text(query), params).fetchall())


@router.get("/contacts/{contact_id}")
def get_contact(contact_id: int, auth=Depends(require_auth)):
    """Get a single contact with their interactions and deals."""
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


@router.post("/contacts", status_code=201)
def create_contact(data: ContactCreate, auth=Depends(require_auth)):
    """Create a new contact."""
    with db() as conn:
        _validate_category_subcategory(conn, data.category, data.subcategory)
        row = conn.execute(sqlalchemy.text("""
            INSERT INTO contacts (first_name,last_name,email,email_secondary,phone,phone_secondary,
                linkedin_url,organization_id,title,category,subcategory,status,tier,
                last_contact_date,next_action,next_action_date,notes,
                address_line1,address_line2,city,state,zip,country,website,twitter_url)
            VALUES (:first_name,:last_name,:email,:email_secondary,:phone,:phone_secondary,
                :linkedin_url,:organization_id,:title,:category,:subcategory,:status,:tier,
                :last_contact_date,:next_action,:next_action_date,:notes,
                :address_line1,:address_line2,:city,:state,:zip,:country,:website,:twitter_url)
            RETURNING id
        """), data.model_dump()).fetchone()
        conn.commit()
        return {"id": row[0]}


@router.put("/contacts/{contact_id}")
def update_contact(contact_id: int, data: ContactUpdate, auth=Depends(require_auth)):
    """Update a contact. Include only the fields you want to change."""
    with db() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT * FROM contacts WHERE id = :cid"), {"cid": contact_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Contact not found")
        dump = data.model_dump(exclude_unset=True)
        # Validate category/subcategory if either is being updated
        cat = dump.get("category", dict(existing._mapping).get("category"))
        sub = dump.get("subcategory", dict(existing._mapping).get("subcategory"))
        if "category" in dump or "subcategory" in dump:
            _validate_category_subcategory(conn, cat, sub)
        updates = {k: v for k, v in dump.items() if k in CONTACT_COLUMNS}
        if not updates:
            return row_to_dict(existing)
        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = :val_{k}" for k in updates.keys())
        params = {f"val_{k}": v for k, v in updates.items()}
        params["cid"] = contact_id
        conn.execute(sqlalchemy.text(f"UPDATE contacts SET {set_clause} WHERE id = :cid"), params)
        conn.commit()
        return row_to_dict(conn.execute(sqlalchemy.text("SELECT * FROM contacts WHERE id = :cid"), {"cid": contact_id}).fetchone())


@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, auth=Depends(require_auth)):
    """Delete a contact."""
    with db() as conn:
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
    with db() as conn:
        if data.category is not None:
            _validate_category_subcategory(conn, data.category)
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
    with db() as conn:
        return rows_to_list(conn.execute(sqlalchemy.text("SELECT * FROM tags ORDER BY name")).fetchall())


@router.post("/tags", status_code=201)
def create_tag(data: TagCreate, auth=Depends(require_auth)):
    """Create a new tag."""
    with db() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT id FROM tags WHERE name = :name"), {"name": data.name}).fetchone()
        if existing:
            raise HTTPException(409, "Tag already exists")
        row = conn.execute(sqlalchemy.text("INSERT INTO tags (name) VALUES (:name) RETURNING id"), {"name": data.name}).fetchone()
        conn.commit()
        return {"id": row[0], "name": data.name}


@router.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, auth=Depends(require_auth)):
    """Delete a tag and remove it from all contacts."""
    with db() as conn:
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
    with db() as conn:
        contact = conn.execute(sqlalchemy.text("SELECT id FROM contacts WHERE id = :cid"), {"cid": contact_id}).fetchone()
        if not contact:
            raise HTTPException(404, "Contact not found")
        return rows_to_list(conn.execute(sqlalchemy.text(
            "SELECT t.* FROM tags t JOIN contact_tags ct ON t.id = ct.tag_id WHERE ct.contact_id = :cid ORDER BY t.name"),
            {"cid": contact_id}).fetchall())


@router.post("/contacts/{contact_id}/tags/{tag_id}", status_code=201)
def add_tag_to_contact(contact_id: int, tag_id: int, auth=Depends(require_auth)):
    """Assign a tag to a contact."""
    with db() as conn:
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
    with db() as conn:
        deleted = conn.execute(sqlalchemy.text(
            "DELETE FROM contact_tags WHERE contact_id = :cid AND tag_id = :tid RETURNING contact_id"),
            {"cid": contact_id, "tid": tag_id}).fetchone()
        if not deleted:
            raise HTTPException(404, "Tag not assigned to this contact")
        conn.commit()
        return {"contact_id": contact_id, "tag_id": tag_id, "status": "removed"}
