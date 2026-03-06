"""
BetterMind CRM - Interaction Routes
CRUD operations for interactions (emails, calls, meetings, notes).
"""
from datetime import datetime
from typing import Optional

import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException

from auth import require_auth
from models import InteractionCreate, InteractionUpdate

router = APIRouter(prefix="/api", tags=["interactions"])


def _db():
    from main import db
    return db


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row._mapping)


def _rows_to_list(rows):
    return [dict(r._mapping) for r in rows]


@router.get("/interactions")
def list_interactions(contact_id: Optional[int] = None, limit: int = 50, auth=Depends(require_auth)):
    """List interactions, optionally filtered by contact."""
    with _db()() as conn:
        if contact_id:
            return _rows_to_list(conn.execute(sqlalchemy.text(
                "SELECT * FROM interactions WHERE contact_id = :cid ORDER BY date DESC LIMIT :lim"),
                {"cid": contact_id, "lim": limit}).fetchall())
        return _rows_to_list(conn.execute(sqlalchemy.text(
            """SELECT i.*, c.first_name || ' ' || COALESCE(c.last_name, '') as contact_name
            FROM interactions i JOIN contacts c ON i.contact_id = c.id
            ORDER BY i.date DESC LIMIT :lim"""), {"lim": limit}).fetchall())


@router.post("/interactions", status_code=201)
def create_interaction(data: InteractionCreate, auth=Depends(require_auth)):
    """Log a new interaction and update the contact's last_contact_date."""
    with _db()() as conn:
        contact = conn.execute(sqlalchemy.text(
            "SELECT id FROM contacts WHERE id = :cid"), {"cid": data.contact_id}).fetchone()
        if not contact:
            raise HTTPException(404, f"Contact {data.contact_id} not found")
        try:
            row = conn.execute(sqlalchemy.text("""INSERT INTO interactions (contact_id,type,channel,subject,summary,date)
                VALUES (:a,:b,:c,:d,:e,:f) RETURNING id"""),
                {"a":data.contact_id,"b":data.type,"c":data.channel,"d":data.subject,"e":data.summary,"f":data.date}).fetchone()
            conn.execute(sqlalchemy.text("UPDATE contacts SET last_contact_date = :dt, updated_at = :ua WHERE id = :cid"),
                         {"dt":data.date,"ua":datetime.now().isoformat(),"cid":data.contact_id})
            conn.commit()
            return {"id": row[0]}
        except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.DatabaseError) as e:
            conn.rollback()
            raise HTTPException(422, f"Invalid data: {str(e.orig)}")


@router.get("/interactions/{interaction_id}")
def get_interaction(interaction_id: int, auth=Depends(require_auth)):
    """Get a single interaction."""
    with _db()() as conn:
        row = conn.execute(sqlalchemy.text("SELECT * FROM interactions WHERE id = :iid"), {"iid": interaction_id}).fetchone()
        if not row:
            raise HTTPException(404, "Interaction not found")
        return _row_to_dict(row)


@router.put("/interactions/{interaction_id}")
def update_interaction(interaction_id: int, data: InteractionUpdate, auth=Depends(require_auth)):
    """Update an interaction. Include only the fields you want to change."""
    with _db()() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT * FROM interactions WHERE id = :iid"), {"iid": interaction_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Interaction not found")
        ALLOWED_COLUMNS = {"type", "channel", "subject", "summary", "date"}
        updates = {k: v for k, v in data.dict(exclude_unset=True).items() if k in ALLOWED_COLUMNS}
        if not updates:
            return _row_to_dict(existing)
        set_clause = ", ".join(f"{k} = :val_{k}" for k in updates.keys())
        params = {f"val_{k}": v for k, v in updates.items()}
        params["iid"] = interaction_id
        try:
            conn.execute(sqlalchemy.text(f"UPDATE interactions SET {set_clause} WHERE id = :iid"), params)
            conn.commit()
            return _row_to_dict(conn.execute(sqlalchemy.text("SELECT * FROM interactions WHERE id = :iid"), {"iid": interaction_id}).fetchone())
        except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.DatabaseError) as e:
            conn.rollback()
            raise HTTPException(422, f"Invalid data: {str(e.orig)}")


@router.delete("/interactions/{interaction_id}")
def delete_interaction(interaction_id: int, auth=Depends(require_auth)):
    """Delete an interaction."""
    with _db()() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT id FROM interactions WHERE id = :iid"), {"iid": interaction_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Interaction not found")
        conn.execute(sqlalchemy.text("DELETE FROM interactions WHERE id = :iid"), {"iid": interaction_id})
        conn.commit()
        return {"deleted": interaction_id}
