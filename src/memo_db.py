import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "ige_prototype.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,  
    type TEXT NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS note_concepts (
        note_id INTEGER NOT NULL,
        concept_id INTEGER NOT NULL
        )
        """)

    conn.commit()
    conn.close()


def show_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    tables = cursor.fetchall()

    print("생성된 테이블:")
    for table in tables:
        table_name = table[0]
        print("-", table_name)

    conn.close()

if __name__ == "__main__":
    create_tables()
    show_tables()
    print("생성확인:", DB_PATH)





    
    
    

