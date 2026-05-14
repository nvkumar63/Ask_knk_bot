"""
password_manager.py  –  bcrypt password handling for restricted KB entries.
"""
import bcrypt

# Session state: (chat_id, platform) → restricted kb row
_pending: dict = {}
_unlocked: dict = {}


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False

def set_pending(chat_id, platform, kb_row):
    _pending[(str(chat_id), platform)] = kb_row

def get_pending(chat_id, platform):
    return _pending.get((str(chat_id), platform))

def clear_pending(chat_id, platform):
    _pending.pop((str(chat_id), platform), None)

def mark_unlocked(chat_id, platform, kb_id):
    _unlocked.setdefault((str(chat_id), platform), set()).add(kb_id)

def is_unlocked(chat_id, platform, kb_id):
    return kb_id in _unlocked.get((str(chat_id), platform), set())

def handle_password_attempt(chat_id, platform, entered: str) -> tuple:
    kb_row = get_pending(chat_id, platform)
    if not kb_row:
        return False, ""
    if verify_password(entered, kb_row["password_hash"]):
        clear_pending(chat_id, platform)
        mark_unlocked(chat_id, platform, kb_row["id"])
        return True, f"✅ Password accepted!\n\n{kb_row['answer']}"
    else:
        clear_pending(chat_id, platform)
        return False, "❌ Incorrect password. Access denied."
