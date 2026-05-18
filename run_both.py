import threading
import asyncio
import logging
from config import TELEGRAM_TOKEN, FLASK_PORT, validate
from database import init_db
from import_doc import import_text_file
import os

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)

def run_whatsapp():
    from whatsapp_bot import app
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)

async def run_telegram():
    from telegram_bot import build_app, set_commands
    app = build_app()
    await set_commands(app)
    print("🤖 Telegram bot running...")
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()
        await app.updater.stop()
        await app.stop()

if __name__ == "__main__":
    validate()
    init_db()
    if os.path.exists("mydata.txt"):
        import_text_file("mydata.txt")
        print("Data loaded!")

    # Run WhatsApp in background thread
    wa_thread = threading.Thread(target=run_whatsapp, daemon=True)
    wa_thread.start()
    print(f"🌐 WhatsApp webhook running on port {FLASK_PORT}")

    # Run Telegram in main thread
    asyncio.run(run_telegram())