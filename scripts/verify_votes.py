"""Check every recorded vote against senate.gov and fix what's wrong.

For each vote in each senator's file:
- No roll call number: look it up in the session's vote list by date and bill.
- Fetch the roll call and read the senator's actual vote.
- If research recorded the wrong vote, correct it and flip `consistent`.
- "Not Voting" / "Present" -> excluded from the score (consistent = null).
- Mark the vote `verified`.
A vote that can't be found stays unverified, which keeps that senator's
grade unpublished until it's resolved.

Run on GitHub (senate.gov is reachable there):  python scripts/verify_votes.py
"""
import json
import re
import time
from pathlib import Path

from update_votes import get_xml, text, fetch_vote, find_member, MENU, DRY, FETCH_ERRORS

ROOT = Path(__file__).resolve().parent.parent
SEN = ROOT / "data" / "senators"
_menus, _votes = {}, {}


def norm_bill(b):
    return re.sub(r"[^A-Z0-9]", "", (b or "").upper())


def menu(c, s):
    if (c, s) not in _menus:
        root = get_xml(MENU.format(c=c, s=s))
        rows = []
        if root is not None:
            for v in root.iter("vote"):
                rows.append({"n": int(text(v, "vote_number") or 0), "issue": text(v, "issue"),
                             "date": text(v, "vote_date"), "question": text(v, "question")})
        _menus[(c, s)] = rows
    return _menus[(c, s)]


def vote(c, s, n):
    if (c, s, n) not in _votes:
        _votes[(c, s, n)] = fetch_vote(c, s, n)
        time.sleep(0.5)
    return _votes[(c, s, n)]


def find_roll_call(v):
    """Find a missing roll call number by bill and date in the vote list."""
    c, s, d = v.get("congress"), v.get("session"), v.get("date", "")
    if not (c and s and d and v.get("bill")):
        return None
    try:
        month_day = time.strftime("%d-%b", time.strptime(d[:10], "%Y-%m-%d"))  # menu dates look like 17-Mar
    except ValueError:
        return None
    b = norm_bill(v["bill"])
    hits = [r for r in menu(c, s) if r["date"] == month_day and b and b in norm_bill(r["issue"])]
    if not menu(c, s):  # senate.gov unreachable: search voteview instead
        from update_votes import voteview
        hits = [{"n": n} for (s_, n), rec in voteview(c).items()
                if s_ == s and rec["roll"].get("date", "")[:10] == d[:10]
                and b and b in norm_bill(rec["roll"].get("bill_number"))]
    return hits[0]["n"] if len(hits) == 1 else None


def main():
    fixed = checked = missing = 0
    for f in sorted(SEN.glob("*.json")):
        s = json.loads(f.read_text())
        changed = False
        for issue in s.get("issues", []):
            for v in issue.get("votes", []):
                if v.get("verified"):
                    continue
                if not (v.get("congress") and v.get("session")):
                    missing += 1
                    continue
                if not v.get("roll_call"):
                    n = find_roll_call(v)
                    if not n:
                        missing += 1
                        continue
                    v["roll_call"], changed = n, True
                rec = vote(v["congress"], v["session"], v["roll_call"])
                if rec is None:
                    missing += 1
                    continue
                m = find_member(s, rec["members"])
                if m is None:
                    missing += 1
                    continue
                actual = m["vote"]
                if actual not in ("Yea", "Nay"):
                    v["consistent"] = None
                elif actual != v.get("vote") and v.get("consistent") is not None:
                    v["consistent"] = not v["consistent"]
                    v["corrected_from"] = v.get("vote")
                    fixed += 1
                    print(f"  corrected {s['name']} RC {v['roll_call']}: {v.get('vote')} -> {actual}")
                v["vote"] = actual
                v["date"] = v.get("date") or rec["date"]
                v["bill"] = v.get("bill") or rec["bill"]
                v["verified"] = True
                checked += 1
                changed = True
        if changed and not DRY:
            f.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n")
    print(f"Verified {checked} votes, corrected {fixed}, could not find {missing}")
    if FETCH_ERRORS:
        print(f"{len(FETCH_ERRORS)} senate.gov pages could not be fetched; those votes stay unverified")


if __name__ == "__main__":
    main()
