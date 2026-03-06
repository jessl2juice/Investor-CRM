"""
BetterMind CRM - Deal Routes
CRUD operations for the fundraising pipeline.
"""
from datetime import datetime
from typing import Optional

import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException

from auth import require_auth
from models import DealCreate, DealUpdate

router = APIRouter(prefix="/api", tags=["deals"])


def _db():
    from main import db
    return db


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row._mapping)


def _rows_to_list(rows):
    return [dict(r._mapping) for r in rows]


@router.get("/deals")
def list_deals(stage: Optional[str] = None, contact_id: Optional[int] = None, auth=Depends(require_auth)):
    """List deals with optional filtering by stage or contact."""
    with _db()() as conn:
        query = """SELECT d.*, c.first_name || ' ' || COALESCE(c.last_name, '') as contact_name,
                   o.name as org_name
            FROM deals d
            LEFT JOIN contacts c ON d.contact_id = c.id
            LEFT JOIN organizations o ON d.organization_id = o.id"""
        conditions = []
        params = {}
        if stage:
            conditions.append("d.stage = :stage")
            params["stage"] = stage
        if contact_id:
            conditions.append("d.contact_id = :cid")
            params["cid"] = contact_id
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY d.probability DESC"
        return _rows_to_list(conn.execute(sqlalchemy.text(query), params).fetchall())


@router.post("/deals", status_code=201)
def create_deal(data: DealCreate, auth=Depends(require_auth)):
    """Create a new deal in the pipeline."""
    with _db()() as conn:
        row = conn.execute(sqlalchemy.text("""INSERT INTO deals (contact_id,organization_id,deal_name,stage,amount,probability,notes)
            VALUES (:a,:b,:c,:d,:e,:f,:g) RETURNING id"""),
            {"a":data.contact_id,"b":data.organization_id,"c":data.deal_name,"d":data.stage,
             "e":data.amount,"f":data.probability,"g":data.notes}).fetchone()
        conn.commit()
        return {"id": row[0]}


@router.get("/deals/{deal_id}")
def get_deal(deal_id: int, auth=Depends(require_auth)):
    """Get a single deal with contact and organization info."""
    with _db()() as conn:
        row = conn.execute(sqlalchemy.text("""
            SELECT d.*, c.first_name || ' ' || COALESCE(c.last_name, '') as contact_name,
                   o.name as org_name
            FROM deals d
            LEFT JOIN contacts c ON d.contact_id = c.id
            LEFT JOIN organizations o ON d.organization_id = o.id
            WHERE d.id = :did"""), {"did": deal_id}).fetchone()
        if not row:
            raise HTTPException(404, "Deal not found")
        return _row_to_dict(row)


@router.put("/deals/{deal_id}")
def update_deal(deal_id: int, data: DealUpdate, auth=Depends(require_auth)):
    """Update a deal. Include only the fields you want to change."""
    with _db()() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT * FROM deals WHERE id = :did"), {"did": deal_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Deal not found")
        ALLOWED_COLUMNS = {"contact_id", "organization_id", "deal_name", "stage", "amount", "probability", "notes"}
        updates = {k: v for k, v in data.dict(exclude_unset=True).items() if k in ALLOWED_COLUMNS}
        if not updates:
            return _row_to_dict(existing)
        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = :val_{k}" for k in updates.keys())
        params = {f"val_{k}": v for k, v in updates.items()}
        params["did"] = deal_id
        conn.execute(sqlalchemy.text(f"UPDATE deals SET {set_clause} WHERE id = :did"), params)
        conn.commit()
        return _row_to_dict(conn.execute(sqlalchemy.text("SELECT * FROM deals WHERE id = :did"), {"did": deal_id}).fetchone())


@router.delete("/deals/{deal_id}")
def delete_deal(deal_id: int, auth=Depends(require_auth)):
    """Delete a deal."""
    with _db()() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT id FROM deals WHERE id = :did"), {"did": deal_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Deal not found")
        conn.execute(sqlalchemy.text("DELETE FROM deals WHERE id = :did"), {"did": deal_id})
        conn.commit()
        return {"deleted": deal_id}
