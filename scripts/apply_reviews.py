"""Apply review issues labeled `approve`, then close them."""
import json
import os

import requests

from review import parse_issue_body
from update_votes import load_senators, load_json, save_json, apply_match
from post import post_move


def main():
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    if not (repo and token):
        print("No GitHub credentials; skipping reviews")
        return
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    r = requests.get(f"https://api.github.com/repos/{repo}/issues",
                     params={"state": "open", "labels": "review,approve", "per_page": 100}, headers=h, timeout=30)
    r.raise_for_status()
    senators = load_senators()
    changes = load_json("changes.json", [])
    for issue in r.json():
        data = parse_issue_body(issue.get("body") or "")
        if not data or data["senator"] not in senators:
            continue
        s = senators[data["senator"]]
        member = {"vote": data["member_vote"]}
        mv = apply_match(s, data["rank"], data["vote"], member, data["match"], changes, auto=False)
        save_json("changes.json", changes)
        if mv:
            post_move(mv, s)
        requests.post(issue["comments_url"], headers=h, timeout=30,
                      json={"body": "Applied." + (f" Grade {mv['from_grade']} → {mv['to_grade']}." if mv else " No score change.")})
        requests.patch(issue["url"], headers=h, json={"state": "closed"}, timeout=30)
        print("Applied review:", issue["title"])


if __name__ == "__main__":
    main()
