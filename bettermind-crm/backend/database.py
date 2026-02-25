"""
BetterMind CRM Database — Schema & Seed Data (PostgreSQL via Cloud SQL)
Run directly to initialize: python database.py
"""
import hashlib
import os
import secrets
from datetime import datetime

import sqlalchemy

# Cloud SQL connection config
INSTANCE_CONNECTION_NAME = os.environ.get("INSTANCE_CONNECTION_NAME", "")
DB_USER = os.environ.get("DB_USER", "bettermind")
DB_PASS = os.environ.get("DB_PASS", "bettermind-crm-2026")
DB_NAME = os.environ.get("DB_NAME", "bettermind_crm")

# For local dev fallback to SQLite
USE_POSTGRES = bool(INSTANCE_CONNECTION_NAME)

if USE_POSTGRES:
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


def get_engine():
    if USE_POSTGRES:
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
            created_at TEXT DEFAULT (now()::text),
            updated_at TEXT DEFAULT (now()::text)
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS interactions (
            id SERIAL PRIMARY KEY,
            contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
            type TEXT NOT NULL CHECK(type IN (
                'email_sent','email_received','linkedin_dm','linkedin_connect',
                'meeting','call','intro','follow_up','pitch','note'
            )),
            channel TEXT CHECK(channel IN (
                'email','linkedin','phone','zoom','google_meet','in_person','slack','other'
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
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )"""))
        conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            channel TEXT,
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
        conn.commit()


def _hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return h, salt


def seed_data(conn):
    result = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM organizations"))
    if result.fetchone()[0] > 0:
        return

    orgs = [
        ('Verdict Capital','vc_firm','https://verdictcap.com',None,'San Francisco','CA','Consumer, community, marketplace','Niko Bonatsos GP. Discord, Livongo thesis.'),
        ('Norwest Venture Partners','vc_firm','https://nvp.com',None,'San Francisco','CA','Healthcare, enterprise, consumer',None),
        ('Andreessen Horowitz (a16z)','vc_firm','https://a16z.com',None,'Menlo Park','CA','Bio+Health, AI, fintech',None),
        ('Founders Fund','vc_firm','https://foundersfund.com',None,'San Francisco','CA','Deep tech, biotech, AI',None),
        ('GV (Google Ventures)','cvc','https://gv.com',None,'Mountain View','CA','Life science, health, AI',None),
        ('Khosla Ventures','vc_firm','https://khoslaventures.com',None,'Menlo Park','CA','Health, AI, sustainability',None),
        ('Future Ventures','vc_firm','https://future.ventures',None,'Menlo Park','CA','Deep tech, science, frontier','Steve Jurvetson firm'),
        ('Forerunner Ventures','vc_firm','https://forerunnerventures.com',None,'San Francisco','CA','Consumer',None),
        ('7Wire Ventures','vc_firm','https://7wireventures.com',None,'Chicago','IL','Digital health',None),
        ('Draper Associates','vc_firm','https://draper.vc',None,'San Mateo','CA','Early stage, disruptive tech',None),
        ('Xfund','vc_firm','https://xfund.com',None,'Cambridge','MA','Seed, university-adjacent',None),
        ('Google Cloud','tech_company','https://cloud.google.com','(650) 253-0000','Mountain View','CA','Cloud, AI, ML, startups','Google for Startups Cloud Program partner'),
        ('Trillo','consulting','https://trillo.io',None,None,None,'Cloud consulting','Google-assigned consulting partner'),
        ('DuploCloud','consulting','https://duplocloud.com',None,None,None,'DevOps, cloud infrastructure','Selected for DevOps/infrastructure'),
        ('BetterMind.Space','startup','https://bettermind.space','(541) 799-8746','Portland','OR','AI mental health, DMHT','Clinician Assist Inc. DBA BetterMind.Space'),
        ('Santa Clara University','university','https://scu.edu',None,'Santa Clara','CA',None,'First campus pilot target'),
        ('Stanford University','university','https://stanford.edu',None,'Stanford','CA',None,'Second campus pilot target'),
        ('UC Berkeley','university','https://berkeley.edu',None,'Berkeley','CA',None,'Third campus. WDB partnership.'),
        ('Kintsugi Health','startup','https://kintsugihealth.com',None,None,None,'Voice biomarkers, mental health AI',None),
        ('Itransition Group','consulting','https://itransition.com',None,None,None,'Healthcare IT, EMR development',None),
        ('Google DeepMind','tech_company','https://deepmind.google',None,'London',None,'AI research',None),
    ]
    for o in orgs:
        conn.execute(sqlalchemy.text(
            "INSERT INTO organizations (name,type,website,phone,city,state,focus_areas,notes) VALUES (:a,:b,:c,:d,:e,:f,:g,:h)"
        ), {"a":o[0],"b":o[1],"c":o[2],"d":o[3],"e":o[4],"f":o[5],"g":o[6],"h":o[7]})

    rows = conn.execute(sqlalchemy.text("SELECT id, name FROM organizations")).fetchall()
    om = {name: oid for oid, name in rows}

    contacts = [
        ('Niko','Bonatsos','niko@verdictcap.com',None,'650.575.5415',None,'linkedin.com/in/bonatsos',om['Verdict Capital'],'General Partner','investor','Tier 1 VC','diligence',1,'2026-02-12','Re-engage after team leveled up',None,'Likes mission + "Brush Your Brain". Says "Level up team first". 25-year history via Lemons2/ComDais.'),
        ('Scott','Beechuk','sbeechuk@nvp.com',None,None,None,'linkedin.com/in/scottbeechuk',om['Norwest Venture Partners'],'Partner','investor','Series A VC','active',1,'2026-02-11','Follow up on diligence package','2026-02-18','Full diligence package sent 2/11. Met during Lemons2 era at Salesforce event 3/2017.'),
        ('Farwell',None,None,None,None,None,None,om['Xfund'],'Partner','investor','Seed VC','outreach',1,'2026-02-11','Follow up','2026-02-18','Outreach sent 2/11'),
        ('Julie',None,'julie@a16z.com',None,None,None,None,om['Andreessen Horowitz (a16z)'],'Partner','investor','Mega VC','follow_up',1,'2026-02-10','Follow up on pitch',None,'Outreach 2/6 + follow-up 2/10. Slingshot/Ash regulatory angle'),
        ('Scott',None,'scott@foundersfund.com',None,None,None,None,om['Founders Fund'],'Partner','investor','Mega VC','follow_up',1,'2026-02-10','Follow up',None,'Outreach 2/6 + follow-up 2/10. Regulatory moat thesis'),
        ('Dr. Ben','Robbins','ben@gv.com',None,None,None,None,om['GV (Google Ventures)'],'Partner','investor','CVC','follow_up',1,'2026-02-10',None,None,None),
        ('Dr. David','Yoo',None,None,None,None,None,om['Khosla Ventures'],'Partner','investor','Mega VC','follow_up',1,'2026-02-10',None,None,None),
        ('Dr. Brian','Nolan',None,None,None,None,None,om['Khosla Ventures'],'Partner','investor','Mega VC','follow_up',1,'2026-02-10',None,None,None),
        ('Lee','Jaffee',None,None,None,None,None,om['7Wire Ventures'],'Partner','investor','Health VC','outreach',1,'2026-02-10','Follow up on email',None,'Emailed 2/10'),
        ('Andy','Tang',None,None,None,None,None,om['Draper Associates'],None,'investor','Seed VC','outreach',2,'2026-02-10',None,None,'LinkedIn message 2/10'),
        ('Manny',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LI DM sent 2/11'),
        ('Robb','Henshaw',None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LI DM sent 2/11'),
        ('Hays',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM 2/11'),
        ('Sietstra',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM 2/11'),
        ('Evans',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM 2/11'),
        ('Patel',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM 2/11'),
        ('Kocher',None,None,None,None,None,None,None,None,'investor',None,'outreach',2,'2026-02-11',None,None,'LinkedIn DM 2/11'),
        ('Kraus',None,None,None,None,None,None,None,None,'investor',None,'scheduled',2,'2026-02-12','LI outreach',None,'LI outreach 2/12'),
        ('Morgan',None,None,None,None,None,None,None,None,'investor',None,'scheduled',2,'2026-02-12','LI outreach',None,'LI outreach 2/12'),
        ('Holly',None,None,None,None,None,None,None,None,'investor',None,'scheduled',2,'2026-02-13','Outreach',None,'Scheduled 2/13'),
        ('Steve','Jurvetson',None,None,None,None,'linkedin.com/in/jurvetson',om['Future Ventures'],'Founder/Partner','investor','Deep Tech VC','passed',1,'2026-02-01',None,None,'25-year relationship. Pitched ComDais Series A at DFJ. Passed on BetterMind.'),
        ('Kristen','Green',None,None,None,None,None,om['Forerunner Ventures'],'Founder/Partner','investor','Consumer VC','passed',1,'2026-02-01',None,None,'Passed.'),
        ('Dallas','Willisson',None,None,None,None,None,None,'Family Office Network','investor','Family Office','scheduled',2,'2026-02-25','Intro meeting Feb 25','2026-02-25','Intro meeting Feb 25, 11:30 AM.'),
        ('Maria','Alvarez Bermudez','delsolm@xwf.google.com',None,'+1 (313) 483-9149',None,None,om['Google Cloud'],'Account Manager','google','GFS Program','active',None,'2026-02-12','Schedule meeting ASAP','2026-02-14','PRIMARY Google contact. MedGemma follow-up. Full update sent 2/12.'),
        ('Rajmeet','Singh','rajmeet@google.com',None,None,None,None,om['Google Cloud'],'Startup Program','google','GFS Program','active',None,'2025-09-11','Re-engage with update',None,'Booked Getting Started call Sep 11.'),
        ('Jorquel','Condomina','jcondomina@google.com',None,None,None,None,om['Google Cloud'],'Startup Program','google','GFS Program','contact',None,'2025-07-07',None,None,'Organized first GFS meeting Jul 7. Gemini notes available.'),
        ('Shivangidubeyy',None,'shivangidubeyy@google.com',None,None,None,None,om['Google Cloud'],'Startup Program','google','GFS Program','contact',None,'2025-07-07',None,None,'Attended Jul 7 onboarding call'),
        ('Kambi',None,'kambi@trillo.io',None,None,None,None,om['Trillo'],'Consultant','google','Consulting Partner','contact',None,'2025-09-11','Re-engage',None,'Google-assigned. Discussed MedGemma 27B, 3-LLM arch, FHIR, SaMD.'),
        ('Shrut','Parmar',None,None,None,None,'linkedin.com/in/shrutparmar',om['Google Cloud'],'SMB Business Consultant, Looker','google','Google Employee','connected',None,'2024-08-30',None,None,None),
        ('Thorsten','Schaeff',None,None,None,None,'linkedin.com/in/thorwebdev',om['Google DeepMind'],'Developer Relations Engineer','google','Google Employee','connected',None,'2025-11-13',None,None,None),
        ('Alan','Cowen',None,None,None,None,'linkedin.com/in/alan-cowen',om['Google DeepMind'],'Principal Research Scientist','google','Google Employee','connected',None,'2024-08-01',None,None,None),
        ('Parag','Goyal',None,None,None,None,None,om['Google Cloud'],'Senior Software Engineer','google','Google Employee','connected',None,'2025-08-04',None,None,None),
        ('Jess','Jessop','jess@clinicianassist.ai',None,'(541) 799-8746',None,'linkedin.com/in/jessjessop',om['BetterMind.Space'],'CEO/CTO & Founder','team','Founder','active',None,None,None,None,'Sr SWE (Tradex/Ariba-SAP, Atari). Published HuffPost author.'),
        ('Thomas','Jessop','thomas@clinicianassist.ai',None,None,None,'linkedin.com/in/tljessop',om['BetterMind.Space'],'Jr Software Engineer','team','Co-Founder','active',None,None,None,None,None),
        ('Sebastian','Power',None,None,None,None,'linkedin.com/in/sebastianepower',None,'EA & Project Manager','team','Hire','recruiting',None,None,'Extend offer post-funding',None,'Former Arcimoto colleague.'),
        ('TBD',None,None,None,None,None,None,None,'Chief Clinical Officer','team','Hire','searching',None,None,None,None,'CRITICAL. Therapist network, clinical quality, insurance credentialing.'),
        ('TBD',None,None,None,None,None,None,None,'Head of Campus Growth','team','Hire','searching',None,None,None,None,None),
        ('TBD',None,None,None,None,None,None,None,'Fractional CFO','team','Hire','searching',None,None,None,None,None),
        ('TBD',None,None,None,None,None,None,None,'CTO','team','Hire','searching',None,None,None,None,None),
        ('TBD',None,None,None,None,None,None,None,'Ambassador Coordinator','team','Hire','searching',None,None,None,None,None),
        ('Thomas','Stiansen',None,None,None,None,None,None,'CEO, CTRL-DRIVE','advisor',None,'active',None,None,None,None,None),
        ('Brian','Peterson',None,None,None,None,None,None,'Outrigger Group','advisor',None,'active',None,None,None,None,None),
        ('Kimberly','Potter','kimmitchellpotter@gmail.com',None,None,None,None,None,'LBA CSM','advisor',None,'active',None,'2025-09-24',None,None,'Introduced Melvin Grier.'),
        ('Chris','Hemphill',None,None,None,None,None,None,None,'advisor',None,'active',None,None,None,None,None),
        ('Jeanine "Nini"','Martin',None,None,None,None,None,None,'FACHE/FHIMSS Gates Fellow','advisor',None,'active',None,None,None,None,'Olympic athlete.'),
        ('Spencer','Gran','spencer@duplocloud.com',None,None,None,None,om['DuploCloud'],'Account Executive','vendor','DevOps','active',None,'2026-02-12','Move forward on infrastructure',None,'Ready to proceed. Email sent 2/12.'),
        ('Albert','Ihochi',None,None,None,None,None,om['Kintsugi Health'],None,'partner','Tech Partner','contact',None,None,None,None,'Voice biomarker technology.'),
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

    niko = cm.get('Niko Bonatsos')
    scott = cm.get('Scott Beechuk')
    maria = cm.get('Maria Alvarez Bermudez')
    spencer = cm.get('Spencer Gran')

    interactions = []
    if niko:
        interactions.extend([
            (niko,'email_received','email','Re: BetterMind diligence','Niko asked: first hires? What breaks with analogies?','2026-02-11'),
            (niko,'email_sent','email','Re: BetterMind diligence','Detailed response: 4 hires, analogy gaps, campus density','2026-02-11'),
            (niko,'email_received','email','Re: BetterMind diligence','"Level up and form your team first"','2026-02-11'),
            (niko,'email_sent','email','Re: BetterMind diligence','Confirmed recruiting CCO, CFO, CTO, Ambassador. Asked for help.','2026-02-12'),
        ])
    if scott:
        interactions.append((scott,'email_sent','email','Diligence package','Full package: deck, exec summary, biz plan, fin model, launch bible','2026-02-11'))
    if maria:
        interactions.extend([
            (maria,'email_received','email','MedGemma follow-up','Maria following up on MedGemma. Eager to assist.','2026-02-10'),
            (maria,'email_sent','email','UPDATE L2 Juice became BetterMind','Full update: name change, pivot, Brush Your Brain, $2.5M seed, SF trip Feb 17-21.','2026-02-12'),
        ])
    if spencer:
        interactions.append((spencer,'email_sent','email','Re: DuploCloud','Ready to move forward. Investor urgency.','2026-02-12'))

    for ix in interactions:
        conn.execute(sqlalchemy.text(
            "INSERT INTO interactions (contact_id,type,channel,subject,summary,date) VALUES (:a,:b,:c,:d,:e,:f)"
        ), {"a":ix[0],"b":ix[1],"c":ix[2],"d":ix[3],"e":ix[4],"f":ix[5]})

    deals = []
    if niko: deals.append((niko,om['Verdict Capital'],'Verdict Capital Seed','diligence','$2.5M',25,'Likes mission. Wants team first.'))
    if scott: deals.append((scott,om['Norwest Venture Partners'],'Norwest Seed/A','meeting','$2.5M',20,'Historical relationship.'))
    julie = cm.get('Julie')
    if julie: deals.append((julie,om['Andreessen Horowitz (a16z)'],'a16z Seed','outreach','$2.5M',10,'Regulatory angle pitch'))
    dallas = cm.get('Dallas Willisson')
    if dallas: deals.append((dallas,None,'Family Office Intro','meeting',None,15,'Feb 25 intro meeting'))
    for d in deals:
        conn.execute(sqlalchemy.text(
            "INSERT INTO deals (contact_id,organization_id,deal_name,stage,amount,probability,notes) VALUES (:a,:b,:c,:d,:e,:f,:g)"
        ), {"a":d[0],"b":d[1],"c":d[2],"d":d[3],"e":d[4],"f":d[5],"g":d[6]})

    programs = [
        ('Google for Startups Cloud Program',om['Google Cloud'],'active','2025-07-24','2027-07-24','$2,000 credits Year 1',maria,'2-year program. Trillo consulting partner.'),
        ('Y Combinator Spring 2026',None,'applied','2026-01-01',None,None,None,'Full-stack clinical service positioning.'),
        ('Seed Round ($2.5M)',om['BetterMind.Space'],'active','2026-01-01',None,'$2.5M target',None,'9 Tier 1 VCs week 1. SF trip Feb 17-21.'),
        ('CaiT Certification',om['BetterMind.Space'],'complete','2025-01-01','2025-12-31','107K safety tests',None,'APA ethics aligned.'),
        ('SCU Campus Pilot',om['Santa Clara University'],'planning',None,None,None,None,'First campus. Brush Your Brain.'),
        ('Stanford Campus Pilot',om['Stanford University'],'planning',None,None,None,None,None),
        ('Berkeley Campus Pilot',om['UC Berkeley'],'planning',None,None,None,None,'Chris Wang WDB partnership.'),
    ]
    for p in programs:
        conn.execute(sqlalchemy.text(
            "INSERT INTO programs (name,organization_id,status,start_date,end_date,value,primary_contact_id,notes) VALUES (:a,:b,:c,:d,:e,:f,:g,:h)"
        ), {"a":p[0],"b":p[1],"c":p[2],"d":p[3],"e":p[4],"f":p[5],"g":p[6],"h":p[7]})

    tags = ['sf-trip-feb-17','medgemma','campus-pilot','hipaa','dmht-billing',
            'brush-your-brain','voice-biomarker','team-building','warm-intro',
            'cold-outreach','lemons2-era','high-priority','follow-up-needed']
    for t in tags:
        conn.execute(sqlalchemy.text("INSERT INTO tags (name) VALUES (:a)"), {"a": t})

    conn.commit()
    result = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM contacts"))
    print(f"  {result.fetchone()[0]} contacts seeded")
    result = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM organizations"))
    print(f"  {result.fetchone()[0]} organizations seeded")


def seed_users(conn):
    result = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM users"))
    if result.fetchone()[0] > 0:
        return
    pw_hash, pw_salt = _hash_password("Onelongpassword!")
    conn.execute(sqlalchemy.text(
        "INSERT INTO users (email, password_hash, password_salt, name, role) VALUES (:e, :h, :s, :n, :r)"
    ), {"e": "jess@clinicianassist.ai", "h": pw_hash, "s": pw_salt, "n": "Jess Jessop", "r": "admin"})
    conn.commit()
    print("  1 admin user seeded")


if __name__ == "__main__":
    engine = get_engine()
    with engine.connect() as conn:
        init_schema(conn)
        seed_data(conn)
        seed_users(conn)
    print("Database initialized.")
