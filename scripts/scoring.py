"""Scoring rules. Every grade on the site is computed here from the data files,
so the rules live in one place and nothing is typed by hand."""

POINTS = {"Delivered": 1.0, "Mixed": 0.5, "Contradicted": 0.0, "Not testable": 0.0}


def issue_rating(issue):
    """An issue's rating follows from its matched votes.

    - No testable position          -> Not testable (counts as a miss)
    - Testable, no matched votes    -> No vote held (left out of the score)
    - All votes consistent          -> Delivered
    - All votes inconsistent        -> Contradicted
    - Some of each                  -> Mixed
    """
    if issue.get("testable") is None:
        return "Not researched"
    if not issue.get("testable"):
        return "Not testable"
    votes = [v for v in issue.get("votes", []) if v.get("consistent") is not None]
    if not votes:
        return "No vote held"
    good = sum(1 for v in votes if v["consistent"])
    if good == len(votes):
        return "Delivered"
    if good == 0:
        return "Contradicted"
    return "Mixed"


def readiness(senator):
    """A senator is graded publicly only when research is finished and every
    recorded vote has been checked against senate.gov. Returns (ready, reasons)."""
    reasons = []
    issues = senator.get("issues", [])
    if len(issues) != 10:
        reasons.append(f"{len(issues)} of 10 issues")
    if any(i.get("testable") is None for i in issues):
        reasons.append("issues not yet researched")
    unchecked = sum(1 for i in issues for v in i.get("votes", []) if not v.get("verified"))
    if unchecked:
        reasons.append(f"{unchecked} votes not yet checked against the official roll call")
    if senator.get("status") == "draft":
        reasons.append("research marked incomplete")
    return (not reasons, reasons)


def grade_letter(pct):
    if pct is None:
        return "—"
    if pct >= 0.9:
        return "A"
    if pct >= 0.8:
        return "B"
    if pct >= 0.7:
        return "C"
    if pct >= 0.6:
        return "D"
    return "F"


def delivery(senator):
    """Delivery score for a senator's current term."""
    issues = senator.get("issues", [])
    counts = {k: 0 for k in ["Delivered", "Mixed", "Contradicted", "Not testable", "No vote held", "Not researched"]}
    points = 0.0
    for i in issues:
        r = issue_rating(i)
        i["rating"] = r
        counts[r] += 1
        points += POINTS.get(r, 0.0)
    denom = len(issues) - counts["No vote held"] - counts["Not researched"]
    pct = points / denom if denom else None
    return {
        "points": points,
        "denominator": denom,
        "pct": pct,
        "grade": grade_letter(pct),
        "counts": counts,
        "graded": denom,
    }


def plan_score(plan):
    """Candidate (locked plan) score: share of top issues with a Concrete plan."""
    if not plan:
        return None
    items = plan.get("issues", [])
    counts = {k: 0 for k in ["Concrete", "Partial", "Vague", "None"]}
    for i in items:
        counts[i.get("rating", "None")] = counts.get(i.get("rating", "None"), 0) + 1
    pct = counts["Concrete"] / len(items) if items else None
    return {"pct": pct, "counts": counts, "total": len(items)}
