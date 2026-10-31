# KounOS design decisions

Settled decisions future tasks depend on. See `docs/PLAN.md` (baseline) and `TASKS.md` (backlog).

## D01 (2026-10-26): Quote amounts and sourcing clause rescale to the real solicitation

- Decision: The dollar amounts and sourcing-clause check in A09 / A11 / A12 are placeholders from `docs/PLAN.md` (Alder $42,100 / Cobalt $44,150 / Brightline $46,900 at a $54,000 bid; domestic-sourcing example). They must be rescaled to the real demo solicitation once H03 lands.
- Why: PLAN § "Demo data kit" says the example set assumes a $54,000 bid and must be scaled to the award picked; the sourcing clause must use whichever the real solicitation has.
- Impact: A09 fictional quotes, A11 requirement checks (Alder late / Cobalt non-compliant / Brightline pass), A12 cost-engine test vectors.

## D02 (2026-10-26): Gate 1 failure swaps in an eval solicitation before screens

- Decision: If the demo solicitation fails Gate 1 (no verified citations), swap to an eval solicitation before building screens (A08 onward).
- Why: PLAN risks table lists extraction errors mitigated by document choice; building screens on an unreadable solicitation wastes Tue–Wed.
- Impact: Gate 1; A08 solicitation screen; A05–A07 extraction work.

## D03 (2026-10-28): Demo quote verdicts and sourcing status for A11 (and A16/A19 dates)

- Decision: Ninebark fails on delivery (up to 98 days lead time vs. the solicitation's 60-day delivery requirement). Larkspur fails on spec (quotes PTB8850LS42 with a 208-240V cord; the solicitation requires PTB8850LS41 with a 10-foot cord and 5-15P plug, brand name only, so "equal" products are technically unacceptable). Tallgrass passes every requirement. Sourcing under FAR 52.225-3 (Buy American) reads "needs confirmation" on all three quotes, since no quote states a country of origin.
- Why: A11 requirement checks must encode exactly these verdicts; a missing country-of-origin is not a pass, so code must flag it for a person to confirm rather than guess.
- Impact: A11 requirement checks (delivery + brand-name/spec + sourcing-needs-confirmation); A16/A19 seed data: rescale the simulated-award dates to the 60-day delivery requirement and keep the Tallgrass delay landing two days late.

## D04 (2026-10-30): Live model runs stay on the contributor tier for cost

- Decision: `MODEL_READ` remains `muse-spark-1.3-contributor` in `.env`. The stored live outputs (smoke, extraction, gap pass) stand as-is; nothing is re-run on another tier.
- Why: Owner direction — the contributor tier is an intentional cost choice, not a misconfiguration.
- Impact: A02/A05/A07 provenance notes keep naming the contributor model; future live runs use the same tier unless a new decision says otherwise.

## D05 (2026-10-30): The demo is a linked contract file, not a file reader

- Decision: After Gate 2, the product direction is one linked picture per contract and order, Palantir-style: solicitation → requirements → quotes + checks → cost/bid → award → order → events → cash on one screen. Every number is clickable to its lineage (source doc + page, or the calculation and its inputs). A delay event shows its ripple across the linked picture (date, margin, deposit/cash, risk) before the Muse Wonder options. The demo is about connecting the information and deciding, not about reading files.
- Why: Owner direction — the memorable moments (award reveal, delay rescue) are connection moments; the file-by-file screens prove extraction but not understanding.
- Impact: New contract-file view + lineage + ripple tasks (A37+); A28/A29 stretch dropped to make room; triage (A34–A36) stays; PLAN scope/stretch and the order-monitor story update accordingly.
