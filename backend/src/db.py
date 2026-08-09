import sqlite3
import json
import logging

logger = logging.getLogger("db")
DB_PATH = "finbuddy_memory.db"

def init_db():
    """Initialize the caller facts database table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_caller(user_id: str):
    """Retrieve a caller's record by user_id."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, language_preference, facts, last_interaction FROM callers WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        name, language_preference, facts_str, last_interaction = row
        try:
            facts = json.loads(facts_str) if facts_str else {}
        except Exception:
            facts = {}
        return {
            "user_id": user_id,
            "name": name,
            "language_preference": language_preference,
            "facts": facts,
            "last_interaction": last_interaction
        }
    return None

def save_caller(user_id: str, name: str, language_preference: str, facts: dict):
    """Save/update a caller's record in the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    facts_str = json.dumps(facts)
    cursor.execute("""
        INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            language_preference=excluded.language_preference,
            facts=excluded.facts,
            last_interaction=CURRENT_TIMESTAMP
    """, (user_id, name, language_preference, facts_str))
    conn.commit()
    conn.close()
