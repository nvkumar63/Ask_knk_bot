import logging
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes,
)
from telegram.constants import ParseMode
from config import TELEGRAM_TOKEN
from database import get_recent_display, get_or_create_user
from bot_engine import handle_message, get_welcome, get_help
from budget import (
    get_budget_pending, set_budget_pending,
    handle_budget_entry_text, format_summary,
)
from admin_commands import (
    is_admin, cmd_admin_panel, cmd_addbusiness, cmd_addqa,
    cmd_addrestricted, cmd_adddoc, cmd_listkb, cmd_deletekb,
    cmd_escalations, cmd_resolve, cmd_stats, cmd_block, cmd_unblock,
    cmd_setcontact, cmd_config, get_broadcast_targets,
)

log = logging.getLogger(__name__)
PLATFORM = "telegram"

def _cid(u): return str(u.effective_chat.id)
def _un(u):  return u.effective_user.username or ""
def _fn(u):  return u.effective_user.first_name or ""

def _args_from_text(update):
    raw = update.message.text or ""
    return raw.split(" ", 1)[1].strip() if " " in raw else ""

async def _reply(update, text, md=False, reply_markup=None):
    if not text:
        return
    mode = ParseMode.MARKDOWN if md else None
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for idx, chunk in enumerate(chunks):
        # Only attach the keyboard to the last chunk
        markup = reply_markup if idx == len(chunks) - 1 else None
        await update.message.reply_text(chunk, parse_mode=mode, reply_markup=markup)


# ── Basic commands ───────────────────────────────────────────────────────────

async def start(update, ctx):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ Information", callback_data="info"),
         InlineKeyboardButton("💰 Budget", callback_data="budget_menu")]
    ])
    await update.message.reply_text(get_welcome(_fn(update)), reply_markup=keyboard)

async def help_cmd(update, ctx):
    await _reply(update, get_help(), md=True)

async def history_cmd(update, ctx):
    user = get_or_create_user(_cid(update), PLATFORM, _un(update), _fn(update))
    rows = get_recent_display(user["id"], 10)
    if not rows:
        await _reply(update, "No messages yet. Just type your question!")
        return
    lines = ["Your last messages:\n"]
    for r in rows:
        icon = "You:" if r["role"] == "user" else "Bot:"
        txt  = r["content"][:100]
        lines.append(f"{icon} {txt}\n")
    await _reply(update, "\n".join(lines))


# ── Budget commands ──────────────────────────────────────────────────────────

