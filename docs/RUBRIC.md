# Judging rubric and review scorecard

Use this file to review any change, branch or the whole project. Score from evidence you can point to (a file and line, test output, eval numbers, a screenshot), never from claims in a PR description or a commit message.

## Hackathon judging criteria

| Criterion | Weight | What the judges ask |
| --- | --- | --- |
| Impact | 30% | What's the real-world potential? Who benefits, and how much does it matter? Could this become something people use? Does it fit one of the hackathon's problem statements? |
| Use of Meta AI tooling | 25% | How creatively did the team use Meta's AI tooling? Did they go beyond a basic integration? Did they surface capabilities that surprised the judges? |
| Technical depth and execution | 20% | Is the engineering sound and thoughtfully refined? Does it feel thought through with real craft? |
| Demo | 25% | Is it a working, impressive demo? Does the product hold up live? Is the demo video genuinely good to watch? |

## What winning looks like for KounOS

| Criterion | Strong evidence |
| --- | --- |
| Impact | The problem is concrete: a late delivery can cost a contract and a past-performance rating. The demo runs on a real, civilian-agency solicitation and checks the bid against the real award. The README names who benefits and the problem statement. |
| Use of Meta AI tooling | Three Meta models doing distinct jobs: native PDF reading with citations that code verifies; one schema reading PDF, photo and screenshot quotes; voicemail transcription into a structured event; a Muse Wonder tool-calling agent whose numbers all come from tools. Each AI result in the UI is labeled with its model. |
| Technical depth and execution | Deterministic, unit-tested math for costs, margins, lowest safe bid, dates and cash. Schema-validated model output. Citation checks. Number grounding for explanations. Untrusted documents treated as data. Model IDs in config with a fallback. An eval with real numbers in the README. |
| Demo | One continuous story: read, compare, price, reveal against the award, simulated award, voicemail delay, priced recovery options, Ask KounOS. Seeded data, a reset button, a replay mode that says when it's on, and an end-to-end test that passes on the live link. |

## Rules that disqualify a project

A review must fail any change that breaks one of these.

1. **Public repository.** The repository must be public at submission.
2. **New work only.** What is presented must have been built during the event, and judges must be able to tell what was built during the hackathon. Pre-existing code must be isolated and listed.
3. **Demo shows only hackathon-built work.** The video and live demo highlight only features built during the event.
4. **Rights to everything.** No code, data or assets the team has no rights to. No real supplier quotes without written permission. Only permissively licensed dependencies.
5. **Legal, ethical and platform policies.** Nothing that violates them.
6. **No politics or war content.** Civilian-agency material only.
7. **Team of four or fewer.**

Also blocking for this project: secrets in git, real Koun business data, a missing "Simulated award" label, a model-produced number shown as fact, any code path that sends, submits or acts outside the app.

## Score scale (per criterion)

| Score | Meaning |
| --- | --- |
| 5 | A judge would remember it. Clear evidence, nothing to fix. |
| 4 | Solid and demo-ready, minor polish left. |
| 3 | Works, but a judge would notice a gap. |
| 2 | Partly works or is hard to see in the demo. |
| 1 | Missing or broken. |

Score only the criteria a change affects; mark the rest `null`.

## Review procedure

1. Read the task's "Done when" line in `TASKS.md` and the relevant part of `docs/PLAN.md`.
2. Read the diff. Run or read the results of tests, lint, typecheck, build, and the eval or end-to-end test where relevant.
3. Check every disqualifying rule above.
4. Check every acceptance criterion: pass or fail, with evidence.
5. Score the affected criteria.
6. List blocking issues (must fix before merge) separately from suggestions.
7. Pass only if every acceptance criterion passes, no rule is broken, and there are no blocking issues.

## Scorecard format

Return the review as JSON in this shape:

```json
{
  "task": "A12",
  "verdict": "pass | fail",
  "acceptance": [
    {"criterion": "Lowest safe bid for $46,900 at 10% margin is $52,111", "result": "pass", "evidence": "api/tests/test_cost.py::test_lowest_safe_bid"}
  ],
  "rules": [
    {"rule": "No secrets in git", "result": "pass", "evidence": "secret scan clean"}
  ],
  "scores": {
    "impact": null,
    "meta_ai": null,
    "technical": 4,
    "demo": null
  },
  "blocking": [
    "Margin rounds before comparison; use Decimal until display (api/app/cost.py:41)"
  ],
  "suggestions": [
    "Add a test for zero freight"
  ]
}
```
