"""
BetterMind CRM - Category & Subcategory Routes
CRUD operations for dynamic category and subcategory management.
"""
import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException

from auth import require_auth
from deps import db, row_to_dict, rows_to_list

router = APIRouter(prefix="/api", tags=["categories"])


@router.get("/categories")
def list_categories(auth=Depends(require_auth)):
    """List all categories with their subcategories."""
    with db() as conn:
        cats = rows_to_list(conn.execute(sqlalchemy.text(
            "SELECT * FROM categories ORDER BY sort_order, name"
        )).fetchall())
        subs = rows_to_list(conn.execute(sqlalchemy.text(
            "SELECT * FROM subcategories ORDER BY sort_order, name"
        )).fetchall())
        # Group subcategories by category_id
        sub_map = {}
        for s in subs:
            sub_map.setdefault(s["category_id"], []).append(s)
        for cat in cats:
            cat["subcategories"] = sub_map.get(cat["id"], [])
        return cats


@router.get("/categories/{category_id}")
def get_category(category_id: int, auth=Depends(require_auth)):
    """Get a single category with its subcategories."""
    with db() as conn:
        row = conn.execute(sqlalchemy.text(
            "SELECT * FROM categories WHERE id = :cid"
        ), {"cid": category_id}).fetchone()
        if not row:
            raise HTTPException(404, "Category not found")
        cat = row_to_dict(row)
        cat["subcategories"] = rows_to_list(conn.execute(sqlalchemy.text(
            "SELECT * FROM subcategories WHERE category_id = :cid ORDER BY sort_order, name"
        ), {"cid": category_id}).fetchall())
        return cat


@router.post("/categories", status_code=201)
def create_category(data: dict, auth=Depends(require_auth)):
    """Create a new category."""
    name = (data.get("name") or "").strip().lower()
    display_name = (data.get("display_name") or "").strip()
    icon = (data.get("icon") or "📋").strip()
    sort_order = data.get("sort_order", 0)
    if not name:
        raise HTTPException(400, "Category name is required")
    if not display_name:
        display_name = name.title()
    with db() as conn:
        existing = conn.execute(sqlalchemy.text(
            "SELECT id FROM categories WHERE name = :n"
        ), {"n": name}).fetchone()
        if existing:
            raise HTTPException(409, f"Category '{name}' already exists")
        row = conn.execute(sqlalchemy.text(
            "INSERT INTO categories (name, display_name, icon, sort_order) VALUES (:n, :d, :i, :s) RETURNING id"
        ), {"n": name, "d": display_name, "i": icon, "s": sort_order}).fetchone()
        conn.commit()
        return {"id": row[0], "name": name, "display_name": display_name, "icon": icon, "sort_order": sort_order}


