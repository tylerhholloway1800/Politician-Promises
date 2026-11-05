# Politician Promises

Grades U.S. senators on whether their floor votes match what they promised when they ran.

- **Issue list:** the top 10 issues in the senator's state when they were elected, from public polling.
- **Promises:** their stated campaign position on each issue, locked on Election Day.
- **Grade:** Delivered 1, Mixed ½, Contradicted 0, Not testable 0. Issues that never got a floor vote are left out. Votes only.
- **Newly elected senators:** their plan is scored on how many top issues have a concrete plan, then graded on votes once their term starts.

Full method: `templates/method.html` (published as the site's Method page).

## How it runs

A GitHub Action (`.github/workflows/daily.yml`) runs twice a day:

1. Checks every researched vote against senate.gov and corrects mistakes.
2. Applies review issues you've labeled `approve`.
3. Pulls new Senate roll calls, matches them to locked promises with Claude, and updates grades. Unsure matches become GitHub issues labeled `review` instead of going live.
4. Commits data changes, rebuilds the site, deploys to GitHub Pages, and posts grade moves to X.

A senator's grade stays hidden ("research in progress") until all 10 issues are researched and every vote is checked against senate.gov.

## One-time setup

1. **Pages:** Settings → Pages → Source: **GitHub Actions**.
2. **Anthropic key** (for vote matching): Settings → Secrets and variables → Actions → New repository secret → `ANTHROPIC_API_KEY`.
3. **Site URL** (for links in posts): same page, Variables tab → `SITE_URL` = `https://tylerhholloway1800.github.io/Politician-Promises`.
4. **X posting (optional):** secrets `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET`. Without them, posts are skipped. Optional variable `POST_LETTER_CHANGES_ONLY` = `true` to post only when a letter grade changes.
5. **Labels:** create `review` and `approve` (Issues → Labels).
6. Run it once: Actions → *Update votes and publish* → Run workflow.

## Working on it locally

```
pip install -r requirements.txt
python scripts/build.py          # builds site/ from data/
python scripts/update_votes.py --dry-run
```

- `data/senators/<id>.json`: one file per senator (format: see `RESEARCH.md`, example `nh-hassan.json`).
- `data/changes.json`: every grade move.
- `RESEARCH.md`: the brief used to research each senator. `QUEUE.md`: research still to do.

Corrections: open an issue.
