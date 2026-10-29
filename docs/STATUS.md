# KounOS build status

Updated at the end of every task or work session, committed with that work.

## Done

- **A01** scaffold (`api/` FastAPI + health route, `web/` Next.js placeholder shell, CI, docs) — [PR #2](https://github.com/RzanderR/KounOS/pull/2), merged as `25d99a4`. Reviewed by Muse Code (pass, in chat 2026-10-27); CI green ([run 40583572645](https://github.com/RzanderR/KounOS/actions/runs/40583572645)).
- Workflow simplification (direct human-Muse loop, briefs optional, spot-skill quality loop) — [PR #3](https://github.com/RzanderR/KounOS/pull/3), merged as `22533b8`.
- **A02–A08 single PR** — [PR #5](https://github.com/RzanderR/KounOS/pull/5) from `task/A08-screen` into `main`, covering A02–A08 instead of six stacked PRs (human direction 2026-10-28). All seven branches pushed.
- **A02** smoke test, live (2026-10-28, dev machine): `api/scripts/smoke_meta.py` runs against the real API (`muse-spark-1.3`), output validates against a Pydantic model, token usage printed (5,577 in / 1,852 out). Saved as `data/extractions/smoke_1232SA26Q0557.txt`. Caveat: the smoke schema sees only the specs PDF, so `solicitation_id` comes back empty; the full A05 run (both PDFs) returns it.
- **A03** contract (`task/A03-contract`): `api/app/schemas.py` (16 models + `KeyClause`), stub routers returning 501 with owning task, `api/scripts/generate_types.py` → `web/lib/kounos-types.ts`, typed `web/lib/api.ts` used by the home page.
- **A04** ingest (`task/A04-ingest`): `api/app/ingest.py` returns per-page text plus word boxes; `tests/test_ingest.py` pins the demo PDFs (specs 2 pages, terms 16).
- **A05** extraction, live (2026-10-28, dev machine): fixed the strict-schema bug the live call exposed (`key_clauses` was missing from `required`; new regression test pins it). `scripts/extract_solicitation.py` over both PDFs returns CLINs 0001 + 1001 (58 EA each, PTB8850LS41) and the 60-day delivery term. Stored as `data/extractions/1232SA26Q0557_extraction.json`. Caveat: the model's "sourcing clause" pick (OEM traceability) misses FAR 52.225-3 named in the answer key.
- **A06** citations (`task/A06-citations`): `api/app/cite.py` checks snippets with word-run matching plus a RapidFuzz fallback; verdicts are `verified`/`needs_review` with the real page and word boxes. Tests cover exact, hyphenated/line-broken, wrong-page and absent snippets.
- **A07** gap pass, live (2026-10-28, dev machine): 8 flags, including all three hand-checked `known_ambiguities` (delivery-date, cord-length and quantity conflicts) plus 5 more. Saved as `data/extractions/1232SA26Q0557_gaps.json` (evidence only, not served). Caveat: the model invents file names ("Solicitation 1232SA26Q0557.pdf") instead of the real attachment names.
- **A08** screen serves the stored live extraction (`task/A08-screen`): `GET /solicitations/1232SA26Q0557` builds from `data/extractions/1232SA26Q0557_extraction.json` with every passage re-checked by the A06 checker at request time (specs PDF first, then terms). 6 of 7 rows verify; the 1001 description is honestly `needs_review` (model prepended "Optional quantity - "). The hand-checked answer key is eval scoring input only, never displayed (set-aside/NAICS now omitted; pinned by test). Provenance note names `muse-spark-1.3` and the stored file.
- **web/** gates green on the dev machine (2026-10-28): `npm install` (also synced the stale `package-lock.json` with `package.json`), `typecheck`, `lint` (fixed one pre-existing `set-state-in-effect` error in the solicitation page by resetting viewer state in the click handler instead of an effect), `build`. API gates green: ruff, mypy, 54 pytest.
- API + web running on the dev machine: API `uvicorn app.main:app --port 8000` from `api/` → http://localhost:8000; web `npm run dev` from `web/` → http://localhost:3000. Both health-checked (API `/health` ok, `/solicitation` 200).
- **CI web-build fix (2026-10-29):** CI (Node 20) failed prerendering `/solicitation` with `TypeError: Promise.withResolvers is not a function` from pdf.js `node_utils.js`; local Node 22 masked it. The PDF viewer is now its own component (`web/app/solicitation/passage-viewer.tsx`, worker setup inside) loaded via `next/dynamic` with `{ ssr: false }`, so pdf.js never evaluates during prerender. Verified: clean `npm ci` + `lint` + `typecheck` + `build` green locally; server bundle has no executable `withResolvers` reference (only source maps).
- **Extraction sourcing field + snippet rule (2026-10-29):** `sourcing_clause` is now required in the extraction schema (FAR number + certificate); the prompt demands ~5-word surrounding-phrase snippets and checked (☒) clauses only. Live re-run finds FAR 52.225-3 (terms p.4) with the 52.225-4 certificate; every snippet is 16+ words. The A06 checker marks sub-4-word snippets `needs_review`. The A08 screen shows a new `sourcing` row; all 8 served rows verify (4 key clauses carry highlight boxes; requirement rows fuzzy-verify without boxes, so the screenshot should click a clause badge, e.g. delivery, for the highlight).
- Working agreement (human, 2026-10-29): from now on "verified" means the same commands CI runs passed (`npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`; API: `ruff check`, `mypy app`, `pytest`).
- Note: the dev web server had to be stopped for `npm ci` (Windows file locks) and was restarted after; a stale `.next` cache caused one dev-only 500, cleared by deleting `web/.next`.

## In progress

- **A02** smoke test (`task/A02-smoke-test`, covered by PR #5): code done and run live; merges with the single PR.
- **A08** screenshot (human): open http://localhost:3000/solicitation, click the "verified" badge on line 0001 (or any key-clause badge) and screenshot the highlighted passage in the PDF viewer. Then tick A08 in `TASKS.md`.
- Project-local skills installed (untracked, not for commit): caveman, ponytail, rtk, mattpocock set — 73 skills under `.agents/skills/` plus `skills-lock.json`.

## Blocked (on what or whom)

- Gate 1 confirmation tick (human). Evidence for it: live extraction with 6/7 rows `verified` (1001 description `needs_review`); gap pass reproduces all three known ambiguities.
- H03 remainder: two eval solicitations; H06: Tallgrass print-and-photograph; A01 screenshots need a dev machine with a browser.
- A01 home-page screenshots (API ok / unreachable) — needs a dev machine with a browser; neither sandbox nor CI can bind ports or run one.

## Decisions

- [D01](docs/DECISIONS.md#d01-2026-10-26-quote-amounts-and-sourcing-clause-rescale-to-the-real-solicitation): quote amounts and sourcing clause rescale to the real solicitation once H03 lands.
- [D02](docs/DECISIONS.md#d02-2026-10-26-gate-1-failure-swaps-in-an-eval-solicitation-before-screens): gate-1 failure swaps in an eval solicitation before screens.
- [D03](docs/DECISIONS.md#d03-2026-10-28-demo-quote-verdicts-and-sourcing-status-for-a11-and-a16a19-dates): Ninebark fails delivery (98d vs 60), Larkspur fails spec (PTB8850LS42, brand name only), Tallgrass passes; sourcing "needs confirmation" on all three (no country of origin); A16/A19 dates rescale to the 60-day requirement with the delay landing two days late.
- Single-agent loop, briefs optional, Muse reviews (human decision 2026-10-27; PR #3).
- Single PR for A02–A08 from `task/A08-screen` (human decision 2026-10-28; PR #5).

## Next

1. Human captures the A08 screenshot into `docs/screenshots/` (click the delivery clause badge for the highlight), then agent adds it to PR #5 and ticks A08 + A09 (quote files already in `data/quotes/docs/`).
2. After CI is green and the human merges: A10–A14, then A16–A20 for Gate 2. Hold triage (A34–A36) until Gate 2 is ticked.
3. Capture A01 screenshots on a dev machine.

Branches pushed: `task/A01-scaffold` (merged), `task/workflow-direct` (merged), `task/A02-smoke-test`, `task/A03-contract`, `task/A04-ingest`, `task/A05-extract`, `task/A06-citations`, `task/A07-gaps`, `task/A08-screen` (PR #5).
