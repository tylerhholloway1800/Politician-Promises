"""Low-confidence matches become GitHub issues instead of going live.

To approve one, add the label `approve` to the issue. To reject, close it.
The workflow applies approved matches on its next run.
"""
import json
import os

import requests

MARK_START = "<!-- match-data"
MARK_END = "-->"


def open_review_issue(s, rank, vote, member, match):
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    issue = next((i for i in s["issues"] if i["rank"] == rank), {})
    payload = {"senator": s["id"], "rank": rank, "vote": vote | {"members": None},
               "member_vote": member["vote"], "match": match}
    title = f"Review: {s['name']} · RC {vote['roll_call']} · {issue.get('issue', '')}"
    body = (
        f"**{s['name']} ({s['party']}-{s['state']})**\n\n"
        f"- Issue: {issue.get('issue')}\n- Campaign position: {issue.get('position')}\n"
        f"- Vote: {member['vote']} on {vote['bill'] or ''} {vote['bill_title'] or vote['title']}\n"
        f"- Question: {vote['question']}\n- Roll call {vote['roll_call']}, {vote['date']}\n"
        f"- Matcher says a **{match.get('consistent_vote')}** would be consistent "
        f"(confidence {match.get('confidence')}): {match.get('reason')}\n\n"
        "Add the `approve` label to count this vote. Close the issue to ignore it.\n\n"
        f"{MARK_START}\n{json.dumps(payload)}\n{MARK_END}\n"
    )
    if not (repo and token):
        print("[review needed]\n" + title)
        return
    r = requests.post(f"https://api.github.com/repos/{repo}/issues",
                      headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                      json={"title": title, "body": body, "labels": ["review"]}, timeout=30)
    if r.status_code >= 300:
        print("Could not open review issue:", r.status_code, r.text[:200])


def parse_issue_body(body):
    start = body.find(MARK_START)
    if start < 0:
        return None
    end = body.find(MARK_END, start)
    return json.loads(body[start + len(MARK_START):end].strip())
