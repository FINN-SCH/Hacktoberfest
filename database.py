import sqlite3
import os
import time
from typing import List, Dict, Optional, Any
from topics import get_topic_label

DB_PATH = os.getenv("TUTOR_DB_PATH", os.path.join(os.path.dirname(__file__), "tutor.db"))

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        created_at REAL NOT NULL,
        target_lang TEXT DEFAULT 'en',
        native_lang TEXT DEFAULT 'de',
        level TEXT DEFAULT 'B1',
        scenario TEXT DEFAULT 'casual',
        is_ended INTEGER DEFAULT 0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS turns (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        created_at REAL NOT NULL,
        user_transcript TEXT NOT NULL,
        assistant_reply TEXT NOT NULL,
        assistant_spoken TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mistakes (
        id TEXT PRIMARY KEY,
        turn_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        created_at REAL NOT NULL,
        original TEXT NOT NULL,
        corrected TEXT NOT NULL,
        corrected_sentence TEXT NOT NULL,
        kind TEXT NOT NULL,          -- 'error' or 'improvement'
        topic TEXT NOT NULL,         -- e.g. 'en_subject_verb_agreement'
        explanation TEXT NOT NULL,
        is_excluded INTEGER DEFAULT 0, -- 1 if user marked 'Not a mistake' or 'Misheard'
        exclusion_reason TEXT,       -- 'not_a_mistake' or 'misheard'
        FOREIGN KEY (turn_id) REFERENCES turns(id),
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id TEXT PRIMARY KEY,
        created_at REAL NOT NULL,
        mistake_id TEXT NOT NULL,
        question_text TEXT NOT NULL,
        user_answer TEXT NOT NULL,
        is_correct INTEGER NOT NULL,
        FOREIGN KEY (mistake_id) REFERENCES mistakes(id)
    )
    """)
    
    conn.commit()
    conn.close()

def create_session(session_id: str, target_lang: str = "en", native_lang: str = "de", level: str = "B1", scenario: str = "casual"):
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (id, created_at, target_lang, native_lang, level, scenario) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, time.time(), target_lang, native_lang, level, scenario)
        )
    conn.close()

def record_turn(
    turn_id: str,
    session_id: str,
    user_transcript: str,
    assistant_reply: str,
    assistant_spoken: str,
    corrections: List[Dict[str, Any]]
):
    conn = get_connection()
    now = time.time()
    with conn:
        conn.execute(
            "INSERT INTO turns (id, session_id, created_at, user_transcript, assistant_reply, assistant_spoken) VALUES (?, ?, ?, ?, ?, ?)",
            (turn_id, session_id, now, user_transcript, assistant_reply, assistant_spoken)
        )
        for c in corrections:
            conn.execute(
                """INSERT INTO mistakes (
                    id, turn_id, session_id, created_at, original, corrected, corrected_sentence, kind, topic, explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    c["id"],
                    turn_id,
                    session_id,
                    now,
                    c.get("original", ""),
                    c.get("corrected", ""),
                    c.get("corrected_sentence", ""),
                    c.get("kind", "error"),
                    c.get("topic", "en_other"),
                    c.get("explanation", "")
                )
            )
    conn.close()

def exclude_mistake(mistake_id: str, reason: str = "not_a_mistake") -> bool:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "UPDATE mistakes SET is_excluded = 1, exclusion_reason = ? WHERE id = ?",
            (reason, mistake_id)
        )
        updated = cur.rowcount > 0
    conn.close()
    return updated

def get_active_mistakes(session_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_connection()
    query = "SELECT * FROM mistakes WHERE is_excluded = 0 AND kind = 'error'"
    params = []
    if session_id:
        query += " AND session_id = ?"
        params.append(session_id)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_recent_turns(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM turns WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
        (session_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def record_quiz_attempt(attempt_id: str, mistake_id: str, question_text: str, user_answer: str, is_correct: bool):
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO quiz_attempts (id, created_at, mistake_id, question_text, user_answer, is_correct) VALUES (?, ?, ?, ?, ?, ?)",
            (attempt_id, time.time(), mistake_id, question_text, user_answer, 1 if is_correct else 0)
        )
    conn.close()

def get_stats(session_id: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    
    turn_query = "SELECT COUNT(*) as cnt FROM turns"
    turn_params = []
    if session_id:
        turn_query += " WHERE session_id = ?"
        turn_params.append(session_id)
    total_turns = conn.execute(turn_query, turn_params).fetchone()["cnt"]
    
    mistake_query = "SELECT topic, COUNT(*) as cnt FROM mistakes WHERE is_excluded = 0 AND kind = 'error'"
    mistake_params = []
    if session_id:
        mistake_query += " AND session_id = ?"
        mistake_params.append(session_id)
    mistake_query += " GROUP BY topic ORDER BY cnt DESC"
    
    topic_counts = conn.execute(mistake_query, mistake_params).fetchall()
    total_mistakes = sum(r["cnt"] for r in topic_counts)
    
    # Error-free turns
    # Find turns that have NO active errors
    err_turn_query = "SELECT DISTINCT turn_id FROM mistakes WHERE is_excluded = 0 AND kind = 'error'"
    if session_id:
        err_turn_query += " AND session_id = ?"
    err_turn_ids = {r[0] for r in conn.execute(err_turn_query, turn_params).fetchall()}
    
    error_free_turns = max(0, total_turns - len(err_turn_ids))
    accuracy_pct = round((error_free_turns / total_turns * 100), 1) if total_turns > 0 else 100.0
    
    topic_breakdown = [
        {
            "topic": r["topic"],
            "label": get_topic_label(r["topic"]),
            "count": r["cnt"]
        }
        for r in topic_counts
    ]
    
    conn.close()
    return {
        "total_turns": total_turns,
        "total_mistakes": total_mistakes,
        "error_free_turns": error_free_turns,
        "accuracy_pct": accuracy_pct,
        "topic_breakdown": topic_breakdown
    }

# Initialize database on module load
init_db()
