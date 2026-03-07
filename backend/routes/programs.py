"""
BetterMind CRM - Program Routes
CRUD operations for programs and milestones.
"""
from typing import Optional

import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException

from auth import require_auth
from deps import db, row_to_dict, rows_to_list
from models import ProgramCreate, ProgramUpdate

router = APIRouter(prefix="/api", tags=["programs"])

PROGRAM_COLUMNS = frozenset({"name", "organization_id", "status", "start_date", "end_date", "value", "primary_contact_id", "notes"})


@router.get("/programs")
def list_programs(status: Optional[str] = None, auth=Depends(require_auth)):
    """List programs with optional status filtering."""
    with db() as conn:
        query = """SELECT p.*, o.name as org_name,
                   c.first_name || ' ' || COALESCE(c.last_name, '') as contact_name
            FROM programs p
            LEFT JOIN organizations o ON p.organization_id = o.id
            LEFT JOIN contacts c ON p.primary_contact_id = c.id"""
        params = {}
        if status:
            query += " WHERE p.status = :status"
            params["status"] = status
        query += " ORDER BY p.status, p.name"
        return rows_to_list(conn.execute(sqlalchemy.text(query), params).fetchall())


@router.post("/programs", status_code=201)
def create_program(data: ProgramCreate, auth=Depends(require_auth)):
    """Create a new program."""
    with db() as conn:
        row = conn.execute(sqlalchemy.text(
            """INSERT INTO programs (name,organization_id,status,start_date,end_date,value,primary_contact_id,notes)
            VALUES (:name,:org_id,:status,:start,:end,:value,:contact_id,:notes) RETURNING id"""),
            {"name":data.name,"org_id":data.organization_id,"status":data.status,
             "start":data.start_date,"end":data.end_date,"value":data.value,
             "contact_id":data.primary_contact_id,"notes":data.notes}).fetchone()
        conn.commit()
        return row_to_dict(conn.execute(sqlalchemy.text("SELECT * FROM programs WHERE id = :pid"), {"pid": row[0]}).fetchone())


@router.get("/programs/{program_id}")
def get_program(program_id: int, auth=Depends(require_auth)):
    """Get a single program with organization and contact info."""
    with db() as conn:
        row = conn.execute(sqlalchemy.text("""
            SELECT p.*, o.name as org_name,
                   c.first_name || ' ' || COALESCE(c.last_name, '') as contact_name
            FROM programs p
            LEFT JOIN organizations o ON p.organization_id = o.id
            LEFT JOIN contacts c ON p.primary_contact_id = c.id
            WHERE p.id = :pid"""), {"pid": program_id}).fetchone()
        if not row:
            raise HTTPException(404, "Program not found")
        return row_to_dict(row)


@router.put("/programs/{program_id}")
def update_program(program_id: int, data: ProgramUpdate, auth=Depends(require_auth)):
    """Update a program. Include only the fields you want to change."""
    with db() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT * FROM programs WHERE id = :pid"), {"pid": program_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Program not found")
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if k in PROGRAM_COLUMNS}
        if not updates:
            return row_to_dict(existing)
        set_clause = ", ".join(f"{k} = :val_{k}" for k in updates.keys())
        params = {f"val_{k}": v for k, v in updates.items()}
        params["pid"] = program_id
        conn.execute(sqlalchemy.text(f"UPDATE programs SET {set_clause} WHERE id = :pid"), params)
        conn.commit()
        return row_to_dict(conn.execute(sqlalchemy.text("SELECT * FROM programs WHERE id = :pid"), {"pid": program_id}).fetchone())


@router.delete("/programs/{program_id}")
def delete_program(program_id: int, auth=Depends(require_auth)):
    """Delete a program."""
    with db() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT id FROM programs WHERE id = :pid"), {"pid": program_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Program not found")
        conn.execute(sqlalchemy.text("DELETE FROM programs WHERE id = :pid"), {"pid": program_id})
        conn.commit()
        return {"deleted": program_id}
