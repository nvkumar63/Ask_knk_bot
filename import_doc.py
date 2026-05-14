import sys
import os
from database import init_db, add_kb_entry, get_conn

def clear_existing():
    with get_conn() as conn:
        conn.execute("DELETE FROM knowledge_base")
    print("Cleared old content.")

def import_text_file(filepath):
    if not os.path.exists(filepath):
        print("File not found:", filepath)
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        print("File is empty!")
        return
    words = content.split()
    chunk_size = 500
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    clear_existing()
    init_db()
    for i, chunk in enumerate(chunks):
        add_kb_entry(
            category="document",
            question="part " + str(i+1),
            answer=chunk,
            source=filepath
        )
        print("Loaded chunk", i+1, "of", len(chunks))
    print("Done! Bot is ready to answer from your document.")

if len(sys.argv) < 2:
    print("Usage: python3 import_doc.py yourfile.txt")
else:
    import_text_file(sys.argv[1])