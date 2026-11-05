# Research brief: lock one 2026 Senate winner's plan

You are researching ONE winner of a 2026 U.S. Senate race for Politician Promises, a nonpartisan site that grades senators on whether their floor votes match what they promised. Their 2026 campaign plan is being LOCKED: these 10 issues and positions are what their votes will be graded on for the next six years. Today is Nov 5, 2026. Apply every rule with identical strictness regardless of party. Use WebSearch/WebFetch; every rating needs a URL. Paraphrase; no long quotes.

## Budget
Web searches are shared with other researchers running at the same time. Use at most ~45 searches. If you run out before finishing an issue, give it `"rating": "None"` only if you looked and found nothing; otherwise put `"rating": null` and set `"status": "draft"` at the top level.

## Step 1: Top 10 issues in the state in 2026
Public polling of that state's voters in 2026 on the most important issues. Prefer, in order:
1. A state poll that ranks issues (most important issue, or share calling each very important), closest to Election Day.
2. Several state polls combined (say how).
3. Regional or national 2026 polling (say so in `issue_poll.note`).
Rank national and state issues together; take the top 10; name them neutrally ("Immigration", not "border crisis"). Leave out items no vote can test (e.g. "which party controls Congress", "candidate character"); take the next issue instead.

## Step 2: Rate the winner's 2026 campaign plan on each issue
Campaign site and issue pages, plan releases, ads, debates, interviews, candidate questionnaires, 2026 campaign news. Only forward-looking 2026 campaign positions count; their past record (in office or elsewhere) is not a promise. Opponents' descriptions of them don't count.
- `Concrete` = a specific solution AND an outcome you can check later: a number or target, or a clear end state such as a ban, a cap, a repeal, a named bill, or a new program. How it's paid for is NOT required.
- `Partial` = a specific direction or approach but nothing checkable, OR only pointing to a law that already exists.
- `Vague` = slogan or direction only ("lower costs", "secure the border", "support our police").
- `None` = no stated position found after looking.
`detail` = the specific items, plain and short (under ~20 words), no adjectives. Concrete and Partial details become the positions their votes are graded on, so write them as checkable commitments.

## Output: write ONE JSON file, then reply briefly
Write `/home/claude/politician-promises/data/plans/<id>.json` (id given in your task). Do NOT touch `data/senators/`. Shape:

```json
{
  "id": "<id>", "name": "<full name as commonly used>", "state": "<2-letter>", "party": "D|R|I",
  "elected": 2026, "term_start": "2027-01-03", "term_end": "2033-01-03",
  "plan": {
    "year": 2026, "locked": "2026-11-03",
    "issue_poll": {"name": "<poll name and dates>", "url": "<url>", "note": "<how combined / fallback, or empty>"},
    "issues": [
      {"rank": 1, "issue": "<neutral name>", "rating": "Concrete|Partial|Vague|None",
       "detail": "<the specific items>", "source": "<url>"}
    ]
  },
  "plan_caveats": ["<one line each: judgment calls, missing sources>"],
  "researched": "2026-11-05"
}
```
Exactly 10 issues, ranks 1–10. Validate the JSON (`python3 -m json.tool <file>`) after writing.

Reply with only: the file path, the count of Concrete/Partial/Vague/None, and any caveat that seriously weakens the result.
