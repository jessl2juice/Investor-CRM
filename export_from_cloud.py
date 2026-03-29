#!/usr/bin/env python3
"""
Export all BetterMind CRM data from Cloud SQL to local JSON files.
Requires: pip install cloud-sql-python-connector[pg8000] sqlalchemy pg8000

This connects via the Cloud SQL Python Connector using your gcloud credentials.
Run: python export_from_cloud.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

os.environ['INSTANCE_CONNECTION_NAME'] = 'bettermind-crm:us-west1:bettermind-crm-db'
os.environ['DB_USER'] = 'bettermind'
os.environ['DB_NAME'] = 'bettermind_crm'

import sqlalchemy
from google.cloud.sql.connector import Connector


def main():
    db_pass = os.environ.get('DB_PASS', '')
    if not db_pass:
        db_pass = input("Enter Cloud SQL password for user 'bettermind': ").strip()
        if not db_pass:
            print("ERROR: Password required")
            sys.exit(1)

    print("Connecting to Cloud SQL...")
    connector = Connector()

    def getconn():
        return connector.connect(
            'bettermind-crm:us-west1:bettermind-crm-db',
            'pg8000',
            user='bettermind',
            password=db_pass,
            db='bettermind_crm',
        )

    engine = sqlalchemy.create_engine("postgresql+pg8000://", creator=getconn)

    tables = {
        'organizations': 'orgs_full.json',
        'contacts': 'contacts_full.json',
        'interactions': 'interactions_full.json',
        'deals': 'deals_full.json',
        'programs': 'programs_full.json',
        'tags': 'tags_full.json',
        'users': 'users_full.json',
        'contact_tags': 'contact_tags_full.json',
    }

    with engine.connect() as conn:
        for table, filename in tables.items():
            print(f"Exporting {table}...")
            try:
                rows = conn.execute(sqlalchemy.text(f"SELECT * FROM {table}")).fetchall()
                keys = conn.execute(sqlalchemy.text(f"SELECT * FROM {table} LIMIT 0")).keys()
                col_names = list(keys)
                data = []
                for row in rows:
                    record = {}
                    for i, col in enumerate(col_names):
                        record[col] = row[i]
                    data.append(record)
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                print(f"  {len(data)} records -> {filename}")
            except Exception as e:
                print(f"  ERROR exporting {table}: {e}")

    connector.close()
    print("\nExport complete! JSON files are ready for import_data.py")


if __name__ == '__main__':
    main()
