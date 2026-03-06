"""
BetterMind CRM - Shared Dependencies
Database context manager and row conversion helpers used by all route modules.
"""
from contextlib import contextmanager

from fastapi import HTTPException

from database import get_engine


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
