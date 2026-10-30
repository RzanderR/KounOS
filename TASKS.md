# TASKS.md

The backlog for the KounOS hackathon prototype, from the schedule in `docs/PLAN.md`. Work agent tasks in order. Tick a task (`[x]`) in the same pull request that completes it.

- **A** tasks are for coding agents.
- **H** tasks are for humans only. An agent may prepare drafts for them but must not do them or mark them done.
- **Gates** are checkpoints a human confirms. Do not start work past a gate until the human ticks it.

Deadline: **Wed, Nov 4, 2026, 9 PM ET.** Submit by 2 PM Phoenix time (5 PM ET).

---

## Mon Oct 26: set up and prove the API

- [ ] **H01** Create the public repo, choose and add a license, settle the teammate IP agreement, read the hackathon's IP terms.
- [ ] **H02** Get a Meta Model API key and put it in `.env` as `MODEL_API_KEY`.
- [ ] **H03** Find the demo solicitation award-first (civilian agency, supply-only, 2 to 4 line items, more than one offer, text-based PDF under 20 pages) plus two more for the eval. Put the PDFs in `data/solicitations/` and each award's total, date, offers received and source link in `data/awards/<solicitation-id>.json`.
- [ ] **H04** List 6 to 8 suppliers for budgetary quote requests.
- [ ] **H15** Company profile for `data/company_profile.json`: Koun's set-aside certifications and NAICS codes (as registered in SAM.gov), the product categories Koun sells, and a demonstration margin floor (not Koun's real one).
- [x] **A01** Scaffold the repo: `api/` (FastAPI with a health route and pytest), `web/` (Next.js with Tailwind and shadcn/ui), `.env.example`, `.gitignore`, and scripts for test, lint, typecheck and build. Fill in the commands section of `AGENTS.md`.
  - Done when: API tests pass, the web app builds, both start locally, and `AGENTS.md` lists the real commands.
- [x] **A02** Meta API smoke test: `api/scripts/smoke_meta.py` sends one PDF from `data/solicitations/` to `MODEL_READ` with a small JSON schema and prints the parsed result and token usage.
  - Done when: it runs against the real API, the output validates against a Pydantic model, and token usage is printed.
- [x] **A03** Contract first: Pydantic schemas for `CompanyProfile`, `Notice`, `FitAssessment`, `SourceRef`, `Requirement`, `Solicitation`, `AwardRecord`, `Quote`, `QuoteLine`, `SourcingDecision`, `Order`, `SupplierPO`, `Shipment`, `Invoice`, `Event`, `Flag`; API route stubs; TypeScript types generated for `web/`.
  - Done when: schemas and stubs are committed, OpenAPI docs load, and the web app imports the generated types.

## Tue Oct 27: read the solicitation

- [ ] **H05** Morning: send budgetary quote requests (no live order; ask for written permission to show quotes publicly). Afternoon: follow up by phone.
- [x] **A04** PDF ingest with pdfplumber: store each page's text and word bounding boxes.
  - Done when: a unit test on a sample PDF returns page count, page text and word coordinates.
- [x] **A05** Extraction: send the solicitation PDF to `MODEL_READ` with a schema that requires, per field, a page number and a verbatim snippet. Fields: line items, part number or NSN, quantity, unit, required delivery, key clauses.
  - Done when: the demo solicitation returns every line item, and output that fails validation is rejected, not stored.
- [x] **A06** Citation check with RapidFuzz: mark each field `verified` or `needs_review` and store the snippet's word boxes.
  - Done when: unit tests cover an exact snippet, a hyphenated or line-broken snippet, and a snippet on the wrong page.
- [x] **A07** Gap and ambiguity pass (`MODEL_READ`, reasoning effort high): flags such as a missing packaging spec, an unclear unit of issue or conflicting dates, each linked to its clause.
  - Done when: flags appear with clause links on the demo solicitation.
- [ ] **A08** Solicitation screen: requirements table with verified or needs-review badges; clicking a row jumps the PDF viewer to the highlighted passage; AI results labeled with their model.
  - Done when: a screenshot shows a highlighted passage after clicking a row.
- [ ] **A09** Fictional quote files from `data/quotes/*.json` (the three suppliers in `docs/PLAN.md`): a PDF quote and an email-screenshot image, each marked fictional.
  - Done when: both files exist and every number matches `docs/PLAN.md`.
