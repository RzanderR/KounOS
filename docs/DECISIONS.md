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
