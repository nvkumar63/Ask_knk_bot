"""
whatsapp_bot.py  –  Flask webhook for WhatsApp Cloud API.
"""
import logging, requests
from flask import Flask, request, jsonify, abort
from config import (WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID,
                    WHATSAPP_VERIFY_TOKEN, FLASK_PORT)
from bot_engine import handle_message, get_welcome, get_help
from admin_commands import (
    is_admin, cmd_admin_panel, cmd_addbusiness, cmd_addqa,
    cmd_addrestricted, cmd_adddoc, cmd_listkb, cmd_deletekb,
    cmd_escalations, cmd_resolve, cmd_stats, cmd_block, cmd_unblock,
    cmd_setcontact, cmd_config,
)

log = logging.getLogger(__name__)
app   = Flask(__name__)
PLATFORM = "whatsapp"
WA_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"


def send(to: str, text: str):
    if not text:
        return
    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        try:
            requests.post(WA_URL, timeout=15,
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}",
                         "Content-Type": "application/json"},
                json={"messaging_product": "whatsapp",
                      "recipient_type": "individual",
                      "to": to, "type": "text",
                      "text": {"preview_url": False, "body": chunk}})
        except Exception as e:
            log.error(f"WA send error: {e}")


def _handle_admin_cmd(sender: str, text: str) -> str | None:
    if not text.startswith("/"):
        return None
    parts = text.split(None, 1)
    cmd  = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    dispatch = {
        "/admin":         lambda: cmd_admin_panel(),
        "/addbusiness":   lambda: cmd_addbusiness(args),
        "/addqa":         lambda: cmd_addqa(args),
        "/addrestricted": lambda: cmd_addrestricted(args),
        "/adddoc":        lambda: cmd_adddoc(args),
        "/listkb":        lambda: cmd_listkb(args),
        "/deletekb":      lambda: cmd_deletekb(args),
        "/escalations":   lambda: cmd_escalations(),
        "/resolve":       lambda: cmd_resolve(args),
        "/stats":         lambda: cmd_stats(),
        "/block":         lambda: cmd_block(args, PLATFORM),
        "/unblock":       lambda: cmd_unblock(args, PLATFORM),
        "/setcontact":    lambda: cmd_setcontact(args),
        "/config":        lambda: cmd_config(args),
        "/start":         lambda: get_welcome(),
        "/help":          lambda: get_help(),
    }
    fn = dispatch.get(cmd)
    return fn() if fn else None


@app.route("/webhook", methods=["GET"])
def verify():
    mode, token, challenge = (
        request.args.get("hub.mode"),
        request.args.get("hub.verify_token"),
        request.args.get("hub.challenge"),
    )
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        return challenge, 200
    abort(403)


@app.route("/webhook", methods=["POST"])
def receive():
    data = request.get_json(silent=True) or {}
    try:
        msg    = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = msg["from"]
        if msg.get("type") != "text":
            send(sender, "I can only handle text messages right now.")
            return jsonify({"status": "ok"}), 200
        text = msg["text"]["body"].strip()
        log.info(f"WA {sender}: {text[:80]}")

        if is_admin(sender):
            reply = _handle_admin_cmd(sender, text)
            if reply:
                send(sender, reply)
                return jsonify({"status": "ok"}), 200

        if text.lower() in ["/start", "start", "hi", "hello", "مرحبا", "السلام عليكم"]:
            send(sender, get_welcome())
        elif text.lower() in ["/help", "help"]:
            send(sender, get_help())
        else:
            send(sender, handle_message(sender, PLATFORM, text, sender))
    except (KeyError, IndexError, TypeError):
        pass
    return jsonify({"status": "ok"}), 200


@app.route("/health")
def health():
    return jsonify({"status": "running"}), 200
