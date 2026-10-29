# KounOS build status

Updated at the end of every task or work session, committed with that work.

## Done

- **A01** scaffold (`api/` FastAPI + health route, `web/` Next.js placeholder shell, CI, docs) — [PR #2](https://github.com/RzanderR/KounOS/pull/2), merged as `25d99a4`. Reviewed by Muse Code (pass, in chat 2026-10-27); CI green ([run 40583572645](https://github.com/RzanderR/KounOS/actions/runs/40583572645)).
- Workflow simplification (direct human-Muse loop, briefs optional, spot-skill quality loop) — [PR #3](https://github.com/RzanderR/KounOS/pull/3), merged as `22533b8`.

## In progress

- **A02** smoke test (`task/A02-smoke-test`, PR to open): `api/scripts/smoke_meta.py` runs against the real API, output validates against a Pydantic model, token usage printed. Needs merge; then A03-A08 in order.
- Project-local skills installed (untracked, not for commit): caveman, ponytail, rtk, mattpocock set — 73 skills under `.agents/skills/` plus `skills-lock.json`.

## Blocked (on what or whom)

- Gate 1 confirmation tick (human; running a day late, building through per human direction).
- H03 remainder: two eval solicitations; H06: Tallgrass print-and-photograph; A01 screenshots need a dev machine with a browser.
- A01 home-page screenshots (API ok / unreachable) — needs a dev machine with a browser; neither sandbox nor CI can bind ports or run one.

## Decisions

- [D01](docs/DECISIONS.md#d01-2026-10-26-quote-amounts-and-sourcing-clause-rescale-to-the-real-solicitation): quote amounts and sourcing clause rescale to the real solicitation once H03 lands.
- [D02](docs/DECISIONS.md#d02-2026-10-26-gate-1-failure-swaps-in-an-eval-solicitation-before-screens): gate-1 failure swaps in an eval solicitation before screens.
- Single-agent loop, briefs optional, Muse reviews (human decision 2026-10-27; PR #3).
- Single-agent loop, briefs optional, Muse reviews (human decision 2026-10-27, in chat; change itself is PR #3, not yet a DECISIONS.md entry).

## Next

1. Merge the A02 PR.
2. A03 schemas + routes, then A04-A08 in order (Gate 1 confirmation still owed).
3. Capture A01 screenshots on a dev machine.

Branches pushed (even half done): `task/A01-scaffold` (merged), `task/workflow-direct` (open PR #3).
