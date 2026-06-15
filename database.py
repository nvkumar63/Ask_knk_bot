"""
database.py  –  SQLite with 7 tables:
  users, messages, knowledge_base, escalations, documents, bot_config, budget_entries
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

    -- Budget tracking (debit/credit entries)
    CREATE TABLE IF NOT EXISTS budget_entries (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id),
        type        TEXT NOT NULL,        -- 'debit' or 'credit'
        amount      REAL NOT NULL,
        category    TEXT NOT NULL,
        currency    TEXT NOT NULL DEFAULT 'INR',  -- 'INR' or 'SAR'
        person      TEXT NOT NULL DEFAULT 'Family',
        entry_date  TEXT NOT NULL,        -- YYYY-MM-DD
        platform    TEXT NOT NULL,
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Pending budget entry state (persisted, so it survives restarts)
    -- Tracks the multi-step flow: entry_type -> currency -> person -> (waiting for text)
    CREATE TABLE IF NOT EXISTS budget_pending (
        chat_id     TEXT NOT NULL,
        platform    TEXT NOT NULL,
        entry_type  TEXT NOT NULL,        -- 'debit' or 'credit'
        currency    TEXT,                 -- 'INR' or 'SAR' (set in step 2)
        person      TEXT,                 -- 'Family','Naveen', etc. (set in step 3)
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (chat_id, platform)
    );

    INSERT OR IGNORE INTO bot_config(key,value) VALUES
        ('welcome_message','Hello! Ask me anything about our services.'),
        ('out_of_scope_logged','1');
    """
    with get_conn() as conn:
        conn.executescript(sql)
        _migrate_budget_columns(conn)
    print("✅ DB ready:", DB_PATH)


def _migrate_budget_columns(conn):
    """
    Add new columns to budget_entries/budget_pending if upgrading from an
    older schema where these columns didn't exist yet (existing Railway DBs).
    Safe to run every startup - skips if columns already exist.
    """
    entry_cols = {row["name"] for row in conn.execute("PRAGMA table_info(budget_entries)")}
    if "currency" not in entry_cols:
        conn.execute("ALTER TABLE budget_entries ADD COLUMN currency TEXT NOT NULL DEFAULT 'INR'")
    if "person" not in entry_cols:
        conn.execute("ALTER TABLE budget_entries ADD COLUMN person TEXT NOT NULL DEFAULT 'Family'")

    pending_cols = {row["name"] for row in conn.execute("PRAGMA table_info(budget_pending)")}
    if "currency" not in pending_cols:
        conn.execute("ALTER TABLE budget_pending ADD COLUMN currency TEXT")
    if "person" not in pending_cols:
        conn.execute("ALTER TABLE budget_pending ADD COLUMN person TEXT")


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


# ── Budget ────────────────────────────────────────────────────────────────────

def add_budget_entry(user_id, entry_type, amount, category, entry_date, platform,
                      currency="INR", person="Family"):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO budget_entries(user_id,type,amount,category,entry_date,platform,currency,person)
               VALUES(?,?,?,?,?,?,?,?)""",
            (user_id, entry_type, amount, category, entry_date, platform, currency, person))
        return cur.lastrowid

def get_budget_summary(user_id, month=None):
    """month format: 'YYYY-MM'. Defaults to current month."""
    import datetime
    if month is None:
        month = datetime.date.today().strftime("%Y-%m")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM budget_entries WHERE user_id=? AND entry_date LIKE ? "
            "ORDER BY entry_date DESC",
            (user_id, f"{month}%")).fetchall()
    rows = [dict(r) for r in rows]

    # Totals grouped by currency
    totals_by_currency = {}
    for r in rows:
        cur_code = r["currency"]
        bucket = totals_by_currency.setdefault(cur_code, {"debit": 0.0, "credit": 0.0})
        bucket[r["type"]] += r["amount"]

    by_category = {}
    for r in rows:
        key = (r["type"], r["category"], r["currency"])
        by_category[key] = by_category.get(key, 0) + r["amount"]

    by_person = {}
    for r in rows:
        key = (r["person"], r["type"], r["currency"])
        by_person[key] = by_person.get(key, 0) + r["amount"]

    return {
        "month": month,
        "entries": rows,
        "totals_by_currency": totals_by_currency,
        "by_category": by_category,
        "by_person": by_person,
    }

def get_recent_budget_entries(user_id, limit=10):
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM budget_entries WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit))]


# ── Budget Pending State (persisted) ────────────────────────────────────────────
# Multi-step flow stored as one row, filled in progressively:
#   1. set_budget_pending_type(...)      -> entry_type set
#   2. set_budget_pending_currency(...)  -> currency set
#   3. set_budget_pending_person(...)    -> person set, ready for free-text amount/category

def set_budget_pending_type(chat_id, platform, entry_type):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO budget_pending(chat_id,platform,entry_type,currency,person,created_at)
               VALUES(?,?,?,NULL,NULL,CURRENT_TIMESTAMP)
               ON CONFLICT(chat_id,platform) DO UPDATE
               SET entry_type=excluded.entry_type, currency=NULL, person=NULL,
                   created_at=CURRENT_TIMESTAMP""",
            (str(chat_id), platform, entry_type))

def set_budget_pending_currency(chat_id, platform, currency):
    with get_conn() as conn:
        conn.execute(
            "UPDATE budget_pending SET currency=? WHERE chat_id=? AND platform=?",
            (currency, str(chat_id), platform))

def set_budget_pending_person(chat_id, platform, person):
    with get_conn() as conn:
        conn.execute(
            "UPDATE budget_pending SET person=? WHERE chat_id=? AND platform=?",
            (person, str(chat_id), platform))

def get_budget_pending(chat_id, platform):
    """Returns dict {entry_type, currency, person} or None if nothing pending."""
    with get_conn() as conn:
        r = conn.execute(
            "SELECT entry_type, currency, person FROM budget_pending WHERE chat_id=? AND platform=?",
            (str(chat_id), platform)).fetchone()
        return dict(r) if r else None

def clear_budget_pending(chat_id, platform):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM budget_pending WHERE chat_id=? AND platform=?",
            (str(chat_id), platform))


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