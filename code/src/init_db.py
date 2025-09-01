import sqlite3
import os

# Get the directory of this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths to SQL files
schema_path = os.path.join(BASE_DIR, 'data', 'banking_schema_sqlite.sql')
data_path = os.path.join(BASE_DIR, 'data', 'banking_data.sql')

# Connect/create the DB
db = sqlite3.connect(os.path.join(BASE_DIR, 'banking_system.db'))
cursor = db.cursor()

# Run your schema
with open(schema_path, 'r') as f:
    cursor.executescript(f.read())

# Run your data inserts
with open(data_path, 'r') as f:
    cursor.executescript(f.read())

db.commit()
db.close()
print("✅ banking_system.db created and populated from .sql files")