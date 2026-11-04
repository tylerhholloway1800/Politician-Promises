"""Post a grade move to X. Skips quietly if the X keys aren't set.

Secrets: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET.
Set POST_LETTER_CHANGES_ONLY=true to post only when the letter grade changes.
"""
import os


def pct(x):
    return "—" if x is None else f"{round(x * 100)}%"


def bill_url(mv):
    from build import bill_url as bu
    return bu(mv.get("bill"), mv.get("congress"))


def compose(mv, s):
    site = os.environ.get("SITE_URL", "").rstrip("/")
    head = f"{s['name']} ({s['party']}-{s['state']}): {mv['from_grade']} → {mv['to_grade']}"
    if mv["from_grade"] == mv["to_grade"]:
        head = f"{s['name']} ({s['party']}-{s['state']}): {pct(mv['from_pct'])} → {pct(mv['to_pct'])}, still {mv['to_grade']}"
    what = f"{mv['vote']} on {mv['bill'] or mv['question']}"
    if mv.get("bill_title"):
        what += f", {mv['bill_title']}"
    match = "Matches" if mv["consistent"] else "Goes against"
    lines = [head, "", f"{what}. {match} their campaign position: {mv['position']}."]
    url = bill_url(mv)
    if url:
        lines += ["", f"Bill: {url}"]
    if site:
        lines.append(f"Record: {site}/s/{s['id']}.html")
    text = "\n".join(lines)
    if len(text) > 280:  # trim the position text first
        over = len(text) - 280 + 1
        lines[2] = lines[2][: max(40, len(lines[2]) - over)].rstrip() + "…"
        text = "\n".join(lines)
    return text[:280]


def post_move(mv, s):
    if os.environ.get("POST_LETTER_CHANGES_ONLY", "").lower() == "true" and mv["from_grade"] == mv["to_grade"]:
        return
    keys = [os.environ.get(k) for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")]
    text = compose(mv, s)
    if not all(keys):
        print("[post skipped, no X keys]\n" + text + "\n")
        return
    import tweepy
    client = tweepy.Client(consumer_key=keys[0], consumer_secret=keys[1],
                           access_token=keys[2], access_token_secret=keys[3])
    try:
        client.create_tweet(text=text)
        print("Posted:", text.splitlines()[0])
    except Exception as e:  # posting must never break the data update
        print("Post failed:", e)
