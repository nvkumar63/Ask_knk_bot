import threading
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO)

def run_telegram():
    async def main():
        from config import validate
        from database import init_db
        validate()
        init_db()
        if os.path.exists("mydata.txt"):
            from import_doc import import_text_file
            import_text_file("mydata.txt")
        from telegram_bot import build_app, set_commands
        app = build_app()
        await set_commands(app)
        print("Telegram bot running...")
        async with app:
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            await asyncio.Event().wait()
            await app.updater.stop()
            await app.stop()
    asyncio.run(main())

if __name__ == "__main__":
    tg_thread = threading.Thread(target=run_telegram, daemon=True)
    tg_thread.start()
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting Flask on port {port}")
    from whatsapp_bot import app
    app.run(host="0.0.0.0", port=port, debug=False)
# force
