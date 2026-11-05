# Research queue

Work 4 senators per turn (search budget is ~200 per turn, shared). Each new senator: Agent (general-purpose) with prompt
"Read /home/claude/promise-ledger/RESEARCH.md and follow it exactly for: Sen. <Name> (<P>-<ST>), elected <year>, term <start> to <end>. File id: <id>"
Class I: elected 2024, term 2025-01-03 to 2031-01-03. Class III: elected 2022, term 2023-01-03 to 2029-01-03.

## Finish pass (drafts from batch 1; continue the same agent with SendMessage, or re-run if the agent is gone)
Message: "Continue with a fresh search budget (max ~45 searches). Re-read /home/claude/promise-ledger/RESEARCH.md (updated). Finish the issues you could not research, fix weak positions, set testable null for anything still unresearched, update the file, and remove \"status\": \"draft\" if all 10 issues are researched."
- [x] az-gallego (agent aeeedcd67535e4021)
- [x] ca-schiff (a0ef637f53441b896)
- [x] ct-murphy (a6e5011174a5305db)
- [x] de-blunt-rochester (acfd9b37d825a1cd0)
- [x] fl-scott (a7d080e145c877e35)
- [x] hi-hirono (a6b74d70f67839d00)
- [x] in-banks (a2d5205b0fcc3fa68)
- [x] me-king (afd6d5e89744694b4)
- [x] md-alsobrooks (af998e42543ea12ad)
- [x] ma-warren (a834673f9dfb0d7db)
- [x] mi-slotkin (a72bd2bb70343206e)
- [x] mn-klobuchar (ada89eefede2fab3e)
- [x] ms-wicker (a2924661f370aff6a)

## New, class I (2024)
- [x] mo-hawley Josh Hawley R-MO
- [x] mt-sheehy Tim Sheehy R-MT
- [x] ne-fischer Deb Fischer R-NE
- [x] nv-rosen Jacky Rosen D-NV
- [x] nj-kim Andy Kim D-NJ
- [x] nm-heinrich Martin Heinrich D-NM
- [x] ny-gillibrand Kirsten Gillibrand D-NY
- [x] nd-cramer Kevin Cramer R-ND
- [x] oh-moreno Bernie Moreno R-OH
- [x] pa-mccormick Dave McCormick R-PA
- [x] ri-whitehouse Sheldon Whitehouse D-RI
- [x] tn-blackburn Marsha Blackburn R-TN
- [x] tx-cruz Ted Cruz R-TX
- [x] ut-curtis John Curtis R-UT
- [x] vt-sanders Bernie Sanders I-VT
- [x] va-kaine Tim Kaine D-VA
- [x] wa-cantwell Maria Cantwell D-WA
- [x] wv-justice Jim Justice R-WV
- [x] wi-baldwin Tammy Baldwin D-WI
- [x] wy-barrasso John Barrasso R-WY

## New, class III (2022)
- [x] al-britt Katie Britt R-AL
- [x] ak-murkowski Lisa Murkowski R-AK
- [x] az-kelly Mark Kelly D-AZ
- [x] ar-boozman John Boozman R-AR
- [x] ca-padilla Alex Padilla D-CA
- [x] co-bennet Michael Bennet D-CO
- [x] ct-blumenthal Richard Blumenthal D-CT
- [x] ga-warnock Raphael Warnock D-GA
- [x] hi-schatz Brian Schatz D-HI
- [x] id-crapo Mike Crapo R-ID
- [x] il-duckworth Tammy Duckworth D-IL
- [x] in-young Todd Young R-IN
- [x] ia-grassley Chuck Grassley R-IA
- [x] ks-moran Jerry Moran R-KS
- [x] ky-paul Rand Paul R-KY
- [x] la-kennedy John Kennedy R-LA
- [x] md-van-hollen Chris Van Hollen D-MD
- [x] mo-schmitt Eric Schmitt R-MO
- [x] nv-cortez-masto Catherine Cortez Masto D-NV
- [x] ny-schumer Chuck Schumer D-NY
- [x] nc-budd Ted Budd R-NC
- [x] nd-hoeven John Hoeven R-ND
- [x] ok-lankford James Lankford R-OK
- [x] or-wyden Ron Wyden D-OR
- [x] pa-fetterman John Fetterman D-PA
- [x] sc-scott Tim Scott R-SC
- [x] sd-thune John Thune R-SD
- [x] ut-lee Mike Lee R-UT
- [x] vt-welch Peter Welch D-VT
- [x] wa-murray Patty Murray D-WA
- [x] wi-johnson Ron Johnson R-WI

## Later: 2026 class (35 seats incl. FL and OH specials)
Lock winners' plans once results are final; re-elected incumbents also get a delivery score for the term that just ended.