- [ ] **H06** Print the third fictional quote (Brightline) and photograph it with a phone into `data/quotes/`.
- [ ] **H07** Hand-label expected fields for the three solicitations in `eval/expected/<solicitation-id>.json`. An agent may draft these; a human must check every value.
- [x] **Gate 1 (human):** the demo solicitation extracts with verified citations.

## Wed Oct 28: compare quotes

- [x] **A10** Quote extraction: one schema reads the PDF, the phone photo and the email screenshot.
  - Done when: all three quotes produce matching structured records.
- [x] **A11** Requirement checks in code: delivery date against the requirement, and the sourcing clause (for example country of origin) against each quote.
  - Done when: Alder fails on delivery, Cobalt fails on sourcing, Brightline passes.
- [x] **A12** Cost engine as pure, tested functions: landed cost, margin, lowest safe bid = landed cost ÷ (1 − target margin), cash exposure. Use `Decimal` for money.
  - Done when: tests reproduce the demo numbers: landed costs $79,348 / $78,764 / $82,070; margins 13.6% / 14.3% / 10.7% at the $91,880.12 award; lowest safe bid $91,189.92 for $82,070 at 10%.
- [x] **A13** Quote comparison screen: side-by-side quotes with pass or fail checks; a bid-price input that recomputes margins live; supplier selection; a one-page printable sourcing package.
  - Done when: changing the bid updates every margin without a model call.
