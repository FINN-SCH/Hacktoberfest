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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS written_analyses (
        id TEXT PRIMARY KEY,
        created_at REAL NOT NULL,
        summary TEXT NOT NULL,
        strengths TEXT NOT NULL,
        focus_areas TEXT NOT NULL
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

def get_active_mistakes(session_id: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
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

def get_analysis_data(session_id: Optional[str] = None) -> Dict[str, Any]:
    """Computes deterministic analysis data following PLAN.md Section 8"""
    conn = get_connection()

    # 1. Total sessions and turns
    total_sessions = conn.execute("SELECT COUNT(DISTINCT id) as cnt FROM sessions").fetchone()["cnt"]
    total_turns = conn.execute("SELECT COUNT(*) as cnt FROM turns").fetchone()["cnt"]
    
    # 2. Topic frequency table
    topic_query = """
    SELECT topic, COUNT(*) as cnt, COUNT(DISTINCT session_id) as session_cnt, MAX(created_at) as last_seen
    FROM mistakes
    WHERE is_excluded = 0 AND kind = 'error'
    GROUP BY topic
    ORDER BY cnt DESC
    """
    topic_rows = conn.execute(topic_query).fetchall()
    total_mistakes = sum(r["cnt"] for r in topic_rows)

    topic_frequency = []
    for r in topic_rows:
        share = round((r["cnt"] / total_mistakes * 100), 1) if total_mistakes > 0 else 0
        topic_frequency.append({
            "topic": r["topic"],
            "label": get_topic_label(r["topic"]),
            "errors": r["cnt"],
            "share_pct": share,
            "sessions": r["session_cnt"],
            "last_seen": time.strftime("%Y-%m-%d %H:%M", time.localtime(r["last_seen"])) if r["last_seen"] else "-"
        })

    # 3. Recurring mistakes (topics appearing in 2+ mistakes or sessions)
    recurring = []
    for r in topic_rows:
        if r["cnt"] >= 2:
            # Fetch recent examples
            examples = conn.execute(
                "SELECT original, corrected FROM mistakes WHERE is_excluded = 0 AND kind = 'error' AND topic = ? ORDER BY created_at DESC LIMIT 3",
                (r["topic"],)
            ).fetchall()
            recurring.append({
                "topic": r["topic"],
                "label": get_topic_label(r["topic"]),
                "count": r["cnt"],
                "examples": [{"original": e["original"], "corrected": e["corrected"]} for e in examples]
            })

    # 4. Progress per session
    sessions_list = conn.execute("SELECT * FROM sessions ORDER BY created_at ASC").fetchall()
    progress_sessions = []
    for s in sessions_list:
        sid = s["id"]
        s_turns = conn.execute("SELECT id, user_transcript FROM turns WHERE session_id = ?", (sid,)).fetchall()
        s_turn_cnt = len(s_turns)
        
        # Count words
        word_count = sum(len(t["user_transcript"].split()) for t in s_turns)
        
        # Active mistakes for session
        s_mistakes = conn.execute("SELECT turn_id FROM mistakes WHERE session_id = ? AND is_excluded = 0 AND kind = 'error'", (sid,)).fetchall()
        s_err_count = len(s_mistakes)
        err_turn_ids = {m["turn_id"] for m in s_mistakes}
        
        error_free_turns = max(0, s_turn_cnt - len(err_turn_ids))
        err_free_pct = round((error_free_turns / s_turn_cnt * 100), 1) if s_turn_cnt > 0 else 100.0
        err_per_100_words = round((s_err_count / word_count * 100), 1) if word_count > 0 else 0.0

        progress_sessions.append({
            "session_id": sid,
            "date": time.strftime("%d %b %H:%M", time.localtime(s["created_at"])),
            "scenario": s["scenario"],
            "level": s["level"],
            "turns": s_turn_cnt,
            "error_free_pct": err_free_pct,
            "err_per_100_words": err_per_100_words,
            "errors": s_err_count
        })

    # 5. Accuracy snapshot
    err_turn_ids = {r[0] for r in conn.execute("SELECT DISTINCT turn_id FROM mistakes WHERE is_excluded = 0 AND kind = 'error'").fetchall()}
    error_free_total = max(0, total_turns - len(err_turn_ids))
    accuracy_pct = round((error_free_total / total_turns * 100), 1) if total_turns > 0 else 100.0

    conn.close()
    return {
        "total_sessions": max(1, total_sessions),
        "total_turns": total_turns,
        "total_mistakes": total_mistakes,
        "accuracy_pct": accuracy_pct,
        "topic_frequency": topic_frequency,
        "recurring_mistakes": recurring,
        "progress_sessions": progress_sessions
    }

def get_stats(session_id: Optional[str] = None) -> Dict[str, Any]:
    return get_analysis_data(session_id)

init_db()