## Consistency pass (after all senators are in)
- H.R.1 (RC 372) is applied unevenly: some files count a Nay as Contradicting a border-funding / LIHTC / child-tax-credit position, others leave the issue as No vote held (Kaine, Murphy, Blunt Rochester, Hassan-immigration). Pick one rule and apply it to every file.
- SAVE America Act vs. a 2022 pledge to oppose federalizing elections: ks-moran scores it Contradicted, ar-boozman leaves it unscored. Same rule needed. (nd-hoeven also scored Contradicted.)
- Procedural Nays to enable reconsideration (e.g. Schumer on RC 211) are scored consistent by hand; make sure verify_votes never flips them.
- Plan sourcing: ma-markey is 10/10 Concrete mostly from "YES" answers on an advocacy-group questionnaire; decide whether questionnaire checkboxes count as Concrete (affects others using Ballotpedia/iVoterGuide surveys too).
- nm-lujan and or-merkley delivery: agents used only ~9-10 searches and took roll call numbers/dates from memory; re-check after verify_votes runs (or re-research).

## 2026 class: lock winners' plans (closed races, as of Nov 5)
Plan brief: "Read /home/claude/politician-promises/PLAN.md and follow it exactly for: <Name> (<P>-<ST>), won the 2026 U.S. Senate race. File id: <id>"
Delivery brief for re-elected incumbents (separate agent, writes data/senators/): "Read /home/claude/politician-promises/RESEARCH.md and follow it exactly for: Sen. <Name> (<P>-<ST>), elected <year>, term <start> to 2027-01-03. File id: <id>"
Not called yet (do later): AK (Sullivan vs Peltola), MS (Hyde-Smith vs Colom).

### Extend existing locked plans from 8 to 10 issues
Message to a fresh agent: "In /home/claude/politician-promises/data/senators/<id>.json the `plan` has 8 issues. Using the same poll named in plan.issue_poll (or the closest 2026 state poll if it has fewer items, noted), add ranks 9 and 10 per /home/claude/politician-promises/PLAN.md rules, rating this candidate's 2026 plan on each. Edit only plan.issues; keep everything else. Max ~20 searches. Validate JSON. Reply with the two added issues and ratings."
- [x] ext:sc-andrews
- [x] ext:mi-el-sayed
- [x] ext:nc-cooper
- [x] ext:nh-pappas
- [x] ext:ia-turek

### New senators (plan only)
- [x] plan:al-moore Barry Moore R-AL
- [x] plan:il-stratton Juliana Stratton D-IL
- [x] plan:ks-hamilton Adam Hamilton D-KS
- [x] plan:ky-barr Andy Barr R-KY
- [x] plan:la-letlow Julia Letlow R-LA
- [x] plan:me-jackson Troy Jackson D-ME
- [x] plan:mn-flanagan Peggy Flanagan D-MN
- [x] plan:mt-alme Kurt Alme R-MT
- [x] plan:oh-brown Sherrod Brown D-OH (special; term 2027-01-03 to 2029-01-03)
- [x] plan:ok-hern Kevin Hern R-OK
- [x] plan:tx-talarico James Talarico D-TX
- [x] plan:wy-hageman Harriet Hageman R-WY
- [x] plan:fl-moody Ashley Moody R-FL (special; appointed 2025, no prior campaign for this seat; term 2027-01-03 to 2029-01-03)

### Re-elected incumbents (plan + delivery for the term now ending)
- [x] plan:ar-cotton Tom Cotton R-AR
- [x] del:ar-cotton elected 2020, term 2021-01-03
- [x] plan:co-hickenlooper John Hickenlooper D-CO
- [x] del:co-hickenlooper elected 2020, term 2021-01-03
- [x] plan:de-coons Chris Coons D-DE
- [x] del:de-coons elected 2020, term 2021-01-03
- [x] plan:ga-ossoff Jon Ossoff D-GA
- [x] del:ga-ossoff elected 2020 (Jan 2021 runoff), term 2021-01-20
- [x] plan:id-risch Jim Risch R-ID
- [x] del:id-risch elected 2020, term 2021-01-03
- [x] plan:ma-markey Ed Markey D-MA
- [x] del:ma-markey elected 2020, term 2021-01-03
- [x] plan:ne-ricketts Pete Ricketts R-NE
- [x] del:ne-ricketts elected 2024 special, term 2024-11-05
- [x] plan:nj-booker Cory Booker D-NJ
- [x] del:nj-booker elected 2020, term 2021-01-03
- [x] plan:nm-lujan Ben Ray Luján D-NM
- [x] del:nm-lujan elected 2020, term 2021-01-03
- [x] plan:or-merkley Jeff Merkley D-OR
- [x] del:or-merkley elected 2020, term 2021-01-03
- [x] plan:ri-reed Jack Reed D-RI
- [x] del:ri-reed elected 2020, term 2021-01-03
- [x] plan:sd-rounds Mike Rounds R-SD
- [x] del:sd-rounds elected 2020, term 2021-01-03
- [x] plan:tn-hagerty Bill Hagerty R-TN
- [x] del:tn-hagerty elected 2020, term 2021-01-03
- [x] plan:va-warner Mark Warner D-VA
- [x] del:va-warner elected 2020, term 2021-01-03
- [x] plan:wv-capito Shelley Moore Capito R-WV
- [x] del:wv-capito elected 2020, term 2021-01-03
