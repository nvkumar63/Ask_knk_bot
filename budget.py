"""
budget.py – Budget tracking feature for Telegram bot.

Flow:
  1. User taps "Budget" (button or /budget command)
  2. Bot shows Debit / Credit inline buttons
  3. User picks one -> bot saves pending entry_type, shows Currency buttons
  4. User picks INR / SAR -> bot saves currency, shows Person buttons
  5. User picks a person -> bot saves person, asks for "amount, category[, date]"
  6. User sends free text -> parsed, saved to budget_entries, pending cleared

Pending state is persisted in the budget_pending table so it survives
restarts/redeploys on Railway.
"""
import datetime
from database import (
    add_budget_entry, get_budget_summary, get_or_create_user,
    set_budget_pending_type, set_budget_pending_currency, set_budget_pending_person,
    get_budget_pending, clear_budget_pending,
)

CURRENCIES = ["INR", "SAR"]
PEOPLE = ["Family", "Naveen", "Thara", "Nanu", "Santhi", "Tinu"]


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
    Called when a pending budget entry (with entry_type, currency, person all
    set) exists and the user sends free text "amount, category[, date]".
    Returns a reply string. Always clears pending state afterwards.
    """
    pending = get_budget_pending(chat_id, platform)
    entry_type = pending["entry_type"]
    currency   = pending["currency"] or "INR"
    person     = pending["person"] or "Family"
    clear_budget_pending(chat_id, platform)

    amount, category, date_str = parse_budget_text(text)
    if amount is None:
        return (
            "⚠️ Couldn't understand that. Please use the format:\n"
            "`amount, category` or `amount, category, YYYY-MM-DD`\n\n"
            "Example: `250, Groceries` or `1200, Rent, 2026-06-01`"
        )

    user = get_or_create_user(str(chat_id), platform, username, first_name)
    add_budget_entry(user["id"], entry_type, amount, category, date_str, platform,
                      currency=currency, person=person)

    icon = "🔴" if entry_type == "debit" else "🟢"
    return (
        f"{icon} *{entry_type.capitalize()} recorded*\n\n"
        f"Amount: {amount:,.2f} {currency}\n"
        f"Category: {category}\n"
        f"Person: {person}\n"
        f"Date: {date_str}"
    )


def format_summary(user_id, month=None) -> str:
    data = get_budget_summary(user_id, month)

    if not data["entries"]:
        return f"📊 No entries found for {data['month']}."

    lines = [f"📊 *Budget Summary – {data['month']}*\n"]

    lines.append("*Totals by currency:*")
    for currency, totals in data["totals_by_currency"].items():
        debit  = totals.get("debit", 0)
        credit = totals.get("credit", 0)
        balance = credit - debit
        lines.append(f"  *{currency}*")
        lines.append(f"  🟢 Credit: {credit:,.2f}")
        lines.append(f"  🔴 Debit:  {debit:,.2f}")
        lines.append(f"  ⚖️ Balance: {balance:,.2f}")

    lines.append("\n*By category:*")
    for (etype, category, currency), amt in sorted(data["by_category"].items(),
                                                     key=lambda x: -x[1]):
        icon = "🟢" if etype == "credit" else "🔴"
        lines.append(f"{icon} {category}: {amt:,.2f} {currency}")

    lines.append("\n*By person:*")
    for (person, etype, currency), amt in sorted(data["by_person"].items(),
                                                   key=lambda x: -x[1]):
        icon = "🟢" if etype == "credit" else "🔴"
        lines.append(f"{icon} {person}: {amt:,.2f} {currency}")

    lines.append("\n*Recent entries:*")
    for e in data["entries"][:10]:
        icon = "🟢" if e["type"] == "credit" else "🔴"
        lines.append(
            f"{icon} {e['entry_date']} – {e['category']} "
            f"({e['person']}): {e['amount']:,.2f} {e['currency']}"
        )

    return "\n".join(lines)