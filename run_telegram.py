python3 -c "
content = '''import asyncio
import logging
import os
from config import TELEGRAM_TOKEN, validate
from database import init_db

logging.basicConfig(format=\"%(asctime)s %(levelname)s %(name)s: %(message)s\", level=logging.INFO)

async def main():
    validate()
    if not TELEGRAM_TOKEN:
        print(\"TELEGRAM_TOKEN missing\")
        return
    init_db()
    if os.path.exists(\"mydata.txt\"):
        from import_doc import import_text_file
        import_text_file(\"mydata.txt\")
        print(\"Data loaded!\")
    if os.path.exists(\"restricted_topics.txt\"):
        from load_restricted import load_restricted
        load_restricted()
    from telegram_bot import build_app, set_commands
    app = build_app()
    await set_commands(app)
    print(\"Telegram bot running...\")
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()
        await app.updater.stop()
        await app.stop()

if __name__ == \"__main__\":
    asyncio.run(main())
'''
open('run_telegram.py', 'w').write(content)
print('Done!')
"