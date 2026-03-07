"""
BetterMind CRM Database — Schema & Seed Data (PostgreSQL via Cloud SQL)
Run directly to initialize: python database.py
"""
import hashlib
import hmac
import os
import secrets
from datetime import datetime

import sqlalchemy

# Cloud SQL connection config
INSTANCE_CONNECTION_NAME = os.environ.get("INSTANCE_CONNECTION_NAME", "")
DB_USER = os.environ.get("DB_USER", "")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# For local dev fallback to SQLite
USE_POSTGRES = bool(INSTANCE_CONNECTION_NAME) or bool(DATABASE_URL)

if INSTANCE_CONNECTION_NAME:
    from google.cloud.sql.connector import Connector

_connector = None
_engine = None


def _get_connector():
    global _connector
    if _connector is None:
        _connector = Connector()
    return _connector


def _get_pg_engine():
    global _engine
    if _engine is not None:
        return _engine

    connector = _get_connector()

    def getconn():
        return connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
        )

    _engine = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
    )
    return _engine


def _get_sqlite_engine():
    global _engine
    if _engine is not None:
        return _engine
    db_path = os.path.join(os.path.dirname(__file__), "bettermind_crm.db")
    _engine = sqlalchemy.create_engine(f"sqlite:///{db_path}")
    return _engine


def _get_direct_pg_engine():
    global _engine
    if _engine is not None:
        return _engine
    _engine = sqlalchemy.create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
    )
    return _engine


def get_engine():
    if DATABASE_URL:
        return _get_direct_pg_engine()
    if INSTANCE_CONNECTION_NAME:
        return _get_pg_engine()
    return _get_sqlite_engine()


def get_connection():
    return get_engine().connect()


