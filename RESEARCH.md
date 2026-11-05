# Research brief: one senator's delivery score

You are researching ONE U.S. senator for Politician Promises, a nonpartisan site that grades senators on whether their floor votes match the campaign positions they ran on. Today is Nov 4, 2026. Apply every rule with identical strictness regardless of party. Do not report or speculate about 2026 election results. Use WebSearch/WebFetch; every position and vote needs a URL. Paraphrase; no long quotes.

## Budget and access (read first)
- Web searches are shared with other researchers running at the same time. Use at most ~45 searches. Spend them on the campaign positions (Step 2) first: that is the part only research can do.
- senate.gov, govtrack and congress.gov vote pages are usually blocked here. Don't retry them. Every vote you record is re-checked against senate.gov automatically later and corrected if wrong, so a vote reported by a reliable source (news, the senator's own release, Congressional Record on govinfo, watch.vote) with its date and bill is enough. Include the roll call number when a source gives it; if not, give congress, session, date and bill and leave `roll_call` out.
- If you run out of searches before finishing an issue, set `"testable": null` for it (meaning "not yet researched") instead of guessing `false`. `false` means you looked and found no specific position.
- When all 10 issues are researched, leave `status` out of the file. If any issue is still `null`, set `"status": "draft"`.

## Step 1: Top 10 issues at the senator's last election
Find public polling of that state's voters from their election year (2020, 2022 or 2024) on the most important issues. Prefer, in order:
1. A state poll that ranks issues (most important issue, or share calling each very important), closest to Election Day.
2. Several state polls combined (say how).
3. Regional or national polling from that year (say so in `issue_poll.note`).
Rank national and state issues together; take the top 10; name them neutrally ("Immigration", not "border crisis"). Leave out items no vote can test (e.g. "which party controls Congress"); take the next issue instead.

## Step 2: The senator's stated position on each issue during that campaign
Campaign site (archived copies count), ads, debates, interviews, candidate questionnaires, campaign-year news. Official Senate statements made during the campaign year count if they clearly state a forward position.
- `testable: true` = a specific, checkable position: a policy to pass or block, a ban, a cap, a named bill, a clear for/against.
- `testable: false` = no position found, or a slogan/direction only ("lower costs", "secure the border", "back law enforcement"). Put the closest thing they said, or "No specific position found", in `position`.
Past record is not a promise; only forward-looking positions from the campaign.

## Step 3: Floor votes in the term that test each testable position
Votes cast from the start of the term (Jan 3 of the year after the election) to today. Senate floor roll calls only: final passage, amendments, and cloture or motions to proceed when that vote decided the bill's fate. Not bill sponsorship or cosponsorship. A big package bill counts once for each issue it actually touches. For each vote record whether the senator's vote was consistent with the stated position. If no floor vote tested a testable position, leave `votes` empty and explain in `note` (e.g. "Blocked without a recorded vote").
Sources for roll calls: senate.gov, govinfo.gov Congressional Record, watch.vote, usquery.com, congress.gov, reliable news reporting of the roll call. Record the roll call number, congress (117 = 2021–22, 118 = 2023–24, 119 = 2025–26) and session (1 = odd year, 2 = even year). If you can't confirm the number, omit `roll_call` and say so in a caveat.

## Output: write ONE JSON file, then reply briefly
Write the file at `/home/claude/promise-ledger/data/senators/<id>.json` (id given in your task) with exactly this shape. Use `/home/claude/promise-ledger/data/senators/nh-hassan.json` as a worked example (read it first).

```json
{
  "id": "<id>", "name": "<full name as commonly used>", "state": "<2-letter>", "party": "D|R|I",
  "elected": 2022, "term_start": "2023-01-03", "term_end": "2029-01-03",
  "issue_poll": {"name": "<poll name and dates>", "url": "<url>", "note": "<how combined / fallback, or empty>"},
  "issues": [
    {"rank": 1, "issue": "<neutral name>", "testable": true,
     "position": "<short, plain: what they said they'd do>", "position_source": "<url>",
     "votes": [
       {"congress": 119, "session": 1, "roll_call": 372, "date": "2025-07-01",
        "bill": "H.R.1", "bill_title": "<short title>", "question": "<e.g. On passage>",
        "vote": "Yea|Nay", "consistent": true, "auto": false}
     ],
     "note": "<optional, one short line>"}
  ],
  "plan": null,
  "caveats": ["<one line each: judgment calls, unconfirmed votes, missing sources>"],
  "researched": "2026-11-04"
}
```
Rules for the file: exactly 10 issues, ranks 1–10. Bill format: "S.1383", "H.R.1", "H.J.Res.88", "S.J.Res.26" (no spaces). Write positions in plain, short language (under ~12 words), no adjectives. Keep caveats to the few that matter. Validate the JSON (e.g. `python3 -m json.tool <file>`) after writing.

Reply with only: the file path, the count of Delivered/Mixed/Contradicted/Not testable/No vote held as your data implies, and any caveat that seriously weakens the result.
