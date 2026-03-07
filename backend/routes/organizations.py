"""
BetterMind CRM - Organization Routes
CRUD operations for organizations.
"""
import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException

from auth import require_auth
from deps import db, row_to_dict, rows_to_list
from models import OrganizationCreate, OrganizationUpdate

router = APIRouter(prefix="/api", tags=["organizations"])

ORG_COLUMNS = frozenset({
    "name", "type", "website", "phone", "city", "state",
    "focus_areas", "notes",
})


@router.get("/organizations")
def list_organizations(auth=Depends(require_auth)):
    """List all organizations ordered by name."""
    with db() as conn:
        return rows_to_list(conn.execute(sqlalchemy.text("SELECT * FROM organizations ORDER BY name")).fetchall())


@router.post("/organizations", status_code=201)
def create_organization(data: OrganizationCreate, auth=Depends(require_auth)):
    """Create a new organization."""
    with db() as conn:
        row = conn.execute(sqlalchemy.text(
            """INSERT INTO organizations (name,type,website,phone,city,state,focus_areas,notes)
            VALUES (:name,:type,:website,:phone,:city,:state,:focus_areas,:notes) RETURNING id"""),
            {"name":data.name,"type":data.type,"website":data.website,"phone":data.phone,
             "city":data.city,"state":data.state,"focus_areas":data.focus_areas,"notes":data.notes}).fetchone()
        conn.commit()
        return row_to_dict(conn.execute(sqlalchemy.text("SELECT * FROM organizations WHERE id = :oid"), {"oid": row[0]}).fetchone())


@router.get("/organizations/{org_id}")
def get_organization(org_id: int, auth=Depends(require_auth)):
    """Get an organization with its associated contacts."""
    with db() as conn:
        org = conn.execute(sqlalchemy.text("SELECT * FROM organizations WHERE id = :oid"), {"oid": org_id}).fetchone()
        if not org:
            raise HTTPException(404, "Organization not found")
        result = row_to_dict(org)
        result["contacts"] = rows_to_list(
            conn.execute(sqlalchemy.text("SELECT * FROM contacts WHERE organization_id = :oid ORDER BY category, status"), {"oid": org_id}).fetchall()
        )
        return result


@router.put("/organizations/{org_id}")
def update_organization(org_id: int, data: OrganizationUpdate, auth=Depends(require_auth)):
    """Update an organization. Include only the fields you want to change."""
    with db() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT * FROM organizations WHERE id = :oid"), {"oid": org_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Organization not found")
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if k in ORG_COLUMNS}
        if not updates:
            return row_to_dict(existing)
        set_clause = ", ".join(f"{k} = :val_{k}" for k in updates.keys())
        params = {f"val_{k}": v for k, v in updates.items()}
        params["oid"] = org_id
        conn.execute(sqlalchemy.text(f"UPDATE organizations SET {set_clause} WHERE id = :oid"), params)
        conn.commit()
        return row_to_dict(conn.execute(sqlalchemy.text("SELECT * FROM organizations WHERE id = :oid"), {"oid": org_id}).fetchone())


@router.delete("/organizations/{org_id}")
def delete_organization(org_id: int, auth=Depends(require_auth)):
    """Delete an organization. Unlinks associated contacts."""
    with db() as conn:
        existing = conn.execute(sqlalchemy.text("SELECT id FROM organizations WHERE id = :oid"), {"oid": org_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Organization not found")
        conn.execute(sqlalchemy.text("UPDATE contacts SET organization_id = NULL WHERE organization_id = :oid"), {"oid": org_id})
        conn.execute(sqlalchemy.text("DELETE FROM organizations WHERE id = :oid"), {"oid": org_id})
        conn.commit()
        return {"deleted": org_id}
