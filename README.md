# 🤖 Custom Knowledge-Base Chatbot
### Telegram + WhatsApp | Python + SQLite | 100% Free

> **This bot ONLY answers from YOUR content.**  
> Unknown questions → "Please contact us at [your info]"

---

## Quick Setup (4 Steps)

### Step 1 – Get Free API Keys
| Key | Where |
|-----|-------|
| `TELEGRAM_TOKEN` | @BotFather on Telegram → /newbot |
| `GEMINI_API_KEY` | aistudio.google.com/app/apikey |
| `WHATSAPP_TOKEN` | developers.facebook.com → App → WhatsApp |
| `ADMIN_CHAT_ID`  | Message @userinfobot on Telegram |

### Step 2 – Install
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env with your keys
```

### Step 3 – Run
```bash
# Telegram
python run_telegram.py

# WhatsApp (in separate terminal)
python run_whatsapp.py
ngrok http 5000             # copy the URL → set as Meta webhook
```

### Step 4 – Add YOUR Content (as admin on Telegram)
```
/addbusiness services | What do you offer? | We offer web design, SEO, and mobile apps.
/addbusiness prices | How much does it cost? | Our packages start from SAR 1500.
/addbusiness location | Where are you located? | We are in Riyadh, Saudi Arabia.
/addqa Do you offer free consultation? | Yes! Contact us for a free 30-min consultation.
/addrestricted internal report | Q3 revenue was SAR 500,000 | admin123
/adddoc Company Policy | [paste your full document text here]
```

---

## How the Bot Answers

```
User: "What services do you offer?"
         ↓
Bot searches YOUR knowledge base
         ↓
Match found → Gemini formats the answer from YOUR text
         ↓
"We offer web design, SEO, and mobile apps."

─────────────────────────────────────────────────

User: "What is the weather today?"
         ↓
No match in YOUR knowledge base
         ↓
"Sorry, I can only answer questions about our services.
 Please contact us: info@company.com | +966-XXX"
 + question logged in escalations table for admin review
```

---

## Admin Commands

### Add Content
```
/addbusiness category | question | answer
/addqa question | answer
/addrestricted keyword | answer | password
/adddoc document_name | full text content
```

### Manage Knowledge Base
```
/listkb              – list all KB entries
/listkb 2            – page 2
/deletekb 5          – delete entry with ID 5
```

### Review Unanswered Questions
```
/escalations         – questions bot couldn't answer
/resolve 3           – mark escalation #3 as resolved
```

### Users & Settings
```
/stats               – full statistics
/block 123456789     – block a user
/unblock 123456789   – unblock a user
/setcontact new contact info here
/broadcast message to all users
/config key value    – update any config setting
```

---

## File Structure
```
chatbot_v2/
├── .env                  ← Your secrets + contact info
├── config.py             ← Loads .env
├── database.py           ← SQLite: 6 tables
├── knowledge_base.py     ← Searches KB, asks Gemini to format
├── password_manager.py   ← bcrypt for restricted topics
├── bot_engine.py         ← Core router → answer or escalate
├── admin_commands.py     ← All admin functions
├── telegram_bot.py       ← Telegram handlers
├── whatsapp_bot.py       ← Flask WhatsApp webhook
├── run_telegram.py       ← Start Telegram
├── run_whatsapp.py       ← Start WhatsApp
└── bot.db                ← Auto-created SQLite
```

---

## Tips for Best Results

- **Add lots of Q&A pairs** – more coverage = fewer escalations
- **Check /escalations weekly** – add answers for common unknown questions
- **Use /adddoc** for long content like policies, catalogues, FAQs
- **Categories help** – use: `services`, `prices`, `location`, `contact`, `policy`
- **Restricted topics** – good for internal info, VIP pricing, staff-only data
# Start 

# cd /Users/knks_macbook/Documents/Python_Projects/Ask_knk_v2
source venv/bin/activate
python3 run_telegram.py

# To open a file /Users/knks_macbook/Documents/Python_Projects/Ask_knk_v2/mydata.txt