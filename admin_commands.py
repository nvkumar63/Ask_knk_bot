from config import CONTACT_MESSAGE
from database import get_stats, list_kb, delete_kb_entry, add_kb_entry, add_document_chunks, set_config, get_config, set_blocked, get_escalations, resolve_escalation, get_all_users
from password_manager import hash_password

def is_admin(chat_id):
    return True

def cmd_addbusiness(args):
    parts = [p.strip() for p in args.split(chr(124))]
    if len(parts) != 3: return chr(85)+chr(115)+chr(97)+chr(103)+chr(101)+chr(58)+chr(32)+chr(47)+chr(97)+chr(100)+chr(100)+chr(98)+chr(117)+chr(115)+chr(105)+chr(110)+chr(101)+chr(115)+chr(115)+chr(32)+chr(99)+chr(97)+chr(116)+chr(101)+chr(103)+chr(111)+chr(114)+chr(121)+chr(32)+chr(124)+chr(32)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(32)+chr(124)+chr(32)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)
    category, question, answer = parts
    eid = add_kb_entry(category, question, answer, source=chr(98)+chr(117)+chr(115)+chr(105)+chr(110)+chr(101)+chr(115)+chr(115))
    return chr(65)+chr(100)+chr(100)+chr(101)+chr(100)+chr(32)+chr(73)+chr(68)+chr(58)+str(eid)

def cmd_addqa(args):
    parts = [p.strip() for p in args.split(chr(124))]
    if len(parts) != 2: return chr(85)+chr(115)+chr(97)+chr(103)+chr(101)+chr(58)+chr(32)+chr(47)+chr(97)+chr(100)+chr(100)+chr(113)+chr(97)+chr(32)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(32)+chr(124)+chr(32)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)
    question, answer = parts
    eid = add_kb_entry(chr(113)+chr(97), question, answer, source=chr(109)+chr(97)+chr(110)+chr(117)+chr(97)+chr(108))
    return chr(81)+chr(38)+chr(65)+chr(32)+chr(65)+chr(100)+chr(100)+chr(101)+chr(100)+chr(32)+chr(73)+chr(68)+chr(58)+str(eid)

def cmd_addrestricted(args):
    parts = [p.strip() for p in args.split(chr(124))]
    if len(parts) != 3: return chr(85)+chr(115)+chr(97)+chr(103)+chr(101)+chr(58)+chr(32)+chr(47)+chr(97)+chr(100)+chr(100)+chr(114)+chr(101)+chr(115)+chr(116)+chr(114)+chr(105)+chr(99)+chr(116)+chr(101)+chr(100)+chr(32)+chr(107)+chr(101)+chr(121)+chr(119)+chr(111)+chr(114)+chr(100)+chr(32)+chr(124)+chr(32)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(32)+chr(124)+chr(32)+chr(112)+chr(97)+chr(115)+chr(115)+chr(119)+chr(111)+chr(114)+chr(100)
    keyword, answer, plain_pass = parts
    hashed = hash_password(plain_pass)
    eid = add_kb_entry(chr(114)+chr(101)+chr(115)+chr(116)+chr(114)+chr(105)+chr(99)+chr(116)+chr(101)+chr(100), keyword, answer, is_restricted=1, password_hash=hashed, source=chr(114)+chr(101)+chr(115)+chr(116)+chr(114)+chr(105)+chr(99)+chr(116)+chr(101)+chr(100))
    return chr(82)+chr(101)+chr(115)+chr(116)+chr(114)+chr(105)+chr(99)+chr(116)+chr(101)+chr(100)+chr(32)+chr(116)+chr(111)+chr(112)+chr(105)+chr(99)+chr(32)+chr(97)+chr(100)+chr(100)+chr(101)+chr(100)+chr(32)+chr(73)+chr(68)+chr(58)+str(eid)

def cmd_adddoc(args):
    parts = args.split(chr(124), 1)
    if len(parts) != 2: return chr(85)+chr(115)+chr(97)+chr(103)+chr(101)+chr(58)+chr(32)+chr(47)+chr(97)+chr(100)+chr(100)+chr(100)+chr(111)+chr(99)+chr(32)+chr(110)+chr(97)+chr(109)+chr(101)+chr(32)+chr(124)+chr(32)+chr(116)+chr(101)+chr(120)+chr(116)
    name, content = parts[0].strip(), parts[1].strip()
    count = add_document_chunks(name, content)
    return chr(68)+chr(111)+chr(99)+chr(117)+chr(109)+chr(101)+chr(110)+chr(116)+chr(32)+chr(115)+chr(116)+chr(111)+chr(114)+chr(101)+chr(100)+chr(32)+chr(105)+chr(110)+chr(32)+str(count)+chr(32)+chr(99)+chr(104)+chr(117)+chr(110)+chr(107)+chr(115)

