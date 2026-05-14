import os
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN          = os.getenv("TELEGRAM_TOKEN", "")
WHATSAPP_TOKEN          = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID= os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN   = os.getenv("WHATSAPP_VERIFY_TOKEN", "mytoken")
GEMINI_API_KEY          = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL            = os.getenv("GEMINI_MODEL", "gemini-pro")
ADMIN_CHAT_ID           = os.getenv("ADMIN_CHAT_ID", "")
DB_PATH                 = os.getenv("DB_PATH", "bot.db")
FLASK_PORT              = int(os.getenv("FLASK_PORT", "5000"))
CONTACT_MESSAGE         = os.getenv(
    "CONTACT_MESSAGE",
    "Sorry, I can only answer questions about our services. Please contact us directly."
)
BOT_SCOPE               = os.getenv("BOT_SCOPE", "This bot answers questions about our company only.")

def validate():
    missing = [k for k, v in {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "ADMIN_CHAT_ID":  ADMIN_CHAT_ID,
    }.items() if not v]
    if missing:
        print(f"⚠️  Missing .env keys: {', '.join(missing)}")
