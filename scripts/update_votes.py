"""Daily job: pull new Senate roll calls, match them to locked campaign
positions, update grades, log moves, and post grade moves.

Needs ANTHROPIC_API_KEY. Optional: X_* keys (posting), GITHUB_TOKEN +
GITHUB_REPOSITORY (opening review issues), SITE_URL (links in posts).

Run:  python scripts/update_votes.py            (normal run)
      python scripts/update_votes.py --dry-run  (no writes, no posts)
"""
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import requests

from scoring import delivery
from post import post_move
from review import open_review_issue

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MODEL = os.environ.get("MATCH_MODEL", "claude-sonnet-5-5")
AUTO_CONFIDENCE = float(os.environ.get("AUTO_CONFIDENCE", "0.8"))
DRY = "--dry-run" in sys.argv
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PromiseLedger/1.0; public Senate vote tracker)"}

MENU = "https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_{c}_{s}.xml"
VOTE = "https://www.senate.gov/legislative/LIS/roll_call_votes/vote{c}{s}/vote_{c}_{s}_{n:05d}.xml"


# ---------- data ----------

def load_senators():
    out = {}
    for f in sorted((DATA / "senators").glob("*.json")):
        out[f.stem] = json.loads(f.read_text())
    return out


def save_senator(s):
    if not DRY:
        (DATA / "senators" / f"{s['id']}.json").write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n")


def load_json(name, default):
    p = DATA / name
    return json.loads(p.read_text()) if p.exists() else default