def init_schema(conn):
    if USE_POSTGRES:
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS organizations (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT CHECK(type IN (
                'vc_firm','cvc','accelerator','tech_company','university',
                'hospital_system','consulting','startup','media','government','other'
            )),
            website TEXT,
            phone TEXT,
            city TEXT,
            state TEXT,
            focus_areas TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (now()::text)
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT,
            email TEXT,
            email_secondary TEXT,
            phone TEXT,
            phone_secondary TEXT,
            linkedin_url TEXT,
            organization_id INTEGER REFERENCES organizations(id),
            title TEXT,
            category TEXT NOT NULL CHECK(category IN (
                'investor','google','team','advisor','partner',
                'vendor','university','media','accelerator','other'
            )),
            subcategory TEXT,
            status TEXT NOT NULL CHECK(status IN (
                'active','diligence','outreach','follow_up','scheduled',
                'passed','connected','recruiting','searching','contact','cold'
            )),
            tier INTEGER CHECK(tier BETWEEN 1 AND 4),
            last_contact_date TEXT,
            next_action TEXT,
            next_action_date TEXT,
            notes TEXT,
            address_line1 TEXT,
            address_line2 TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            country TEXT DEFAULT 'US',
            website TEXT,
            twitter_url TEXT,
            created_at TEXT DEFAULT (now()::text),
            updated_at TEXT DEFAULT (now()::text)
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS interactions (
            id SERIAL PRIMARY KEY,
            contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
            type TEXT NOT NULL CHECK(type IN (
                'email_sent','email_received','email','linkedin_dm','linkedin_connect',
                'meeting','meeting_scheduled','call','intro','follow_up','pitch',
                'note','demo','webinar','event','referral','other'
            )),
            channel TEXT CHECK(channel IN (
                'email','linkedin','phone','zoom','google_meet','in_person',
                'slack','calendly','twitter','text','teams','other'
            )),
            subject TEXT,
            summary TEXT,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT (now()::text)
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS deals (
            id SERIAL PRIMARY KEY,
            contact_id INTEGER REFERENCES contacts(id),
            organization_id INTEGER REFERENCES organizations(id),
            deal_name TEXT NOT NULL,
            stage TEXT CHECK(stage IN (
                'identified','outreach','meeting','diligence','term_sheet',
                'closed','passed','dead'
            )),
            amount TEXT,
            probability INTEGER CHECK(probability BETWEEN 0 AND 100),
            notes TEXT,
            created_at TEXT DEFAULT (now()::text),
            updated_at TEXT DEFAULT (now()::text)
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS programs (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            organization_id INTEGER REFERENCES organizations(id),
            status TEXT CHECK(status IN ('active','applied','accepted','complete','planning')),
            start_date TEXT,
            end_date TEXT,
            value TEXT,
            primary_contact_id INTEGER REFERENCES contacts(id),
            notes TEXT,
            created_at TEXT DEFAULT (now()::text)
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS tags (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS contact_tags (
            contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
            tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (contact_id, tag_id)
        )"""))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_contacts_category ON contacts(category)"))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status)"))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_contacts_org ON contacts(organization_id)"))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_interactions_contact ON interactions(contact_id)"))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_interactions_date ON interactions(date)"))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_deals_stage ON deals(stage)"))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'user',
            created_at TEXT DEFAULT (now()::text)
        )"""))
        # Migrate existing CHECK constraints to expanded values
        conn.execute(sqlalchemy.text("""
            ALTER TABLE interactions DROP CONSTRAINT IF EXISTS interactions_type_check"""))
        conn.execute(sqlalchemy.text("""
            ALTER TABLE interactions ADD CONSTRAINT interactions_type_check CHECK(type IN (
                'email_sent','email_received','email','linkedin_dm','linkedin_connect',
                'meeting','meeting_scheduled','call','intro','follow_up','pitch',
                'note','demo','webinar','event','referral','other'
            ))"""))
        conn.execute(sqlalchemy.text("""
            ALTER TABLE interactions DROP CONSTRAINT IF EXISTS interactions_channel_check"""))
        conn.execute(sqlalchemy.text("""
            ALTER TABLE interactions ADD CONSTRAINT interactions_channel_check CHECK(channel IN (
                'email','linkedin','phone','zoom','google_meet','in_person',
                'slack','calendly','twitter','text','teams','other'
            ))"""))
        for col, default in [
            ("address_line1", None), ("address_line2", None), ("city", None),
            ("state", None), ("zip", None), ("country", "'US'"),
            ("website", None), ("twitter_url", None),
        ]:
            default_clause = f" DEFAULT {default}" if default else ""
            conn.execute(sqlalchemy.text(
                f"ALTER TABLE contacts ADD COLUMN IF NOT EXISTS {col} TEXT{default_clause}"))
        conn.commit()
    else:
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            website TEXT,
            phone TEXT,
            city TEXT,
            state TEXT,
            focus_areas TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            email TEXT,
            email_secondary TEXT,
            phone TEXT,
            phone_secondary TEXT,
            linkedin_url TEXT,
            organization_id INTEGER REFERENCES organizations(id),
            title TEXT,
            category TEXT NOT NULL,
            subcategory TEXT,
            status TEXT NOT NULL,
            tier INTEGER,
            last_contact_date TEXT,
            next_action TEXT,
            next_action_date TEXT,
            notes TEXT,
            address_line1 TEXT,
            address_line2 TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            country TEXT DEFAULT 'US',
            website TEXT,
            twitter_url TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
            type TEXT NOT NULL CHECK(type IN (
                'email_sent','email_received','email','linkedin_dm','linkedin_connect',
                'meeting','meeting_scheduled','call','intro','follow_up','pitch',
                'note','demo','webinar','event','referral','other'
            )),
            channel TEXT CHECK(channel IN (
                'email','linkedin','phone','zoom','google_meet','in_person',
                'slack','calendly','twitter','text','teams','other'
            )),
            subject TEXT,
            summary TEXT,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER REFERENCES contacts(id),
            organization_id INTEGER REFERENCES organizations(id),
            deal_name TEXT NOT NULL,
            stage TEXT,
            amount TEXT,
            probability INTEGER,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            organization_id INTEGER REFERENCES organizations(id),
            status TEXT,
            start_date TEXT,
            end_date TEXT,
            value TEXT,
            primary_contact_id INTEGER REFERENCES contacts(id),
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS contact_tags (
            contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
            tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (contact_id, tag_id)
        )"""))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_contacts_category ON contacts(category)"))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status)"))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_contacts_org ON contacts(organization_id)"))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_interactions_contact ON interactions(contact_id)"))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_interactions_date ON interactions(date)"))
        conn.execute(sqlalchemy.text("CREATE INDEX IF NOT EXISTS idx_deals_stage ON deals(stage)"))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'user',
            created_at TEXT DEFAULT (datetime('now'))
        )"""))
        for col in ["address_line1", "address_line2", "city", "state", "zip",
                     "country", "website", "twitter_url"]:
            try:
                default = " DEFAULT 'US'" if col == "country" else ""
                conn.execute(sqlalchemy.text(f"ALTER TABLE contacts ADD COLUMN {col} TEXT{default}"))
            except Exception:
                pass
        conn.commit()


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations=600_000).hex()
    return h, salt


