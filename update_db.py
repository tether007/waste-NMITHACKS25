"""
Update the database schema to add missing columns.
Uses explicit transaction management and better error handling.
"""

import sys
import logging
from app import app, db
from sqlalchemy import text, inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def check_if_table_exists(conn, table_name):
    """Check if a table exists in the database."""
    inspector = inspect(db.engine)
    exists = table_name in inspector.get_table_names()
    logging.info(f"Table '{table_name}' exists: {exists}")
    return exists

def check_if_column_exists(conn, table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    exists = column_name in columns
    logging.info(f"Column '{column_name}' in table '{table_name}' exists: {exists}")
    return exists

def add_column_if_missing(conn, table_name, column_name, column_type_sql):
    """Add a column if it's missing."""
    if not check_if_column_exists(conn, table_name, column_name):
        logging.info(f"Adding column '{column_name}' to '{table_name}'...")
        # Escape identifiers using double quotes
        conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type_sql};'))
    else:
        logging.info(f"Column '{column_name}' already exists. Skipping...")

def update_waste_item_table():
    """Add missing columns to the waste_item table."""
    with app.app_context():
        logging.info("Starting database schema update...")
        try:
            with db.engine.begin() as conn:
                table_name = 'waste_item'

                if not check_if_table_exists(conn, table_name):
                    logging.warning(f"Table '{table_name}' doesn't exist.")
                    return

                # Required columns and their types (SQLite-safe)
                required_columns = {
                    'user_id': 'INTEGER',
                    'material_detection': 'TEXT',
                    'recycling_completed': 'INTEGER DEFAULT 0',  # BOOLEAN in SQLite
                    'recycling_completion_date': 'TIMESTAMP',
                    'summary': 'TEXT',
                    'is_dropped_off': 'INTEGER DEFAULT 0',  # BOOLEAN in SQLite
                    'drop_location_id': 'INTEGER',
                    'drop_date': 'TIMESTAMP'
                }

                for column, column_type in required_columns.items():
                    add_column_if_missing(conn, table_name, column, column_type)

            logging.info("✅ Database schema update completed successfully.")
        except Exception as e:
            logging.error(f"❌ Error updating database schema: {str(e)}")

if __name__ == '__main__':
    update_waste_item_table()
