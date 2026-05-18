import threading
import asyncio
import logging
import os
from config import FLASK_PORT, validate
from database import init_db

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)

def run_telegram():
    async def main():
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
    asyncio.run(main())

if __name__ == "__main__":
    validate()
    init_db()
    if os.path.exists("mydata.txt"):
        from import_doc import import_text_file
        import_text_file("mydata.txt")
        print("Data loaded!")

    # Run Telegram in background thread
    tg_thread = threading.Thread(target=run_telegram, daemon=True)
    tg_thread.start()
    print(f"🌐 WhatsApp webhook starting on port {FLASK_PORT}")

    # Run Flask in main thread (Railway needs this)
    from whatsapp_bot import app
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)