def verify_password(password, stored_hash, salt):
    """Verify password against stored hash. Supports both legacy SHA-256 and new PBKDF2."""
    # Try new PBKDF2 format first
    pbkdf2_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations=600_000).hex()
    if hmac.compare_digest(pbkdf2_hash, stored_hash):
        return True
    # Fall back to legacy single SHA-256 for old hashes
    legacy_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return hmac.compare_digest(legacy_hash, stored_hash)


def seed_data(conn):
    """Seed demo data for development and testing. All data is fictional."""
    result = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM organizations"))
    if result.fetchone()[0] > 0:
        return

    orgs = [
        ('Horizon Ventures','vc_firm','https://example.com/horizon',None,'San Francisco','CA','Consumer, community, marketplace','Demo VC firm. Series A focus.'),
        ('Cascade Partners','vc_firm','https://example.com/cascade',None,'San Francisco','CA','Healthcare, enterprise, consumer',None),
        ('Summit Capital','vc_firm','https://example.com/summit',None,'Menlo Park','CA','Bio+Health, AI, fintech',None),
        ('Vanguard Fund','vc_firm','https://example.com/vanguard',None,'San Francisco','CA','Deep tech, biotech, AI',None),
        ('Atlas Ventures','cvc','https://example.com/atlas',None,'Mountain View','CA','Life science, health, AI',None),
        ('Pinnacle Ventures','vc_firm','https://example.com/pinnacle',None,'Menlo Park','CA','Health, AI, sustainability',None),
        ('Frontier Capital','vc_firm','https://example.com/frontier',None,'Menlo Park','CA','Deep tech, science, frontier','Early stage deep tech focus.'),
        ('Waypoint Ventures','vc_firm','https://example.com/waypoint',None,'San Francisco','CA','Consumer',None),
        ('Meridian Health Fund','vc_firm','https://example.com/meridian',None,'Chicago','IL','Digital health',None),
        ('Launchpad Associates','vc_firm','https://example.com/launchpad',None,'San Mateo','CA','Early stage, disruptive tech',None),
        ('Nexus Fund','vc_firm','https://example.com/nexus',None,'Cambridge','MA','Seed, university-adjacent',None),
        ('Acme Cloud','tech_company','https://example.com/cloud','(555) 100-2000','Mountain View','CA','Cloud, AI, ML, startups','Cloud startup program partner.'),
        ('Cloudbridge Consulting','consulting','https://example.com/cloudbridge',None,None,None,'Cloud consulting','Cloud consulting partner.'),
        ('InfraPro','consulting','https://example.com/infrapro',None,None,None,'DevOps, cloud infrastructure','DevOps infrastructure partner.'),
        ('DemoHealth Inc.','startup','https://example.com/demohealth','(555) 867-5309','Portland','OR','AI health technology','Demo startup company.'),
        ('Pacific State University','university','https://example.com/psu',None,'San Jose','CA',None,'First campus pilot target.'),
        ('Bay Area University','university','https://example.com/bau',None,'Oakland','CA',None,'Second campus pilot target.'),
        ('Western Tech University','university','https://example.com/wtu',None,'Berkeley','CA',None,'Third campus pilot target.'),
        ('Resonance Health','startup','https://example.com/resonance',None,None,None,'Voice biomarkers, health AI',None),
        ('Helix Group','consulting','https://example.com/helix',None,None,None,'Healthcare IT, EMR development',None),
        ('Acme Research','tech_company','https://example.com/research',None,'London',None,'AI research',None),
    ]
    for o in orgs:
        conn.execute(sqlalchemy.text(
            "INSERT INTO organizations (name,type,website,phone,city,state,focus_areas,notes) VALUES (:a,:b,:c,:d,:e,:f,:g,:h)"
        ), {"a":o[0],"b":o[1],"c":o[2],"d":o[3],"e":o[4],"f":o[5],"g":o[6],"h":o[7]})

    rows = conn.execute(sqlalchemy.text("SELECT id, name FROM organizations")).fetchall()
    om = {name: oid for oid, name in rows}

    contacts = [
        ('Marcus','Chen','marcus.chen@example.com',None,'555-100-0001',None,'linkedin.com/in/example-mchen',om['Horizon Ventures'],'General Partner','investor','Tier 1 VC','diligence',1,'2026-02-12','Follow up on diligence','2026-02-20','Interested in mission. Wants to see team growth.'),
        ('Elena','Vasquez','elena.v@example.com',None,None,None,'linkedin.com/in/example-evasquez',om['Cascade Partners'],'Partner','investor','Series A VC','active',1,'2026-02-11','Follow up on diligence package','2026-02-18','Full diligence package sent. Met at healthcare conference.'),
        ('James','Whitfield',None,None,None,None,None,om['Nexus Fund'],'Partner','investor','Seed VC','outreach',1,'2026-02-11','Follow up','2026-02-18','Outreach email sent.'),
        ('Priya','Sharma','priya.s@example.com',None,None,None,None,om['Summit Capital'],'Partner','investor','Mega VC','follow_up',1,'2026-02-10','Follow up on pitch',None,'Initial pitch sent. Regulatory angle.'),
        ('David','Park','david.p@example.com',None,None,None,None,om['Vanguard Fund'],'Partner','investor','Mega VC','follow_up',1,'2026-02-10','Follow up',None,'Follow-up on deep tech thesis.'),
        ('Dr. Sarah','Kim','sarah.kim@example.com',None,None,None,None,om['Atlas Ventures'],'Partner','investor','CVC','follow_up',1,'2026-02-10',None,None,None),
        ('Dr. Michael','Torres',None,None,None,None,None,om['Pinnacle Ventures'],'Partner','investor','Mega VC','follow_up',1,'2026-02-10',None,None,None),
        ('Dr. Rachel','Nguyen',None,None,None,None,None,om['Pinnacle Ventures'],'Partner','investor','Mega VC','follow_up',1,'2026-02-10',None,None,None),
        ('Nathan','Brooks',None,None,None,None,None,om['Meridian Health Fund'],'Partner','investor','Health VC','outreach',1,'2026-02-10','Follow up on email',None,'Initial outreach sent.'),
        ('Amy','Liu',None,None,None,None,None,om['Launchpad Associates'],None,'investor','Seed VC','outreach',2,'2026-02-10',None,None,'LinkedIn outreach sent.'),
        ('Ricardo',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM sent.'),
        ('Tanaka','Hiroshi',None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM sent.'),
        ('Wells',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM sent.'),
        ('Larsson',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM sent.'),
        ('Okafor',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM sent.'),
        ('Mehta',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM sent.'),
        ('Fischer',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM sent.'),
        ('Reeves',None,None,None,None,None,None,None,None,'investor',None,'scheduled',2,'2026-02-12','LinkedIn outreach',None,'Outreach sent.'),
        ('Campbell',None,None,None,None,None,None,None,None,'investor',None,'scheduled',2,'2026-02-12','LinkedIn outreach',None,'Outreach sent.'),
        ('Jordan',None,None,None,None,None,None,None,None,'investor',None,'scheduled',2,'2026-02-13','Outreach',None,'Scheduled outreach.'),
        ('Robert','Langford',None,None,None,None,'linkedin.com/in/example-rlangford',om['Frontier Capital'],'Founder/Partner','investor','Deep Tech VC','passed',1,'2026-02-01',None,None,'Long relationship. Passed on current round.'),
        ('Laura','Bennett',None,None,None,None,None,om['Waypoint Ventures'],'Founder/Partner','investor','Consumer VC','passed',1,'2026-02-01',None,None,'Passed.'),
        ('Chris','Donovan',None,None,None,None,None,None,'Family Office Network','investor','Family Office','scheduled',2,'2026-02-25','Intro meeting Feb 25','2026-02-25','Intro meeting scheduled.'),
        ('Sofia','Ramirez','sofia.r@example.com',None,'555-200-0001',None,None,om['Acme Cloud'],'Account Manager','google','Cloud Program','active',None,'2026-02-12','Schedule meeting','2026-02-14','Primary cloud contact. Active program support.'),
        ('Arjun','Patel','arjun.p@example.com',None,None,None,None,om['Acme Cloud'],'Startup Program','google','Cloud Program','active',None,'2025-09-11','Re-engage with update',None,'Getting started call completed.'),
        ('Lena','Muller','lena.m@example.com',None,None,None,None,om['Acme Cloud'],'Startup Program','google','Cloud Program','contact',None,'2025-07-07',None,None,'Organized first program meeting.'),
        ('Anika','Desai','anika.d@example.com',None,None,None,None,om['Acme Cloud'],'Startup Program','google','Cloud Program','contact',None,'2025-07-07',None,None,'Attended onboarding call.'),
        ('Kai','Tanaka','kai.t@example.com',None,None,None,None,om['Cloudbridge Consulting'],'Consultant','google','Consulting Partner','contact',None,'2025-09-11','Re-engage',None,'Cloud-assigned consultant.'),
        ('Nina','Volkov',None,None,None,None,'linkedin.com/in/example-nvolkov',om['Acme Cloud'],'Business Consultant','google','Cloud Employee','connected',None,'2024-08-30',None,None,None),
        ('Felix','Weber',None,None,None,None,'linkedin.com/in/example-fweber',om['Acme Research'],'Developer Relations Engineer','google','Research Employee','connected',None,'2025-11-13',None,None,None),
        ('Zara','Ahmed',None,None,None,None,'linkedin.com/in/example-zahmed',om['Acme Research'],'Principal Research Scientist','google','Research Employee','connected',None,'2024-08-01',None,None,None),
        ('Omar','Hassan',None,None,None,None,None,om['Acme Cloud'],'Senior Software Engineer','google','Cloud Employee','connected',None,'2025-08-04',None,None,None),
        ('Alex','Demo','admin@example.com',None,'555-000-0000',None,'linkedin.com/in/example-ademo',om['DemoHealth Inc.'],'CEO & Founder','team','Founder','active',None,None,None,None,'Senior engineer background. Demo user.'),
        ('Taylor','Demo','taylor@example.com',None,None,None,'linkedin.com/in/example-tdemo',om['DemoHealth Inc.'],'Software Engineer','team','Co-Founder','active',None,None,None,None,None),
        ('Casey','Rivera',None,None,None,None,'linkedin.com/in/example-crivera',None,'EA & Project Manager','team','Hire','recruiting',None,None,'Extend offer post-funding',None,'Former colleague.'),
        ('TBD',None,None,None,None,None,None,None,'Chief Clinical Officer','team','Hire','searching',None,None,None,None,'Key hire for clinical quality.'),
        ('TBD',None,None,None,None,None,None,None,'Head of Growth','team','Hire','searching',None,None,None,None,None),
        ('TBD',None,None,None,None,None,None,None,'Fractional CFO','team','Hire','searching',None,None,None,None,None),
        ('TBD',None,None,None,None,None,None,None,'CTO','team','Hire','searching',None,None,None,None,None),
        ('TBD',None,None,None,None,None,None,None,'Community Coordinator','team','Hire','searching',None,None,None,None,None),
        ('Henrik','Lindqvist',None,None,None,None,None,None,'CEO, TechDrive','advisor',None,'active',None,None,None,None,None),
        ('Margaret','Collins',None,None,None,None,None,None,'Outpost Group','advisor',None,'active',None,None,None,None,None),
        ('Dana','Mitchell','dana.m@example.com',None,None,None,None,None,'Healthcare Consultant','advisor',None,'active',None,'2025-09-24',None,None,'Provided key introductions.'),
        ('Sam','Harper',None,None,None,None,None,None,None,'advisor',None,'active',None,None,None,None,None),
        ('Robin','Nakamura',None,None,None,None,None,None,'Healthcare Fellow','advisor',None,'active',None,None,None,None,'Industry thought leader.'),
        ('Logan','Pierce','logan.p@example.com',None,None,None,None,om['InfraPro'],'Account Executive','vendor','DevOps','active',None,'2026-02-12','Move forward on infrastructure',None,'Ready to proceed with setup.'),
        ('Mia','Santos',None,None,None,None,None,om['Resonance Health'],None,'partner','Tech Partner','contact',None,None,None,None,'Voice biomarker technology partner.'),
    ]
    for ct in contacts:
        conn.execute(sqlalchemy.text("""INSERT INTO contacts
            (first_name,last_name,email,email_secondary,phone,phone_secondary,linkedin_url,
             organization_id,title,category,subcategory,status,tier,last_contact_date,
             next_action,next_action_date,notes)
            VALUES (:a,:b,:c,:d,:e,:f,:g,:h,:i,:j,:k,:l,:m,:n,:o,:p,:q)"""),
            {"a":ct[0],"b":ct[1],"c":ct[2],"d":ct[3],"e":ct[4],"f":ct[5],"g":ct[6],
             "h":ct[7],"i":ct[8],"j":ct[9],"k":ct[10],"l":ct[11],"m":ct[12],"n":ct[13],
             "o":ct[14],"p":ct[15],"q":ct[16]})

    rows = conn.execute(sqlalchemy.text("SELECT id, first_name, last_name FROM contacts")).fetchall()
    cm = {}
    for cid, fn, ln in rows:
        cm[f"{fn} {ln}" if ln else fn] = cid

    marcus = cm.get('Marcus Chen')
    elena = cm.get('Elena Vasquez')
    sofia = cm.get('Sofia Ramirez')
    logan = cm.get('Logan Pierce')

    interactions = []
    if marcus:
        interactions.extend([
            (marcus,'email_received','email','Re: Diligence questions','Asked about first hires and go-to-market strategy.','2026-02-11'),
            (marcus,'email_sent','email','Re: Diligence questions','Detailed response with hiring plan and campus density model.','2026-02-11'),
            (marcus,'email_received','email','Re: Diligence questions','Wants to see team buildout before committing.','2026-02-11'),
            (marcus,'email_sent','email','Re: Diligence questions','Confirmed recruiting plan for key hires.','2026-02-12'),
        ])
    if elena:
        interactions.append((elena,'email_sent','email','Diligence package','Full package: deck, exec summary, biz plan, financial model.','2026-02-11'))
    if sofia:
        interactions.extend([
            (sofia,'email_received','email','Cloud program follow-up','Following up on AI model access and credits.','2026-02-10'),
            (sofia,'email_sent','email','Company update','Full update on product progress and upcoming milestones.','2026-02-12'),
        ])
    if logan:
        interactions.append((logan,'email_sent','email','Re: Infrastructure','Ready to move forward with setup.','2026-02-12'))

    for ix in interactions:
        conn.execute(sqlalchemy.text(
            "INSERT INTO interactions (contact_id,type,channel,subject,summary,date) VALUES (:a,:b,:c,:d,:e,:f)"
        ), {"a":ix[0],"b":ix[1],"c":ix[2],"d":ix[3],"e":ix[4],"f":ix[5]})

    deals = []
    if marcus: deals.append((marcus,om['Horizon Ventures'],'Horizon Ventures Seed','diligence','$2.5M',25,'Interested in mission. Wants team buildout.'))
    if elena: deals.append((elena,om['Cascade Partners'],'Cascade Seed/A','meeting','$2.5M',20,'Strong relationship from conference.'))
    priya = cm.get('Priya Sharma')
    if priya: deals.append((priya,om['Summit Capital'],'Summit Capital Seed','outreach','$2.5M',10,'Regulatory moat thesis pitch.'))
    chris = cm.get('Chris Donovan')
    if chris: deals.append((chris,None,'Family Office Intro','meeting',None,15,'Intro meeting scheduled.'))
    for d in deals:
        conn.execute(sqlalchemy.text(
            "INSERT INTO deals (contact_id,organization_id,deal_name,stage,amount,probability,notes) VALUES (:a,:b,:c,:d,:e,:f,:g)"
        ), {"a":d[0],"b":d[1],"c":d[2],"d":d[3],"e":d[4],"f":d[5],"g":d[6]})

    programs = [
        ('Cloud Startup Program',om['Acme Cloud'],'active','2025-07-24','2027-07-24','$2,000 credits Year 1',sofia,'2-year cloud credits program.'),
        ('Accelerator Spring 2026',None,'applied','2026-01-01',None,None,None,'Applied to top-tier accelerator.'),
        ('Seed Round ($2.5M)',om['DemoHealth Inc.'],'active','2026-01-01',None,'$2.5M target',None,'Active fundraise with multiple VCs.'),
        ('AI Safety Certification',om['DemoHealth Inc.'],'complete','2025-01-01','2025-12-31','107K safety tests',None,'Ethics-aligned AI certification.'),
        ('PSU Campus Pilot',om['Pacific State University'],'planning',None,None,None,None,'First campus pilot.'),
        ('BAU Campus Pilot',om['Bay Area University'],'planning',None,None,None,None,None),
        ('WTU Campus Pilot',om['Western Tech University'],'planning',None,None,None,None,'Student partnership.'),
    ]
    for p in programs:
        conn.execute(sqlalchemy.text(
            "INSERT INTO programs (name,organization_id,status,start_date,end_date,value,primary_contact_id,notes) VALUES (:a,:b,:c,:d,:e,:f,:g,:h)"
        ), {"a":p[0],"b":p[1],"c":p[2],"d":p[3],"e":p[4],"f":p[5],"g":p[6],"h":p[7]})

    tags = ['fundraise','ai-model','campus-pilot','hipaa','compliance',
            'product-launch','voice-biomarker','team-building','warm-intro',
            'cold-outreach','high-priority','follow-up-needed','demo']
    for t in tags:
        conn.execute(sqlalchemy.text("INSERT INTO tags (name) VALUES (:a)"), {"a": t})

    conn.commit()
    result = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM contacts"))
    print(f"  {result.fetchone()[0]} contacts seeded")
    result = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM organizations"))
    print(f"  {result.fetchone()[0]} organizations seeded")


def seed_users(conn):
    """Seed a default admin user for development. Uses SEED_ADMIN_PASSWORD env var."""
    result = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM users"))
    if result.fetchone()[0] > 0:
        return
    default_pw = os.environ.get("SEED_ADMIN_PASSWORD", "changeme123!")
    seed_email = os.environ.get("SEED_ADMIN_EMAIL", "admin@example.com")
    seed_name = os.environ.get("SEED_ADMIN_NAME", "Admin User")
    pw_hash, pw_salt = hash_password(default_pw)
    conn.execute(sqlalchemy.text(
        "INSERT INTO users (email, password_hash, password_salt, name, role) VALUES (:e, :h, :s, :n, :r)"
    ), {"e": seed_email, "h": pw_hash, "s": pw_salt, "n": seed_name, "r": "admin"})
    conn.commit()
    print(f"  Admin user seeded: {seed_email}")


if __name__ == "__main__":
    engine = get_engine()
    with engine.connect() as conn:
        init_schema(conn)
        seed_data(conn)
        seed_users(conn)
    print("Database initialized.")