- [x] **A14** Bid recommendation and award reveal: KounOS recommends "pursue at $X" (the lowest safe bid with the chosen supplier) or "pass, because..." (no compliant quote, or the margin floor can't be met), computed in code. It appears next to the actual award's total, date and offers received, with three caveats on screen (only totals are public; today's quotes reflect today's prices; one award is one data point).
  - Done when: it reads `data/awards/`, shows the recommendation and all three caveats, and a test shows "pass" when no quote is compliant.
- [ ] **H08** 5 pm quote cut-off. Add any real quotes that arrived with written permission, labeled real.
- [ ] **H16** Save the triage batch: 3 to 5 more civilian-agency notices in `data/notices/`, chosen so some fail for different reasons (a set-aside Koun doesn't hold, products Koun doesn't sell, too short a delivery window, too small a value). With the demo and eval solicitations, the batch is 6 to 8 notices.
- [ ] **A15** Eval script `python -m eval.run`: per-field accuracy and citation-verified rate for each labeled solicitation, printed as a Markdown table.
  - Done when: it runs on all three solicitations.

## Thu Oct 29: monitor the order

- [x] **A16** Seed data: the simulated award (award Nov 2, 2026; delivery due Dec 17; Brightline ships Nov 30, arrives Dec 3) plus four background orders in healthy or minor-issue states. `POST /demo/reset` restores it.
  - Done when: reset restores the exact seeded state, and every order screen shows the "Simulated award" banner.
- [x] **A17** Order timeline screen linking customer commitment, supplier PO, shipment, invoice and payment.
- [ ] **H09** Record the 20-second Brightline voicemail (backorder; shipping moves 16 days to Dec 16) into `data/voicemail/`, plus the same message as an email for backup.
- [ ] **A18** Voicemail to event: `MODEL_TRANSCRIBE` transcribes the audio, then `MODEL_READ` extracts supplier, PO, affected items, new ship date and confidence into an `Event`. The email backup goes through the same extraction.
  - Done when: the recorded voicemail produces an event with ship date Dec 16.
- [x] **A19** Rules engine in code: delivery slip past the required date, margin below a floor, cash exposure.
  - Done when: a test shows the delay event yields arrival Dec 19, two days late, and raises a flag.
- [ ] **A20** End-to-end demo-path test (browser automation) from upload to the delay flag.
  - Done when: it passes locally from a reset.
- [ ] **Gate 2 (human):** the core story (read, compare, recommend, monitor) runs end to end, rough edges allowed. Stretch work starts only after this.

## Contract file (after Gate 2, D05; triage A34–A36 stays)

- [ ] **A37** Lineage API: one endpoint per order returning the linked picture (solicitation → requirements → quotes + checks → cost/bid → award → order → events → cash) with per-number lineage — source doc + page for extracted numbers (reusing A06 citations and quote-extraction refs), calculation + inputs for computed numbers (reusing the A12 cost engine).
  - Done when: every number on the demo order resolves to a doc page or a named calculation with inputs, covered by a test.
- [ ] **A21** (existing, prerequisite for A39) impact analysis on `MODEL_IMPACT` with priced options.
- [ ] **A38** Contract-file screen: the linked picture on one screen; clicking any number opens its lineage (doc passage with highlight, or calculation with inputs).
  - Done when: a screenshot shows the linked picture and one open lineage.
- [ ] **A39** Delay ripple: when the Tallgrass delay event lands, the screen first shows the ripple across the linked picture (date, margin, deposit/cash, risk), then the A21 Muse Wonder options.
  - Done when: the e2e delay path asserts the ripple figures before the options.
- [ ] **A40** Extend the end-to-end test to the contract file (lineage click + ripple), passing locally from a reset and on the live link from a fresh browser.

## Fri Oct 30: triage and assist

- [ ] **A34** Fit facts: for each notice in the triage batch, `MODEL_READ` extracts set-aside, product category, quantities, delivery window, estimated value and any competition signal, each with a page and snippet checked by the A06 citation check.
  - Done when: every notice in the batch produces a validated record, with fields not found marked "not stated" rather than guessed.
- [ ] **A35** Fit scoring in code against `data/company_profile.json`: set-aside eligibility, product category match, delivery feasibility, value band and competition, weighted by the profile, giving "pursue" or "pass" with a reason per factor.
  - Done when: tests cover a pass for each reason, and the demo solicitation scores "pursue".
- [ ] **A36** Triage screen: the batch ranked by fit, pursue or pass with per-factor reasons and citations, the model label on extracted facts; opening a notice goes to the solicitation screen.
  - Done when: a screenshot shows the ranked batch and one notice's reasons.

- [ ] **A21** Read-only agent tools (order, commitments, alternate quotes, margin, cash gap) and the impact analysis on `MODEL_IMPACT` with priced options: expedite (about $1,100 overnight, on time, margin 13.1% to 11.1%), request a two-day extension, partial shipment if allowed, and why switching suppliers fails. Falls back to `MODEL_READ` if `MODEL_IMPACT` is unavailable.
  - Done when: the analysis names all four options with numbers that match the cost engine.
- [ ] **A22** Number-grounding check: reject any explanation containing a figure no tool returned, and show the plain rule-based flag instead.
  - Done when: a test with an invented number is rejected.
- [ ] **A23** Draft note to the contracting officer or supplier for a person to edit. No send capability anywhere.
- [ ] **A24** Ask KounOS panel: answers "Which orders need attention today?" from read-only tools across the five seeded orders, linking every record used.
- [ ] **H10** Create hosting accounts and secrets for the front end and API.

## Sat Oct 31: deploy, polish and stretch

- [ ] **A25** Deploy the front end and API; run the end-to-end test against the live link.
- [ ] **A26** Polish the four screens, including loading and error states; run `/taste` on each.
- [ ] **A27** Replay mode (`DEMO_MODE=replay`) serving stored responses for the scripted path, with a visible indicator in the UI.
- [ ] **A28** DROPPED by D05 (room for the contract file): shutdown scenario toggle.

## Sun Nov 1: harden

- [ ] **A29** DROPPED by D05 (room for the contract file): award backtest.
- [ ] **A30** Fix every blocking issue from reviews; extend the end-to-end test to start at triage; it passes on the live link from a fresh browser.
- [ ] **A31** README sync: architecture, model map, "Built during the hackathon" list, third-party table, eval table.

## Mon Nov 2: rehearse and freeze

- [ ] **A32** Final eval run; fill in the README results tables.
- [ ] **H11** Rehearse the demo script twice against the live link.
- [ ] **Gate 3 (human):** feature freeze at end of day. After this, only bug fixes a human approves.

## Tue Nov 3: record the video

- [ ] **H12** Record the video, edit to 3 minutes, add captions.
- [ ] **A33** Final repo check: secret scan clean, license present, third-party table complete, every data file's provenance listed, no real business data.

## Wed Nov 4: submit

- [ ] **H13** Watch the final video once more on a phone.
- [ ] **H14** Submit by 2 PM Phoenix time (5 PM ET), four hours before the 9 PM ET deadline, and confirm it went through.