async def budget_cmd(update, ctx):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 Debit", callback_data="budget_debit"),
         InlineKeyboardButton("🟢 Credit", callback_data="budget_credit")]
    ])
    await update.message.reply_text(
        "💰 *Budget Entry*\n\nSelect a type:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )

async def summary_cmd(update, ctx):
    user = get_or_create_user(_cid(update), PLATFORM, _un(update), _fn(update))
    text = format_summary(user["id"])
    await _reply(update, text, md=True)


# ── Inline button callbacks ─────────────────────────────────────────────────

async def on_callback(update, ctx):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = str(query.message.chat_id)

    if data == "budget_menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔴 Debit", callback_data="budget_debit"),
             InlineKeyboardButton("🟢 Credit", callback_data="budget_credit")]
        ])
        await query.edit_message_text(
            "💰 *Budget Entry*\n\nSelect a type:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )
        return

    if data in ("budget_debit", "budget_credit"):
        entry_type = data.split("_")[1]  # "debit" or "credit"
        set_budget_pending(chat_id, PLATFORM, entry_type)
        icon = "🔴" if entry_type == "debit" else "🟢"
        await query.edit_message_text(
            f"{icon} *{entry_type.capitalize()} selected*\n\n"
            "Now send: `amount, category` (optionally add `, YYYY-MM-DD`)\n\n"
            "Example: `250, Groceries` or `1200, Rent, 2026-06-01`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == "info":
        await query.edit_message_text(get_help(), parse_mode=ParseMode.MARKDOWN)
        return


# ── Admin commands ───────────────────────────────────────────────────────────

async def _admin_only(update, fn, *args, **kwargs):
    if not is_admin(_cid(update)):
        await _reply(update, "Admin only.")
        return
    result = fn(*args, **kwargs)
    await _reply(update, result, md=True)

async def admin_cmd(u, ctx):
    await _admin_only(u, cmd_admin_panel)

async def stats_cmd(u, ctx):
    await _admin_only(u, cmd_stats)

async def escalations_cmd(u, ctx):
    await _admin_only(u, cmd_escalations)

async def listkb_cmd(u, ctx):
    args = " ".join(ctx.args) if ctx.args else ""
    await _admin_only(u, cmd_listkb, args)

async def addbusiness_cmd(u, ctx):
    await _admin_only(u, cmd_addbusiness, _args_from_text(u))

async def addqa_cmd(u, ctx):
    await _admin_only(u, cmd_addqa, _args_from_text(u))

async def addrestricted_cmd(u, ctx):
    await _admin_only(u, cmd_addrestricted, _args_from_text(u))

async def adddoc_cmd(u, ctx):
    await _admin_only(u, cmd_adddoc, _args_from_text(u))

async def deletekb_cmd(u, ctx):
    args = " ".join(ctx.args) if ctx.args else ""
    await _admin_only(u, cmd_deletekb, args)

async def resolve_cmd(u, ctx):
    args = " ".join(ctx.args) if ctx.args else ""
    await _admin_only(u, cmd_resolve, args)

async def block_cmd(u, ctx):
    args = " ".join(ctx.args) if ctx.args else ""
    await _admin_only(u, cmd_block, args, PLATFORM)

async def unblock_cmd(u, ctx):
    args = " ".join(ctx.args) if ctx.args else ""
    await _admin_only(u, cmd_unblock, args, PLATFORM)

async def setcontact_cmd(u, ctx):
    await _admin_only(u, cmd_setcontact, _args_from_text(u))

async def config_cmd(u, ctx):
    await _admin_only(u, cmd_config, _args_from_text(u))

async def broadcast_cmd(update, ctx):
    if not is_admin(_cid(update)):
        await _reply(update, "Admin only.")
        return
    msg = _args_from_text(update)
    if not msg:
        await _reply(update, "Usage: /broadcast <message>")
        return
    targets = get_broadcast_targets()
    sent = 0
    for cid, plat in targets:
        if plat != PLATFORM:
            continue
        try:
            await ctx.bot.send_message(chat_id=cid, text=f"Broadcast: {msg}")
            sent += 1
        except Exception as e:
            log.warning(f"Broadcast to {cid} failed: {e}")
    await _reply(update, f"Sent to {sent} users.")


# ── Default text handler ────────────────────────────────────────────────────

async def on_message(update, ctx):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if text.startswith("/"):
        return

    chat_id = _cid(update)

    # If a budget entry is pending (user picked Debit/Credit earlier),
    # treat this message as the entry data instead of a normal question.
    if get_budget_pending(chat_id, PLATFORM):
        reply = handle_budget_entry_text(
            chat_id, PLATFORM, text,
            username=_un(update), first_name=_fn(update),
        )
        await _reply(update, reply, md=True)
        return

    reply = handle_message(
        chat_id=chat_id, platform=PLATFORM,
        text=text, username=_un(update), first_name=_fn(update),
    )
    await _reply(update, reply)


# ── App setup ────────────────────────────────────────────────────────────────

def build_app():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",         start))
    app.add_handler(CommandHandler("help",          help_cmd))
    app.add_handler(CommandHandler("history",       history_cmd))
    app.add_handler(CommandHandler("budget",        budget_cmd))
    app.add_handler(CommandHandler("summary",       summary_cmd))
    app.add_handler(CommandHandler("admin",         admin_cmd))
    app.add_handler(CommandHandler("addbusiness",   addbusiness_cmd))
    app.add_handler(CommandHandler("addqa",         addqa_cmd))
    app.add_handler(CommandHandler("addrestricted", addrestricted_cmd))
    app.add_handler(CommandHandler("adddoc",        adddoc_cmd))
    app.add_handler(CommandHandler("listkb",        listkb_cmd))
    app.add_handler(CommandHandler("deletekb",      deletekb_cmd))
    app.add_handler(CommandHandler("escalations",   escalations_cmd))
    app.add_handler(CommandHandler("resolve",       resolve_cmd))
    app.add_handler(CommandHandler("stats",         stats_cmd))
    app.add_handler(CommandHandler("block",         block_cmd))
    app.add_handler(CommandHandler("unblock",       unblock_cmd))
    app.add_handler(CommandHandler("setcontact",    setcontact_cmd))
    app.add_handler(CommandHandler("broadcast",     broadcast_cmd))
    app.add_handler(CommandHandler("config",        config_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    return app

async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start",   "Start the bot"),
        BotCommand("help",    "Help"),
        BotCommand("history", "Last 10 messages"),
        BotCommand("budget",  "Record a budget entry"),
        BotCommand("summary", "View your budget summary"),
    ])