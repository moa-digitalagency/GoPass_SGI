"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for update_schema.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Updating schema...")

    # Create new tables
    # db.create_all() will only create tables that don't exist
    db.create_all()
    print("New tables created (if any).")

    # SQLite specific check
    def column_exists(table, column):
        try:
            # Result rows are tuples (cid, name, type, notnull, dflt_value, pk)
            # Access by index 1 for name
            result = db.session.execute(text(f"PRAGMA table_info({table})"))
            for row in result:
                if row[1] == column:
                    return True
            return False
        except Exception as e:
            print(f"Error checking column {column} in {table}: {e}")
            return False

    # Add transaction_id to gopasses
    if not column_exists('gopasses', 'transaction_id'):
        print("Adding transaction_id to gopasses...")
        try:
            # SQLite requires separate statements and doesn't support complex ADD COLUMN with constraints well in older versions,
            # but simple ADD COLUMN is usually fine.
            # Note: SQLite ignores foreign key constraints by default unless PRAGMA foreign_keys = ON;
            # Creating the column with REFERENCES is syntactically valid.
            db.session.execute(text("ALTER TABLE gopasses ADD COLUMN transaction_id INTEGER REFERENCES transactions(id)"))
            db.session.commit()
            print("Done.")
        except Exception as e:
            print(f"Error adding transaction_id: {e}")
            db.session.rollback()
    else:
        print("transaction_id already exists in gopasses.")

    # Add is_offline to access_logs
    if not column_exists('access_logs', 'is_offline'):
        print("Adding is_offline to access_logs...")
        try:
            db.session.execute(text("ALTER TABLE access_logs ADD COLUMN is_offline BOOLEAN DEFAULT 0"))
            db.session.commit()
            print("Done.")
        except Exception as e:
            print(f"Error adding is_offline: {e}")
            db.session.rollback()
    else:
        print("is_offline already exists in access_logs.")

    print("Schema update complete.")