def cmd_listkb(args=chr(32)):
    try:
        page = max(0, int(args.strip()) - 1) if args.strip() else 0
    except ValueError:
        page = 0
    entries = list_kb(limit=10, offset=page * 10)
    if not entries: return chr(75)+chr(66)+chr(32)+chr(101)+chr(109)+chr(112)+chr(116)+chr(121)
    lines = [chr(75)+chr(66)+chr(32)+chr(76)+chr(105)+chr(115)+chr(116)+chr(58)]
    for e in entries:
        lock = chr(32)+chr(76)+chr(79)+chr(67)+chr(75)+chr(69)+chr(68) if e[chr(105)+chr(115)+chr(95)+chr(114)+chr(101)+chr(115)+chr(116)+chr(114)+chr(105)+chr(99)+chr(116)+chr(101)+chr(100)] else chr(32)
        lines.append(chr(91)+str(e[chr(105)+chr(100)])+chr(93)+chr(32)+e[chr(99)+chr(97)+chr(116)+chr(101)+chr(103)+chr(111)+chr(114)+chr(121)]+lock+chr(32)+e[chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)][:40])
    return chr(10).join(lines)

def cmd_deletekb(args):
    try: eid = int(args.strip())
    except ValueError: return chr(85)+chr(115)+chr(97)+chr(103)+chr(101)+chr(58)+chr(32)+chr(47)+chr(100)+chr(101)+chr(108)+chr(101)+chr(116)+chr(101)+chr(107)+chr(98)+chr(32)+chr(60)+chr(105)+chr(100)+chr(62)
    ok = delete_kb_entry(eid)
    return (chr(68)+chr(101)+chr(108)+chr(101)+chr(116)+chr(101)+chr(100)+chr(32)+str(eid)) if ok else (chr(78)+chr(111)+chr(116)+chr(32)+chr(102)+chr(111)+chr(117)+chr(110)+chr(100))

def cmd_escalations():
    rows = get_escalations(resolved=0, limit=15)
    if not rows: return chr(78)+chr(111)+chr(32)+chr(117)+chr(110)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(101)+chr(100)+chr(32)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(115)
    lines = [chr(85)+chr(110)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(101)+chr(100)+chr(58)]
    for r in rows: lines.append(chr(91)+str(r[chr(105)+chr(100)])+chr(93)+chr(32)+r[chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)][:80])
    return chr(10).join(lines)

def cmd_resolve(args):
    try: eid = int(args.strip())
    except ValueError: return chr(85)+chr(115)+chr(97)+chr(103)+chr(101)+chr(58)+chr(32)+chr(47)+chr(114)+chr(101)+chr(115)+chr(111)+chr(108)+chr(118)+chr(101)+chr(32)+chr(60)+chr(105)+chr(100)+chr(62)
    resolve_escalation(eid)
    return chr(82)+chr(101)+chr(115)+chr(111)+chr(108)+chr(118)+chr(101)+chr(100)+chr(32)+str(eid)

def cmd_stats():
    s = get_stats()
    return chr(83)+chr(116)+chr(97)+chr(116)+chr(115)+chr(58)+chr(32)+chr(85)+chr(115)+chr(101)+chr(114)+chr(115)+chr(61)+str(s[chr(117)+chr(115)+chr(101)+chr(114)+chr(115)])+chr(32)+chr(77)+chr(101)+chr(115)+chr(115)+chr(97)+chr(103)+chr(101)+chr(115)+chr(61)+str(s[chr(109)+chr(101)+chr(115)+chr(115)+chr(97)+chr(103)+chr(101)+chr(115)])+chr(32)+chr(75)+chr(66)+chr(61)+str(s[chr(107)+chr(98)+chr(95)+chr(101)+chr(110)+chr(116)+chr(114)+chr(105)+chr(101)+chr(115)])

