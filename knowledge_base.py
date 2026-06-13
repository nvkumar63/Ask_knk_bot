from groq import Groq
from config import CONTACT_MESSAGE
from database import get_conn, search_kb
import os
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_all_content():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT answer FROM knowledge_base WHERE is_restricted=0"
        ).fetchall()
    parts = [r["answer"] for r in rows]
    return " ".join(parts)

def find_answer(question):
    # Check restricted topics FIRST
    matches = search_kb(question, top_n=3)
    for match in matches:
        if match.get("is_restricted"):
            return "__RESTRICTED__", match

    # Search normal content
    content = get_all_content()
    if not content.strip():
        return None, None

    prompt = (
        "You are a helpful assistant. "
        "Answer the user question using ONLY the information below. "
        "If the answer is clearly in the text, answer friendly and clearly. "
        "If not found at all, reply with exactly: NOT_FOUND\n\n"
        "--- KNOWLEDGE ---\n" + content + "\n---\n\n"
        "User question: " + question + "\n"
        "Answer:"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        answer = response.choices[0].message.content.strip()
        if "NOT_FOUND" in answer:
            return None, None
        return answer, {"id": 1}
    except Exception as e:
        print("Groq error:", e)
        return None, None

def build_out_of_scope_reply():
    return "I am sorry, I don't have information about that.\n\n" + CONTACT_MESSAGE