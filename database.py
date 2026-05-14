"""
database.py  –  SQLite with 6 tables:
  users, messages, knowledge_base, escalations, documents, bot_config
"""
import sqlite3
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id     TEXT NOT NULL,
        platform    TEXT NOT NULL DEFAULT 'telegram',
        username    TEXT,
        first_name  TEXT,
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_blocked  INTEGER DEFAULT 0,
        UNIQUE(chat_id, platform)
    );

    CREATE TABLE IF NOT EXISTS messages (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id),
        role        TEXT NOT NULL,
        content     TEXT NOT NULL,
        platform    TEXT NOT NULL,
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- YOUR knowledge: business info, Q&A pairs, document chunks
    CREATE TABLE IF NOT EXISTS knowledge_base (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        category      TEXT NOT NULL DEFAULT 'general',
        question      TEXT NOT NULL,
        answer        TEXT NOT NULL,
        is_restricted INTEGER DEFAULT 0,
        password_hash TEXT,
        source        TEXT DEFAULT 'manual',
        created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Questions the bot could NOT answer (for admin review)
    CREATE TABLE IF NOT EXISTS escalations (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER REFERENCES users(id),
        question    TEXT NOT NULL,
        platform    TEXT NOT NULL,
        resolved    INTEGER DEFAULT 0,
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Raw document storage (chunked)
    CREATE TABLE IF NOT EXISTS documents (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        filename    TEXT NOT NULL,
        content     TEXT NOT NULL,
        chunk_index INTEGER DEFAULT 0,
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Runtime key-value config
    CREATE TABLE IF NOT EXISTS bot_config (
        key        TEXT PRIMARY KEY,
        value      TEXT NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    INSERT OR IGNORE INTO bot_config(key,value) VALUES
        ('welcome_message','Hello! Ask me anything about our services.'),
        ('out_of_scope_logged','1');
    """
    with get_conn() as conn:
        conn.executescript(sql)
    print("✅ DB ready:", DB_PATH)


# ── Users ─────────────────────────────────────────────────────────────────────

def get_or_create_user(chat_id, platform, username="", first_name=""):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE chat_id=? AND platform=?",
            (str(chat_id), platform)).fetchone()
        if row:
            return dict(row)
        conn.execute(
            "INSERT INTO users(chat_id,platform,username,first_name) VALUES(?,?,?,?)",
            (str(chat_id), platform, username, first_name))
        return dict(conn.execute(
            "SELECT * FROM users WHERE chat_id=? AND platform=?",
            (str(chat_id), platform)).fetchone())

def is_blocked(chat_id, platform):
    with get_conn() as conn:
        r = conn.execute(
            "SELECT is_blocked FROM users WHERE chat_id=? AND platform=?",
            (str(chat_id), platform)).fetchone()
        return bool(r and r["is_blocked"])

def set_blocked(chat_id, platform, blocked: bool):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_blocked=? WHERE chat_id=? AND platform=?",
            (1 if blocked else 0, str(chat_id), platform))

def get_all_users():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM users WHERE is_blocked=0")]


# ── Messages ──────────────────────────────────────────────────────────────────

def save_message(user_id, role, content, platform):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages(user_id,role,content,platform) VALUES(?,?,?,?)",
            (user_id, role, content, platform))

def get_history(user_id, limit=6):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role,content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

def get_recent_display(user_id, limit=10):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role,content,created_at FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)).fetchall()
    return [dict(r) for r in reversed(rows)]


# ── Knowledge Base ────────────────────────────────────────────────────────────

def add_kb_entry(category, question, answer,
                 is_restricted=0, password_hash=None, source="manual"):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO knowledge_base
               (category,question,answer,is_restricted,password_hash,source)
               VALUES(?,?,?,?,?,?)""",
            (category, question, answer, is_restricted, password_hash, source))
        return cur.lastrowid

def search_kb(query: str, top_n=3) -> list:
    """
    Simple keyword search across question + answer + category.
    Returns up to top_n best matching rows, scored by word overlap.
    """
    words = [w.lower() for w in query.split() if len(w) > 2]
    if not words:
        return []
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM knowledge_base").fetchall()

    scored = []
    for row in rows:
        text = (row["question"] + " " + row["answer"] + " " + row["category"]).lower()
        score = sum(1 for w in words if w in text)
        if score > 0:
            scored.append((score, dict(row)))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:top_n]]

def get_kb_entry(entry_id):
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM knowledge_base WHERE id=?", (entry_id,)).fetchone()
        return dict(r) if r else None

def delete_kb_entry(entry_id):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM knowledge_base WHERE id=?", (entry_id,))
        return cur.rowcount > 0

def list_kb(limit=20, offset=0):
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id,category,question,is_restricted,source,created_at "
            "FROM knowledge_base ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset))]

def count_kb():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM knowledge_base").fetchone()[0]


# ── Escalations ───────────────────────────────────────────────────────────────

def log_escalation(user_id, question, platform):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO escalations(user_id,question,platform) VALUES(?,?,?)",
            (user_id, question, platform))

def get_escalations(resolved=0, limit=20):
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT e.*,u.chat_id,u.username FROM escalations e "
            "LEFT JOIN users u ON e.user_id=u.id "
            "WHERE e.resolved=? ORDER BY e.id DESC LIMIT ?",
            (resolved, limit))]

def resolve_escalation(esc_id):
    with get_conn() as conn:
        conn.execute("UPDATE escalations SET resolved=1 WHERE id=?", (esc_id,))


# ── Documents ─────────────────────────────────────────────────────────────────

def add_document_chunks(filename: str, content: str, chunk_size=800):
    """Split document into chunks and store each in knowledge_base."""
    words  = content.split()
    chunks = []
    for i in range(0, len(words), chunk_size // 5):   # ~160 words/chunk
        chunk = " ".join(words[i:i + chunk_size // 5])
        chunks.append(chunk)

    ids = []
    for idx, chunk in enumerate(chunks):
        kb_id = add_kb_entry(
            category="document",
            question=f"[{filename} – part {idx+1}]",
            answer=chunk,
            source=filename,
        )
        ids.append(kb_id)
    return len(ids)


# ── Bot Config ────────────────────────────────────────────────────────────────

def get_config(key, default=""):
    with get_conn() as conn:
        r = conn.execute("SELECT value FROM bot_config WHERE key=?", (key,)).fetchone()
        return r["value"] if r else default

def set_config(key, value):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO bot_config(key,value,updated_at) VALUES(?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP""",
            (key, value))


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_stats():
    with get_conn() as conn:
        return {
            "users":         conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "blocked":       conn.execute("SELECT COUNT(*) FROM users WHERE is_blocked=1").fetchone()[0],
            "messages":      conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            "kb_entries":    conn.execute("SELECT COUNT(*) FROM knowledge_base").fetchone()[0],
            "restricted":    conn.execute("SELECT COUNT(*) FROM knowledge_base WHERE is_restricted=1").fetchone()[0],
            "escalations":   conn.execute("SELECT COUNT(*) FROM escalations WHERE resolved=0").fetchone()[0],
        }