@router.put("/categories/{category_id}")
def update_category(category_id: int, data: dict, auth=Depends(require_auth)):
    """Update a category (name, display_name, icon, sort_order)."""
    with db() as conn:
        existing = conn.execute(sqlalchemy.text(
            "SELECT * FROM categories WHERE id = :cid"
        ), {"cid": category_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Category not found")
        updates = {}
        if "name" in data:
            updates["name"] = data["name"].strip().lower()
        if "display_name" in data:
            updates["display_name"] = data["display_name"].strip()
        if "icon" in data:
            updates["icon"] = data["icon"].strip()
        if "sort_order" in data:
            updates["sort_order"] = data["sort_order"]
        if not updates:
            return row_to_dict(existing)
        set_clause = ", ".join(f"{k} = :val_{k}" for k in updates)
        params = {f"val_{k}": v for k, v in updates.items()}
        params["cid"] = category_id
        conn.execute(sqlalchemy.text(
            f"UPDATE categories SET {set_clause} WHERE id = :cid"
        ), params)
        conn.commit()
        return row_to_dict(conn.execute(sqlalchemy.text(
            "SELECT * FROM categories WHERE id = :cid"
        ), {"cid": category_id}).fetchone())


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, auth=Depends(require_auth)):
    """Delete a category (only if no contacts use it)."""
    with db() as conn:
        cat = conn.execute(sqlalchemy.text(
            "SELECT * FROM categories WHERE id = :cid"
        ), {"cid": category_id}).fetchone()
        if not cat:
            raise HTTPException(404, "Category not found")
        cat_dict = row_to_dict(cat)
        # Check if any contacts reference this category
        count = conn.execute(sqlalchemy.text(
            "SELECT COUNT(*) FROM contacts WHERE category = :n"
        ), {"n": cat_dict["name"]}).fetchone()[0]
        if count > 0:
            raise HTTPException(
                409, f"Cannot delete category '{cat_dict['name']}': {count} contact(s) still use it"
            )
        conn.execute(sqlalchemy.text("DELETE FROM categories WHERE id = :cid"), {"cid": category_id})
        conn.commit()
        return {"deleted": category_id}


# ==================== SUBCATEGORIES ====================

@router.get("/subcategories")
def list_subcategories(auth=Depends(require_auth), category_id: int = None):
    """List all subcategories, optionally filtered by category_id."""
    with db() as conn:
        if category_id:
            return rows_to_list(conn.execute(sqlalchemy.text(
                "SELECT * FROM subcategories WHERE category_id = :cid ORDER BY sort_order, name"
            ), {"cid": category_id}).fetchall())
        return rows_to_list(conn.execute(sqlalchemy.text(
            "SELECT * FROM subcategories ORDER BY category_id, sort_order, name"
        )).fetchall())


@router.post("/subcategories", status_code=201)
def create_subcategory(data: dict, auth=Depends(require_auth)):
    """Create a new subcategory (requires category_id)."""
    category_id = data.get("category_id")
    name = (data.get("name") or "").strip()
    display_name = (data.get("display_name") or "").strip()
    sort_order = data.get("sort_order", 0)
    if not category_id:
        raise HTTPException(400, "category_id is required")
    if not name:
        raise HTTPException(400, "Subcategory name is required")
    if not display_name:
        display_name = name
    with db() as conn:
        cat = conn.execute(sqlalchemy.text(
            "SELECT id FROM categories WHERE id = :cid"
        ), {"cid": category_id}).fetchone()
        if not cat:
            raise HTTPException(404, f"Category with id {category_id} not found")
        existing = conn.execute(sqlalchemy.text(
            "SELECT id FROM subcategories WHERE category_id = :cid AND name = :n"
        ), {"cid": category_id, "n": name}).fetchone()
        if existing:
            raise HTTPException(409, f"Subcategory '{name}' already exists in this category")
        row = conn.execute(sqlalchemy.text(
            "INSERT INTO subcategories (category_id, name, display_name, sort_order) VALUES (:cid, :n, :d, :s) RETURNING id"
        ), {"cid": category_id, "n": name, "d": display_name, "s": sort_order}).fetchone()
        conn.commit()
        return {"id": row[0], "category_id": category_id, "name": name, "display_name": display_name, "sort_order": sort_order}


@router.put("/subcategories/{subcategory_id}")
def update_subcategory(subcategory_id: int, data: dict, auth=Depends(require_auth)):
    """Update a subcategory."""
    with db() as conn:
        existing = conn.execute(sqlalchemy.text(
            "SELECT * FROM subcategories WHERE id = :sid"
        ), {"sid": subcategory_id}).fetchone()
        if not existing:
            raise HTTPException(404, "Subcategory not found")
        updates = {}
        if "name" in data:
            updates["name"] = data["name"].strip()
        if "display_name" in data:
            updates["display_name"] = data["display_name"].strip()
        if "sort_order" in data:
            updates["sort_order"] = data["sort_order"]
        if "category_id" in data:
            cat = conn.execute(sqlalchemy.text(
                "SELECT id FROM categories WHERE id = :cid"
            ), {"cid": data["category_id"]}).fetchone()
            if not cat:
                raise HTTPException(404, f"Category with id {data['category_id']} not found")
            updates["category_id"] = data["category_id"]
        if not updates:
            return row_to_dict(existing)
        set_clause = ", ".join(f"{k} = :val_{k}" for k in updates)
        params = {f"val_{k}": v for k, v in updates.items()}
        params["sid"] = subcategory_id
        conn.execute(sqlalchemy.text(
            f"UPDATE subcategories SET {set_clause} WHERE id = :sid"
        ), params)
        conn.commit()
        return row_to_dict(conn.execute(sqlalchemy.text(
            "SELECT * FROM subcategories WHERE id = :sid"
        ), {"sid": subcategory_id}).fetchone())


@router.delete("/subcategories/{subcategory_id}")
def delete_subcategory(subcategory_id: int, auth=Depends(require_auth)):
    """Delete a subcategory (only if no contacts use it)."""
    with db() as conn:
        sub = conn.execute(sqlalchemy.text(
            "SELECT * FROM subcategories WHERE id = :sid"
        ), {"sid": subcategory_id}).fetchone()
        if not sub:
            raise HTTPException(404, "Subcategory not found")
        sub_dict = row_to_dict(sub)
        count = conn.execute(sqlalchemy.text(
            "SELECT COUNT(*) FROM contacts WHERE subcategory = :n"
        ), {"n": sub_dict["name"]}).fetchone()[0]
        if count > 0:
            raise HTTPException(
                409, f"Cannot delete subcategory '{sub_dict['name']}': {count} contact(s) still use it"
            )
        conn.execute(sqlalchemy.text("DELETE FROM subcategories WHERE id = :sid"), {"sid": subcategory_id})
        conn.commit()
        return {"deleted": subcategory_id}