def cmd_setcontact(args):
    if not args.strip(): return chr(85)+chr(115)+chr(97)+chr(103)+chr(101)+chr(58)+chr(32)+chr(47)+chr(115)+chr(101)+chr(116)+chr(99)+chr(111)+chr(110)+chr(116)+chr(97)+chr(99)+chr(116)+chr(32)+chr(105)+chr(110)+chr(102)+chr(111)
    set_config(chr(99)+chr(111)+chr(110)+chr(116)+chr(97)+chr(99)+chr(116)+chr(95)+chr(109)+chr(101)+chr(115)+chr(115)+chr(97)+chr(103)+chr(101), args.strip())
    return chr(67)+chr(111)+chr(110)+chr(116)+chr(97)+chr(99)+chr(116)+chr(32)+chr(117)+chr(112)+chr(100)+chr(97)+chr(116)+chr(101)+chr(100)

def cmd_config(args):
    parts = args.strip().split(None, 1)
    if len(parts) == 1: return get_config(parts[0], chr(110)+chr(111)+chr(116)+chr(32)+chr(115)+chr(101)+chr(116))
    set_config(parts[0], parts[1])
    return chr(85)+chr(112)+chr(100)+chr(97)+chr(116)+chr(101)+chr(100)

def cmd_block(args, platform=chr(116)+chr(101)+chr(108)+chr(101)+chr(103)+chr(114)+chr(97)+chr(109)):
    uid = args.strip()
    if not uid: return chr(85)+chr(115)+chr(97)+chr(103)+chr(101)+chr(58)+chr(32)+chr(47)+chr(98)+chr(108)+chr(111)+chr(99)+chr(107)+chr(32)+chr(60)+chr(105)+chr(100)+chr(62)
    set_blocked(uid, platform, True)
    return chr(66)+chr(108)+chr(111)+chr(99)+chr(107)+chr(101)+chr(100)+chr(32)+uid

def cmd_unblock(args, platform=chr(116)+chr(101)+chr(108)+chr(101)+chr(103)+chr(114)+chr(97)+chr(109)):
    uid = args.strip()
    if not uid: return chr(85)+chr(115)+chr(97)+chr(103)+chr(101)+chr(58)+chr(32)+chr(47)+chr(117)+chr(110)+chr(98)+chr(108)+chr(111)+chr(99)+chr(107)+chr(32)+chr(60)+chr(105)+chr(100)+chr(62)
    set_blocked(uid, platform, False)
    return chr(85)+chr(110)+chr(98)+chr(108)+chr(111)+chr(99)+chr(107)+chr(101)+chr(100)+chr(32)+uid

def get_broadcast_targets():
    return [(u[chr(99)+chr(104)+chr(97)+chr(116)+chr(95)+chr(105)+chr(100)], u[chr(112)+chr(108)+chr(97)+chr(116)+chr(102)+chr(111)+chr(114)+chr(109)]) for u in get_all_users()]

def cmd_admin_panel():
    return chr(65)+chr(100)+chr(109)+chr(105)+chr(110)+chr(32)+chr(80)+chr(97)+chr(110)+chr(101)+chr(108)+chr(10)+chr(47)+chr(97)+chr(100)+chr(100)+chr(98)+chr(117)+chr(115)+chr(105)+chr(110)+chr(101)+chr(115)+chr(115)+chr(32)+chr(99)+chr(97)+chr(116)+chr(101)+chr(103)+chr(111)+chr(114)+chr(121)+chr(124)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(124)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(10)+chr(47)+chr(97)+chr(100)+chr(100)+chr(113)+chr(97)+chr(32)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(124)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(10)+chr(47)+chr(97)+chr(100)+chr(100)+chr(114)+chr(101)+chr(115)+chr(116)+chr(114)+chr(105)+chr(99)+chr(116)+chr(101)+chr(100)+chr(32)+chr(107)+chr(101)+chr(121)+chr(119)+chr(111)+chr(114)+chr(100)+chr(124)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(124)+chr(112)+chr(97)+chr(115)+chr(115)+chr(10)+chr(47)+chr(108)+chr(105)+chr(115)+chr(116)+chr(107)+chr(98)+chr(10)+chr(47)+chr(101)+chr(115)+chr(99)+chr(97)+chr(108)+chr(97)+chr(116)+chr(105)+chr(111)+chr(110)+chr(115)+chr(10)+chr(47)+chr(115)+chr(116)+chr(97)+chr(116)+chr(115)