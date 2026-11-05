"""Build the static site from data/ into site/.

Run:  python scripts/build.py
"""
import json
import shutil
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from scoring import delivery, plan_score, issue_rating, readiness

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "site"
SITE_NAME = "Politician Promises"

STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
PARTY = {"D": "Democrat", "R": "Republican", "I": "Independent"}
BILL_TYPES = {
    "S": "senate-bill", "H.R": "house-bill", "S.J.RES": "senate-joint-resolution",
    "H.J.RES": "house-joint-resolution", "S.RES": "senate-resolution", "H.RES": "house-resolution",
    "S.CON.RES": "senate-concurrent-resolution", "H.CON.RES": "house-concurrent-resolution",
}


def bill_url(bill, congress):
    """'H.R.1' + 119 -> congress.gov bill page. Returns None if it can't parse."""
    if not bill or not congress:
        return None
    b = bill.upper().replace(" ", "")
    for prefix in sorted(BILL_TYPES, key=len, reverse=True):
        p = prefix + "."
        if b.startswith(p) and b[len(p):].isdigit():
            return f"https://www.congress.gov/bill/{congress}th-congress/{BILL_TYPES[prefix]}/{b[len(p):]}"
    return None


def roll_call_url(v):
    c, s, n = v.get("congress"), v.get("session"), v.get("roll_call")
    if not (c and s and n):
        return None
    return (f"https://www.senate.gov/legislative/LIS/roll_call_votes/vote{c}{s}/"
            f"vote_{c}_{s}_{int(n):05d}.htm")


def fmt_date(iso):
    if not iso:
        return ""
    d = date.fromisoformat(iso[:10])
    return d.strftime("%b %-d, %Y")


def pct(x):
    return "—" if x is None else f"{round(x * 100)}%"


def merged_senators():
    """Senator files plus locked-plan files (data/plans/). A plan file for a
    senator who already has a file is attached as their next-term plan;
    otherwise it stands alone as a senator-elect."""
    out = {}
    for f in sorted((DATA / "senators").glob("*.json")):
        s = json.loads(f.read_text())
        out[s["id"]] = s
    plans = DATA / "plans"
    if plans.exists():
        for f in sorted(plans.glob("*.json")):
            pl = json.loads(f.read_text())
            if pl["id"] in out:
                s = out[pl["id"]]
                s["plan"] = pl["plan"]
                s["plan"]["term_start"] = pl.get("term_start")
                s["plan"]["term_end"] = pl.get("term_end")
                s.setdefault("caveats", []).extend(pl.get("plan_caveats", []))
            else:
                pl.setdefault("issues", [])
                pl.setdefault("caveats", pl.pop("plan_caveats", []))
                out[pl["id"]] = pl
    return list(out.values())


def load():
    senators = []
    for s in merged_senators():
        s["state_name"] = STATES.get(s["state"], s["state"])
        s["party_name"] = PARTY.get(s["party"], s["party"])
        s["ready"], s["pending"] = readiness(s) if s.get("issues") else (False, [])
        s["delivery"] = delivery(s) if s.get("issues") and s["ready"] else None
        s["plan_score"] = plan_score(s.get("plan"))
        for i in s.get("issues", []):
            i["rating"] = issue_rating(i)
            for v in i.get("votes", []):
                v["bill_url"] = bill_url(v.get("bill"), v.get("congress"))
                v["rc_url"] = roll_call_url(v)
                v["date_fmt"] = fmt_date(v.get("date"))
        senators.append(s)
    changes = json.loads((DATA / "changes.json").read_text())
    for c in changes:
        c["date_fmt"] = fmt_date(c.get("date"))
        c["rc_url"] = roll_call_url(c)
        c["bill_url"] = bill_url(c.get("bill"), c.get("congress"))
    changes.sort(key=lambda c: (c.get("date", ""), c.get("roll_call", 0)), reverse=True)
    return senators, changes


def main():
    senators, changes = load()
    by_id = {s["id"]: s for s in senators}
    for c in changes:
        s = by_id.get(c["senator"])
        c["name"] = s["name"] if s else c["senator"]
        c["label"] = f"{s['party']}-{s['state']}" if s else ""
    graded = [s for s in senators if s["delivery"]]
    graded.sort(key=lambda s: (s["state"], s["name"]))
    elect = [s for s in senators if s["plan_score"] and not s.get("issues")]
    reelected = sorted([s for s in senators if s["plan_score"] and s.get("issues")], key=lambda s: (s["state"], s["name"]))
    pending = sorted([s for s in senators if s.get("issues") and not s["ready"]], key=lambda s: (s["state"], s["name"]))
    elect.sort(key=lambda s: (s["state"], s["name"]))

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]))
    env.filters["pct"] = pct
    env.filters["fdate"] = fmt_date
    common = {"site": SITE_NAME, "built": date.today().isoformat()}

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "s").mkdir(parents=True)
    shutil.copytree(ROOT / "static", OUT / "static")

    def write(path, tpl, **ctx):
        p = OUT / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(env.get_template(tpl).render(**common, **ctx))

    write("index.html", "index.html", graded=graded, elect=elect, reelected=reelected, pending=pending, changes=changes[:10], page="home")
    write("moves.html", "moves.html", changes=changes, page="moves")
    write("method.html", "method.html", page="method")
    for s in senators:
        mine = [c for c in changes if c["senator"] == s["id"]]
        write(f"s/{s['id']}.html", "senator.html", s=s, changes=mine, page="senator")
    (OUT / ".nojekyll").write_text("")
    print(f"Built {len(senators)} senator pages, {len(changes)} grade moves -> {OUT}")


if __name__ == "__main__":
    main()
