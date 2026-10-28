# KounOS build status

Updated at the end of every task or work session, committed with that work.

## Done

- **A01** scaffold (`api/` FastAPI + health route, `web/` Next.js placeholder shell, CI, docs) — [PR #2](https://github.com/RzanderR/KounOS/pull/2), merged as `25d99a4`. Reviewed by Muse Code (pass, in chat 2026-10-27); CI green ([run 40583572645](https://github.com/RzanderR/KounOS/actions/runs/40583572645)).

## In progress

- Workflow simplification (`task/workflow-direct`, [PR #3](https://github.com/RzanderR/KounOS/pull/3), open): Claude orchestrator role removed, briefs optional, spot-skill quality loop. Needs merge.
- Project-local skills installed (untracked, not for commit): caveman, ponytail, rtk, mattpocock set — 73 skills under `.agents/skills/` plus `skills-lock.json`.

## Blocked (on what or whom)

- **A02** smoke test — on human: needs `MODEL_API_KEY` in `.env` (H02) and demo solicitation PDFs in `data/solicitations/` (H03). No A02 brief exists; spec gets written once inputs land.
- A01 home-page screenshots (API ok / unreachable) — needs a dev machine with a browser; neither sandbox nor CI can bind ports or run one.

## Decisions

- [D01](docs/DECISIONS.md#d01-2026-10-26-quote-amounts-and-sourcing-clause-rescale-to-the-real-solicitation): quote amounts and sourcing clause rescale to the real solicitation once H03 lands.
- [D02](docs/DECISIONS.md#d02-2026-10-26-gate-1-failure-swaps-in-an-eval-solicitation-before-screens): gate-1 failure swaps in an eval solicitation before screens.
- Single-agent loop, briefs optional, Muse reviews (human decision 2026-10-27, in chat; change itself is PR #3, not yet a DECISIONS.md entry).

## Next

1. Merge PR #3.
2. Human sends: demo contracts, `MODEL_API_KEY`, fictional quotes (plus written-permission yes/no for any real ones).
3. Draft A02 spec, build A02.
4. Capture A01 screenshots on a dev machine.

Branches pushed (even half done): `task/A01-scaffold` (merged), `task/workflow-direct` (open PR #3).
