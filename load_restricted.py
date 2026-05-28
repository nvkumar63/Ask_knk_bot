import os
from database import init_db, add_kb_entry, get_conn
from password_manager import hash_password

def load_restricted():
    if not os.path.exists("restricted_topics.txt"):
        print("No restricted_topics.txt found")
        return
    with get_conn() as conn:
        conn.execute("DELETE FROM knowledge_base WHERE is_restricted=1")
    count = 0
    with open("restricted_topics.txt", "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 3:
                continue
            keyword, answer, password = parts
            hashed = hash_password(password)
            add_kb_entry("restricted", keyword, answer,
                        is_restricted=1, password_hash=hashed,
                        source="restricted_file")
            count += 1
            print("Loaded:", keyword)
    print(f"Done! {count} restricted topics loaded.")

if __name__ == "__main__":
    init_db()
    load_restricted()
