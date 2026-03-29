#!/usr/bin/env python3
"""
Import BetterMind CRM data from JSON backup into local PostgreSQL.
Run AFTER docker-compose up (database must be running).

Usage:
  1. Extract crm-complete-backup.tar.gz into this directory
  2. docker-compose up -d
  3. Wait 5 seconds for PostgreSQL to be ready
  4. python import_data.py
"""
import json
import os
import sys
import time

# Add backend to path so we can import database.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

os.environ.setdefault('DATABASE_URL', 'postgresql+pg8000://bettermind:BM_local_2026_secure!@localhost:5433/bettermind_crm')

import sqlalchemy
from database import get_engine, init_schema, hash_password


def load_json(filename):
    with open(filename, encoding='utf-8') as f:
        return json.loads(f.read(), strict=False)


def main():
    print("Connecting to PostgreSQL...")
    engine = get_engine()

    # Retry connection for up to 30 seconds
    for attempt in range(30):
        try:
            with engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))
            break
        except Exception:
            print(f"  Waiting for database... ({attempt+1}s)")
            time.sleep(1)
    else:
        print("ERROR: Could not connect to PostgreSQL after 30 seconds")
        sys.exit(1)

    with engine.connect() as conn:
        print("Initializing schema...")
        init_schema(conn)

        # Check if data already exists
        count = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM organizations")).fetchone()[0]
        if count > 0:
            print(f"Database already has {count} organizations. Skipping import.")
            print("To re-import, drop and recreate the database:")
            print("  docker-compose down -v && docker-compose up -d")
            sys.exit(0)

        # === ORGANIZATIONS ===
        orgs = load_json('orgs_full.json')
        print(f"Importing {len(orgs)} organizations...")
        org_cols = ['id', 'name', 'type', 'website', 'phone', 'city', 'state', 'focus_areas', 'notes', 'created_at']
        for o in orgs:
            vals = {c: o.get(c) for c in org_cols}
            placeholders = ', '.join(f':{c}' for c in org_cols)
            col_names = ', '.join(org_cols)
            conn.execute(sqlalchemy.text(f"INSERT INTO organizations ({col_names}) VALUES ({placeholders})"), vals)

        # === CONTACTS ===
        contacts = load_json('contacts_full.json')
        print(f"Importing {len(contacts)} contacts...")
        contact_cols = [
            'id', 'first_name', 'last_name', 'email', 'email_secondary',
            'phone', 'phone_secondary', 'linkedin_url', 'organization_id',
            'title', 'category', 'subcategory', 'status', 'tier',
            'last_contact_date', 'next_action', 'next_action_date', 'notes',
            'address_line1', 'address_line2', 'city', 'state', 'zip',
            'country', 'website', 'twitter_url', 'created_at', 'updated_at'
        ]
        for c in contacts:
            vals = {col: c.get(col) for col in contact_cols}
            placeholders = ', '.join(f':{col}' for col in contact_cols)
            col_names = ', '.join(contact_cols)
            conn.execute(sqlalchemy.text(f"INSERT INTO contacts ({col_names}) VALUES ({placeholders})"), vals)

        # === INTERACTIONS ===
        interactions = load_json('interactions_full.json')
        print(f"Importing {len(interactions)} interactions...")
        ix_cols = ['id', 'contact_id', 'type', 'channel', 'subject', 'summary', 'date', 'created_at']
        for ix in interactions:
            vals = {col: ix.get(col) for col in ix_cols}
            placeholders = ', '.join(f':{col}' for col in ix_cols)
            col_names = ', '.join(ix_cols)
            conn.execute(sqlalchemy.text(f"INSERT INTO interactions ({col_names}) VALUES ({placeholders})"), vals)

        # === DEALS ===
        deals = load_json('deals_full.json')
        print(f"Importing {len(deals)} deals...")
        deal_cols = ['id', 'contact_id', 'organization_id', 'deal_name', 'stage', 'amount', 'probability', 'notes', 'created_at', 'updated_at']
        for d in deals:
            vals = {col: d.get(col) for col in deal_cols}
            placeholders = ', '.join(f':{col}' for col in deal_cols)
            col_names = ', '.join(deal_cols)
            conn.execute(sqlalchemy.text(f"INSERT INTO deals ({col_names}) VALUES ({placeholders})"), vals)

        # === PROGRAMS ===
        programs = load_json('programs_full.json')
        print(f"Importing {len(programs)} programs...")
        prog_cols = ['id', 'name', 'organization_id', 'status', 'start_date', 'end_date', 'value', 'primary_contact_id', 'notes', 'created_at']
        for p in programs:
            vals = {col: p.get(col) for col in prog_cols}
            placeholders = ', '.join(f':{col}' for col in prog_cols)
            col_names = ', '.join(prog_cols)
            conn.execute(sqlalchemy.text(f"INSERT INTO programs ({col_names}) VALUES ({placeholders})"), vals)

        # === TAGS ===
        tags = load_json('tags_full.json')
        print(f"Importing {len(tags)} tags...")
        for t in tags:
            conn.execute(sqlalchemy.text("INSERT INTO tags (id, name) VALUES (:id, :name)"), {"id": t["id"], "name": t["name"]})

        # === RESET SEQUENCES ===
        print("Resetting PostgreSQL sequences...")
        for table in ['organizations', 'contacts', 'interactions', 'deals', 'programs', 'tags']:
            conn.execute(sqlalchemy.text(f"SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1))"))

        # === USERS ===
        print("Creating user accounts...")
        users_to_create = [
            ("jess@clinicianassist.ai", "Onelongpassword!", "Jess Jessop", "admin"),
            ("tommy@ctrl-drive.com", "BM_user_2026!", "Tommy Stiansen", "user"),
            ("chris@modularfeedback.com", "BM_user_2026!", "Chris Hemphill", "user"),
            ("jeaninecmartin@gmail.com", "BM_user_2026!", "Jeanine Martin", "user"),
            ("kimmitchellpotter@gmail.com", "BM_user_2026!", "Kimberly Potter", "user"),
            ("brian@outrigger.group", "BM_user_2026!", "Brian Peterson", "user"),
            ("dan@heyjoyful.com", "BM_user_2026!", "Dan Wu", "user"),
        ]
        for email, password, name, role in users_to_create:
            pw_hash, pw_salt = hash_password(password)
            conn.execute(sqlalchemy.text(
                "INSERT INTO users (email, password_hash, password_salt, name, role) VALUES (:e, :h, :s, :n, :r)"
            ), {"e": email, "h": pw_hash, "s": pw_salt, "n": name, "r": role})

        conn.execute(sqlalchemy.text("SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1))"))

        conn.commit()

        # === VERIFY ===
        print("\n=== IMPORT COMPLETE ===")
        for table in ['organizations', 'contacts', 'interactions', 'deals', 'programs', 'tags', 'users']:
            count = conn.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
            print(f"  {table}: {count} records")

        print("\nDone! CRM is ready at http://localhost:8080")
        print("Login: jess@clinicianassist.ai / Onelongpassword!")


if __name__ == '__main__':
    main()
