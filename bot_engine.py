"""
bot_engine.py  –  Central message handler used by BOTH Telegram and WhatsApp.

Flow:
  1. Block check
  2. Password-pending check
  3. Search YOUR knowledge base
  4. If match:
       a. Restricted → ask for password
       b. Normal     → Gemini formats answer from KB content
  5. No match → out-of-scope reply + log escalation
"""
from database import (
    get_or_create_user, save_message, is_blocked,
    log_escalation, get_config,
)
from knowledge_base import find_answer, build_out_of_scope_reply
from password_manager import (
    get_pending, handle_password_attempt,
    set_pending, is_unlocked,
)
from config import BOT_SCOPE


def handle_message(chat_id: str, platform: str, text: str,
                   username: str = "", first_name: str = "") -> str:
    text = text.strip()
    if not text:
        return ""

    # 1. Blocked?
    if is_blocked(str(chat_id), platform):
        return ""

    # 2. Ensure user in DB
    user = get_or_create_user(str(chat_id), platform, username, first_name)
    uid  = user["id"]

    # 3. Password pending?
    pending = get_pending(str(chat_id), platform)
    if pending:
        ok, reply = handle_password_attempt(str(chat_id), platform, text)
        save_message(uid, "user",      "[password attempt]", platform)
        save_message(uid, "assistant", reply,                platform)
        return reply

    # 4. Save user message
    save_message(uid, "user", text, platform)

    # 5. Search knowledge base
    answer, kb_row = find_answer(text)

    if answer == "__RESTRICTED__":
        # Already unlocked this session?
        if is_unlocked(str(chat_id), platform, kb_row["id"]):
            reply = f"✅ (Already unlocked)\n\n{kb_row['answer']}"
        else:
            set_pending(str(chat_id), platform, kb_row)
            reply = "🔒 This topic is restricted. Please enter the password:"
        save_message(uid, "assistant", reply, platform)
        return reply

    if answer:
        save_message(uid, "assistant", answer, platform)
        return answer

    # 6. No match → escalate
    log_escalation(uid, text, platform)
    reply = build_out_of_scope_reply()
    save_message(uid, "assistant", reply, platform)
    return reply


def get_welcome(first_name=""):
    base = get_config("welcome_message", "Hello! Ask me anything about our services.")
    hi   = f"👋 Hi {first_name}!\n\n" if first_name else "👋 Hello!\n\n"
    return (
        hi + base +
        f"\n\n📌 {BOT_SCOPE}\n\n"
        "Type /help for commands."
    )

def get_help():
    return (
        "🤖 *Bot Help*\n\n"
        "Just type your question — I'll answer from our knowledge base.\n\n"
        "*Commands:*\n"
        "/start – Welcome\n"
        "/help – This message\n"
        "/history – Your last 10 messages\n\n"
        "If I can't answer, I'll give you our contact details."
    )
