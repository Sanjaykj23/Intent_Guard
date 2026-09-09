import sqlite3
import os
import json

DB_PATH = "intent_guard.db"

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"Database file '{DB_PATH}' does not exist yet. Run FastAPI backend to initialize tables.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    print("\n=======================================================")
    print("  INTENT GUARD — SQLite Live Database Inspection Tool  ")
    print("=======================================================\n")
    print(f"Database Path: {os.path.abspath(DB_PATH)}")
    print(f"Found {len(tables)} tables: {', '.join(tables)}\n")

    for table in tables:
        if table.startswith("sqlite_"):
            continue
            
        print(f"--- TABLE: {table} ---")
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Columns: {', '.join(columns)}")

        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        print(f"Total Records: {len(rows)}")

        for i, row in enumerate(rows, 1):
            print(f"  Row {i}:")
            for col_name, val in zip(columns, row):
                print(f"    • {col_name}: {val}")
        print("\n" + "-"*55 + "\n")

    conn.close()

if __name__ == "__main__":
    inspect_db()
