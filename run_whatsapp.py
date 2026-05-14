"""python run_whatsapp.py"""
import logging
from config import FLASK_PORT, validate
from database import init_db
from whatsapp_bot import app

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)

if __name__ == "__main__":
    validate()
    init_db()
    print(f"🌐 WhatsApp KB bot webhook on port {FLASK_PORT}")
    print(f"📌 Expose with:  ngrok http {FLASK_PORT}")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