def save_json(name, obj):
    if not DRY:
        (DATA / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def start_terms(senators, today):
    """When a new term begins, the locked plan becomes the list the senator's
    votes are graded on (Concrete and Partial plans are testable). A
    re-elected senator's finished term is archived under `past_terms`."""
    from build import merged_senators
    for s in merged_senators():
        pl = s.get("plan")
        if not pl:
            continue
        start = pl.get("term_start") or s.get("term_start", "9999")
        if today.isoformat() < start:
            continue
        if s.get("issues") and s.get("term_start", "") >= start:
            continue  # already converted
        if s.get("issues"):
            s.setdefault("past_terms", []).append({
                "elected": s.get("elected"), "term_start": s.get("term_start"),
                "term_end": s.get("term_end"), "issue_poll": s.get("issue_poll"),
                "issues": s["issues"],
            })
        s["issues"] = [{
            "rank": i["rank"], "issue": i["issue"],
            "testable": i["rating"] in ("Concrete", "Partial"),
            "position": i["detail"], "position_source": i.get("source"),
            "votes": [],
        } for i in pl["issues"]]
        s["elected"], s["term_start"] = pl.get("year", s.get("elected")), start
        s["term_end"] = pl.get("term_end") or s.get("term_end")
        s["issue_poll"] = pl.get("issue_poll", s.get("issue_poll"))
        s.pop("plan", None)
        s.pop("status", None)
        print(f"Term started: {s['name']} now graded on {len(s['issues'])} locked issues")
        senators[s["id"]] = s
        save_senator(s)
        plan_file = DATA / "plans" / f"{s['id']}.json"
        if plan_file.exists() and not DRY:
            plan_file.unlink()


# ---------- senate.gov ----------

def current_session(today):
    congress = (today.year - 1789) // 2 + 1
    session = 1 if today.year % 2 == 1 else 2
    return congress, session


FETCH_ERRORS = []
_ok = [0]


def get_xml(url):
    """Fetch and parse a senate.gov XML file. Returns None on any failure
    (logged in FETCH_ERRORS) so one bad page never stops the run. If the
    first several fetches all fail, senate.gov is unreachable: stop trying."""
    if len(FETCH_ERRORS) >= 5 and _ok[0] == 0:
        return None
    last = None
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                _ok[0] += 1
                return root
            if r.status_code == 404:
                return None
            last = f"HTTP {r.status_code}"
        except (requests.RequestException, ET.ParseError) as e:
            last = type(e).__name__
        time.sleep(5 * (attempt + 1))
    FETCH_ERRORS.append(f"{url}: {last}")
    print(f"  could not fetch {url} ({last})")
    return None


def text(el, path):
    x = el.find(path)
    return (x.text or "").strip() if x is not None and x.text else ""


# ---------- voteview.com (backup source when senate.gov is unreachable) ----------

VV = "https://voteview.com/static/data/out/{kind}/S{c}_{kind}.csv"
_vv = {}
CAST = {1: "Yea", 2: "Yea", 3: "Yea", 4: "Nay", 5: "Nay", 6: "Nay", 7: "Present", 8: "Present", 9: "Not Voting"}


def _csv(url):
    import csv
    import io
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        if r.status_code == 200:
            return list(csv.DictReader(io.StringIO(r.text)))
        print(f"  voteview {url}: HTTP {r.status_code}")
    except requests.RequestException as e:
        print(f"  voteview {url}: {type(e).__name__}")
    return []


def voteview(congress):
    """Roll calls, members and votes for one Congress from voteview.com, keyed
    by (session, senate roll call number)."""
    if congress in _vv:
        return _vv[congress]
    rolls = _csv(VV.format(kind="rollcalls", c=congress))
    members = {m["icpsr"]: m for m in _csv(VV.format(kind="members", c=congress))}
    by_rn, out = {}, {}
    for r in rolls:
        try:
            year = int(r["date"][:4])
            sess = 1 if year % 2 == 1 else 2
            num = int(float(r.get("clerk_rollnumber") or r["rollnumber"]))
        except (KeyError, ValueError):
            continue
        by_rn[r["rollnumber"]] = (sess, num)
        out[(sess, num)] = {"roll": r, "members": []}
    if out:
        for v in _csv(VV.format(kind="votes", c=congress)):
            key = by_rn.get(v["rollnumber"])
            m = members.get(v["icpsr"])
            if not key or not m:
                continue
            last = (m.get("bioname") or "").split(",")[0].strip().title()
            try:
                cast = CAST.get(int(float(v["cast_code"])), "Not Voting")
            except ValueError:
                cast = "Not Voting"
            out[key]["members"].append({"last": last, "first": "", "state": m.get("state_abbrev", ""),
                                        "party": "", "vote": cast})
    _vv[congress] = out
    return out


def _vv_vote(congress, session, n):
    rec = voteview(congress).get((session, n))
    if not rec:
        return None
    r = rec["roll"]
    bill = (r.get("bill_number") or "").replace(" ", "")
    bill = re.sub(r"^(HR|S|HJRES|SJRES|HRES|SRES|HCONRES|SCONRES)(\d+)$",
                  lambda m: {"HR": "H.R.", "S": "S.", "HJRES": "H.J.Res.", "SJRES": "S.J.Res.", "HRES": "H.Res.",
                             "SRES": "S.Res.", "HCONRES": "H.Con.Res.", "SCONRES": "S.Con.Res."}[m.group(1)] + m.group(2),
                  bill.upper())
    return {
        "congress": congress, "session": session, "roll_call": n, "date": r.get("date", "")[:10],
        "question": r.get("vote_question", ""), "title": r.get("vote_desc", "") or r.get("dtl_desc", ""),
        "result": r.get("vote_result", ""), "doc_type": "PN" if "nomination" in (r.get("vote_question", "") + r.get("vote_desc", "")).lower() else "",
        "bill": bill, "bill_title": r.get("vote_desc", ""), "amendment": "", "amendment_purpose": "",
        "members": rec["members"], "source": "voteview",
    }


def vote_numbers(congress, session):
    root = get_xml(MENU.format(c=congress, s=session))
    if root is None:
        return sorted(n for (s_, n) in voteview(congress) if s_ == session)
    return sorted(int(text(v, "vote_number")) for v in root.iter("vote") if text(v, "vote_number").isdigit())


def fetch_vote(congress, session, n):
    root = get_xml(VOTE.format(c=congress, s=session, n=n))
    if root is None:
        return _vv_vote(congress, session, n)
    doc = root.find("document")
    dtype = text(doc, "document_type") if doc is not None else ""
    dnum = text(doc, "document_number") if doc is not None else ""
    bill = f"{dtype}{dnum}".replace(" ", "") if dtype and dnum else ""
    members = []
    for m in root.iter("member"):
        members.append({
            "last": text(m, "last_name"), "first": text(m, "first_name"),
            "state": text(m, "state"), "party": text(m, "party"),
            "vote": text(m, "vote_cast"),
        })
    raw_date = text(root, "vote_date")
    iso = ""
    m = re.match(r"([A-Za-z]+) (\d+), (\d{4})", raw_date)
    if m:
        iso = time.strftime("%Y-%m-%d", time.strptime(f"{m.group(1)[:3]} {m.group(2)} {m.group(3)}", "%b %d %Y"))
    return {
        "congress": congress, "session": session, "roll_call": n, "date": iso,
        "question": text(root, "vote_question_text") or text(root, "question"),
        "title": text(root, "vote_title"), "result": text(root, "vote_result_text"),
        "doc_type": dtype, "bill": bill,
        "bill_title": text(doc, "document_title") if doc is not None else "",
        "amendment": text(root, "amendment/amendment_number"),
        "amendment_purpose": text(root, "amendment/amendment_purpose"),
        "members": members,
    }


def find_member(s, members):
    """Match a senator to a vote record by state, then last name."""
    same_state = [m for m in members if m["state"] == s["state"]]
    name = s["name"].lower()
    for m in same_state:
        if m["last"] and m["last"].lower() in name:
            return m
    return None


# ---------- matching ----------

RULES = """You match one U.S. Senate roll call vote to senators' locked campaign positions for a nonpartisan accountability site.

A position is TESTED by this vote only if a Yea or a Nay on this exact question plainly advances or opposes that specific position. Count: final passage, amendments, and cloture or motions to proceed when that vote decided the bill's fate. Do not count: purely procedural or housekeeping votes, nominations, or votes whose link to the position needs a chain of assumptions. A large bill can test several positions; judge each separately on the provisions that bear on it.

For each tested position, say which vote (Yea or Nay) is consistent with it, and give a confidence from 0 to 1 that this vote really tests that position and that you picked the right side. Apply identical standards regardless of party. Most votes test no positions; return an empty list then.

Reply with JSON only: {"matches": [{"key": "<key>", "consistent_vote": "Yea" or "Nay", "confidence": 0.0-1.0, "reason": "<one short sentence>"}]}"""


def positions_block(senators):
    lines = []
    for s in senators.values():
        for i in s.get("issues", []):
            if i.get("testable"):
                lines.append(f"{s['id']}#{i['rank']} | {s['party']}-{s['state']} | {i['issue']}: {i['position']}")
    return "\n".join(lines)


def match_vote(client, vote, positions):
    desc = (f"Roll call {vote['roll_call']} ({vote['congress']}th Congress, session {vote['session']}), {vote['date']}\n"
            f"Question: {vote['question']}\nTitle: {vote['title']}\n"
            f"Measure: {vote['bill']} {vote['bill_title']}\n"
            f"Amendment: {vote['amendment']} {vote['amendment_purpose']}\nResult: {vote['result']}")
    msg = client.messages.create(
        model=MODEL, max_tokens=2000,
        system=[{"type": "text", "text": RULES},
                {"type": "text", "text": "Locked positions (key | senator | issue: position):\n" + positions,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": desc}],
    )
    out = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    m = re.search(r"\{.*\}", out, re.S)
    if not m:
        return []
    try:
        return json.loads(m.group(0)).get("matches", [])
    except json.JSONDecodeError:
        print(f"  could not parse match output for RC {vote['roll_call']}")
        return []


# ---------- applying ----------

def apply_match(s, rank, vote, member, match, changes, auto=True):
    """Add the vote to the issue, rescore, log a move if the score changed."""
    issue = next((i for i in s["issues"] if i["rank"] == rank), None)
    if issue is None:
        return None
    if any(v.get("congress") == vote["congress"] and v.get("session") == vote["session"]
           and v.get("roll_call") == vote["roll_call"] for v in issue["votes"]):
        return None
    before = delivery(s)
    issue["votes"].append({
        "congress": vote["congress"], "session": vote["session"], "roll_call": vote["roll_call"],
        "date": vote["date"], "bill": vote["bill"], "bill_title": vote["bill_title"] or vote["title"],
        "question": vote["question"], "vote": member["vote"],
        "consistent": member["vote"] == match["consistent_vote"],
        "auto": auto, "confidence": match.get("confidence"), "reason": match.get("reason"),
    })
    after = delivery(s)
    save_senator(s)
    if before["pct"] == after["pct"]:
        return None
    move = {
        "date": vote["date"], "senator": s["id"], "issue": issue["issue"], "rank": rank,
        "congress": vote["congress"], "session": vote["session"], "roll_call": vote["roll_call"],
        "bill": vote["bill"], "bill_title": vote["bill_title"], "question": vote["question"],
        "vote": member["vote"], "consistent": member["vote"] == match["consistent_vote"],
        "position": issue["position"],
        "from_pct": before["pct"], "to_pct": after["pct"],
        "from_grade": before["grade"], "to_grade": after["grade"], "auto": auto,
    }
    changes.append(move)
    return move


def main():
    import anthropic
    today = date.today()
    senators = load_senators()
    start_terms(senators, today)
    state = load_json("state.json", {"last_roll_call": {}})
    changes = load_json("changes.json", [])
    client = anthropic.Anthropic()
    positions = positions_block(senators)

    congress, session = current_session(today)
    key = f"{congress}-{session}"
    last = state["last_roll_call"].get(key)
    numbers = vote_numbers(congress, session)
    if last is None:
        # First run in a session: start from now rather than reprocessing history
        # already covered by research.
        last = max(numbers) if numbers else 0
        print(f"First run for {key}: starting after roll call {last}")
    new = [n for n in numbers if n > last]
    print(f"{len(new)} new roll calls in {key}")

    moves = []
    for n in new:
        vote = fetch_vote(congress, session, n)
        if vote is None:
            continue
        state["last_roll_call"][key] = n
        if vote["doc_type"] == "PN":  # nominations
            continue
        matches = match_vote(client, vote, positions)
        for mt in matches:
            try:
                sid, rank = mt["key"].split("#")
                rank = int(rank)
            except (KeyError, ValueError):
                continue
            s = senators.get(sid)
            if not s:
                continue
            member = find_member(s, vote["members"])
            if not member or member["vote"] not in ("Yea", "Nay"):
                continue
            if mt.get("consistent_vote") not in ("Yea", "Nay"):
                continue
            if float(mt.get("confidence", 0)) >= AUTO_CONFIDENCE:
                mv = apply_match(s, rank, vote, member, mt, changes)
                if mv:
                    moves.append(mv)
                    print(f"  RC {n}: {s['name']} {mv['from_grade']}→{mv['to_grade']} ({mt['reason']})")
            elif not DRY:
                open_review_issue(s, rank, vote, member, mt)
        time.sleep(1)

    save_json("changes.json", changes)
    save_json("state.json", state)
    if not DRY:
        for mv in moves:
            post_move(mv, senators[mv["senator"]])
    print(f"Done: {len(moves)} grade moves")


if __name__ == "__main__":
    main()
