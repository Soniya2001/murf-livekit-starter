import sqlite3
import json
import logging

logger = logging.getLogger("db")
DB_PATH = "finbuddy_memory.db"

def init_db():
    """Initialize the caller facts, escalation requests, and call outcomes database tables if they don't exist."""
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalation_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_id TEXT UNIQUE,
            user_id TEXT,
            caller_name TEXT,
            issue_summary TEXT,
            what_happened TEXT,
            agent_checks TEXT,
            urgency TEXT,
            language TEXT,
            preferred_follow_up TEXT,
            status TEXT DEFAULT 'OPEN',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT UNIQUE,
            user_id TEXT,
            call_type TEXT,
            started_at TEXT,
            ended_at TEXT,
            duration_seconds REAL,
            outcome TEXT DEFAULT 'IN_PROGRESS',
            success_reason TEXT,
            scheme_name TEXT,
            information_requested TEXT,
            language TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def create_escalation(user_id: str, reference_id: str, caller_name: str, issue_summary: str, what_happened: str, agent_checks: str, urgency: str, language: str, preferred_follow_up: str, status: str = "OPEN") -> dict:
    """Create a new escalation request in the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO escalation_requests (reference_id, user_id, caller_name, issue_summary, what_happened, agent_checks, urgency, language, preferred_follow_up, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (reference_id, user_id, caller_name, issue_summary, what_happened, agent_checks, urgency, language, preferred_follow_up, status))
        conn.commit()
        return {"success": True, "reference_id": reference_id, "status": status}
    except Exception as e:
        logger.error(f"Error creating escalation: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def get_escalation(reference_id: str):
    """Retrieve an escalation request by reference_id."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reference_id, user_id, caller_name, issue_summary, what_happened, agent_checks, urgency, language, preferred_follow_up, status, created_at
        FROM escalation_requests WHERE reference_id = ?
    """, (reference_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "reference_id": row[0],
            "user_id": row[1],
            "caller_name": row[2],
            "issue_summary": row[3],
            "what_happened": row[4],
            "agent_checks": row[5],
            "urgency": row[6],
            "language": row[7],
            "preferred_follow_up": row[8],
            "status": row[9],
            "created_at": row[10]
        }
    return None

def list_escalations(status: str = None):
    """List all escalation requests, optionally filtered by status."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if status:
        cursor.execute("""
            SELECT reference_id, user_id, caller_name, issue_summary, what_happened, agent_checks, urgency, language, preferred_follow_up, status, created_at
            FROM escalation_requests WHERE status = ? ORDER BY created_at DESC
        """, (status,))
    else:
        cursor.execute("""
            SELECT reference_id, user_id, caller_name, issue_summary, what_happened, agent_checks, urgency, language, preferred_follow_up, status, created_at
            FROM escalation_requests ORDER BY created_at DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "reference_id": r[0],
            "user_id": r[1],
            "caller_name": r[2],
            "issue_summary": r[3],
            "what_happened": r[4],
            "agent_checks": r[5],
            "urgency": r[6],
            "language": r[7],
            "preferred_follow_up": r[8],
            "status": r[9],
            "created_at": r[10]
        }
        for r in rows
    ]

def update_escalation_status(reference_id: str, status: str) -> bool:
    """Update the status of an escalation request."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE escalation_requests SET status = ? WHERE reference_id = ?
        """, (status, reference_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating escalation status: {e}")
        return False
    finally:
        conn.close()


def start_call_outcome(call_id: str, user_id: str, call_type: str, language: str = "English") -> dict:
    """Initialize a call outcome record as IN_PROGRESS."""
    from datetime import datetime
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    started_at = datetime.utcnow().isoformat() + "Z"
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO call_outcomes 
            (call_id, user_id, call_type, started_at, outcome, language)
            VALUES (?, ?, ?, ?, 'IN_PROGRESS', ?)
        """, (call_id, user_id, call_type, started_at, language))
        conn.commit()
        return {"success": True, "call_id": call_id}
    except Exception as e:
        logger.error(f"Error starting call outcome: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def update_call_outcome(
    call_id: str, 
    outcome: str, 
    success_reason: str = None, 
    scheme_name: str = None, 
    information_requested: str = None,
    language: str = None
) -> bool:
    """Update outcome of a call."""
    from datetime import datetime
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT started_at FROM call_outcomes WHERE call_id = ?", (call_id,))
        row = cursor.fetchone()
        ended_at = datetime.utcnow().isoformat() + "Z"
        duration = 0.0
        if row and row[0]:
            try:
                start_dt = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
                duration = (end_dt - start_dt).total_seconds()
            except Exception:
                pass
        
        query = """
            UPDATE call_outcomes 
            SET ended_at = ?, duration_seconds = ?, outcome = ?
        """
        params = [ended_at, duration, outcome]
        
        if success_reason is not None:
            query += ", success_reason = ?"
            params.append(success_reason)
        if scheme_name is not None:
            query += ", scheme_name = ?"
            params.append(scheme_name)
        if information_requested is not None:
            query += ", information_requested = ?"
            params.append(information_requested)
        if language is not None:
            query += ", language = ?"
            params.append(language)
            
        query += " WHERE call_id = ?"
        params.append(call_id)
        
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating call outcome: {e}")
        return False
    finally:
        conn.close()


def get_call_outcome(call_id: str):
    """Retrieve a call outcome by call_id."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT call_id, user_id, call_type, started_at, ended_at, duration_seconds, outcome, success_reason, scheme_name, information_requested, language, created_at
        FROM call_outcomes WHERE call_id = ?
    """, (call_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "call_id": row[0],
            "user_id": row[1],
            "call_type": row[2],
            "started_at": row[3],
            "ended_at": row[4],
            "duration_seconds": row[5],
            "outcome": row[6],
            "success_reason": row[7],
            "scheme_name": row[8],
            "information_requested": row[9],
            "language": row[10],
            "created_at": row[11]
        }
    return None


def get_analytics_summary() -> dict:
    """Retrieve aggregated counts for call outcomes."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM call_outcomes")
        total_calls = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM call_outcomes WHERE outcome = 'SUCCESS'")
        successful_calls = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM call_outcomes WHERE outcome = 'FAILED'")
        failed_calls = cursor.fetchone()[0]
        
        success_rate = 0.0
        if total_calls > 0:
            success_rate = round((successful_calls / total_calls) * 100, 2)
            
        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": success_rate
        }
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0, "success_rate": 0.0}
    finally:
        conn.close()


