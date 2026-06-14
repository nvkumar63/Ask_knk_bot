"""
budget.py – Budget tracking feature for Telegram bot.

Flow:
  1. User taps "Budget" (button or /budget command)
  2. Bot shows Debit / Credit inline buttons
  3. User picks one -> bot saves pending state in DB, asks for input
  4. User sends free text: "amount, category" or "amount, category, YYYY-MM-DD"
  5. Bot parses, saves to budget_entries, confirms, clears pending state

Pending state is persisted in the budget_pending table so it survives
restarts/redeploys on Railway.
"""
import datetime
from database import (
    add_budget_entry, get_budget_summary, get_or_create_user,
    set_budget_pending, get_budget_pending, clear_budget_pending,
)


def parse_budget_text(text: str):
    """
    Parse 'amount, category' or 'amount, category, YYYY-MM-DD'.
    Returns (amount, category, date_str) or (None, None, None) on failure.
    """
    parts = [p.strip() for p in text.split(",")]
    if len(parts) < 2:
        return None, None, None

    try:
        amount = float(parts[0].replace(",", "").replace("$", "").strip())
    except ValueError:
        return None, None, None

    category = parts[1].strip()
    if not category:
        return None, None, None

    if len(parts) >= 3 and parts[2].strip():
        date_str = parts[2].strip()
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None, None, None
    else:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    return amount, category, date_str


def handle_budget_entry_text(chat_id: str, platform: str, text: str,
                              username: str = "", first_name: str = ""):
    """
    Called when a pending budget entry exists and the user sends free text.
    Returns a reply string. Always clears pending state afterwards.
    """
    entry_type = get_budget_pending(chat_id, platform)
    clear_budget_pending(chat_id, platform)

    amount, category, date_str = parse_budget_text(text)
    if amount is None:
        return (
            "⚠️ Couldn't understand that. Please use the format:\n"
            "`amount, category` or `amount, category, YYYY-MM-DD`\n\n"
            "Example: `250, Groceries` or `1200, Rent, 2026-06-01`"
        )

    user = get_or_create_user(str(chat_id), platform, username, first_name)
    add_budget_entry(user["id"], entry_type, amount, category, date_str, platform)

    icon = "🔴" if entry_type == "debit" else "🟢"
    return (
        f"{icon} *{entry_type.capitalize()} recorded*\n\n"
        f"Amount: {amount:,.2f}\n"
        f"Category: {category}\n"
        f"Date: {date_str}"
    )


def format_summary(user_id, month=None) -> str:
    data = get_budget_summary(user_id, month)

    if not data["entries"]:
        return f"📊 No entries found for {data['month']}."

    lines = [f"📊 *Budget Summary – {data['month']}*\n"]
    lines.append(f"🟢 Credit total: {data['total_credit']:,.2f}")
    lines.append(f"🔴 Debit total:  {data['total_debit']:,.2f}")
    lines.append(f"⚖️ Balance:      {data['balance']:,.2f}\n")

    lines.append("*By category:*")
    for (etype, category), amt in sorted(data["by_category"].items(),
                                          key=lambda x: -x[1]):
        icon = "🟢" if etype == "credit" else "🔴"
        lines.append(f"{icon} {category}: {amt:,.2f}")

    lines.append("\n*Recent entries:*")
    for e in data["entries"][:10]:
        icon = "🟢" if e["type"] == "credit" else "🔴"
        lines.append(f"{icon} {e['entry_date']} – {e['category']}: {e['amount']:,.2f}")

    return "\n".join(lines) 