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
- [ ] **A01** Scaffold the repo: `api/` (FastAPI with a health route and pytest), `web/` (Next.js with Tailwind and shadcn/ui), `.env.example`, `.gitignore`, and scripts for test, lint, typecheck and build. Fill in the commands section of `AGENTS.md`.
  - Done when: API tests pass, the web app builds, both start locally, and `AGENTS.md` lists the real commands.
- [ ] **A02** Meta API smoke test: `api/scripts/smoke_meta.py` sends one PDF from `data/solicitations/` to `MODEL_READ` with a small JSON schema and prints the parsed result and token usage.
  - Done when: it runs against the real API, the output validates against a Pydantic model, and token usage is printed.
- [ ] **A03** Contract first: Pydantic schemas for `SourceRef`, `Requirement`, `Solicitation`, `AwardRecord`, `Quote`, `QuoteLine`, `SourcingDecision`, `Order`, `SupplierPO`, `Shipment`, `Invoice`, `Event`, `Flag`; API route stubs; TypeScript types generated for `web/`.
  - Done when: schemas and stubs are committed, OpenAPI docs load, and the web app imports the generated types.

## Tue Oct 27: read the solicitation

- [ ] **H05** Morning: send budgetary quote requests (no live order; ask for written permission to show quotes publicly). Afternoon: follow up by phone.
- [ ] **A04** PDF ingest with pdfplumber: store each page's text and word bounding boxes.
  - Done when: a unit test on a sample PDF returns page count, page text and word coordinates.
- [ ] **A05** Extraction: send the solicitation PDF to `MODEL_READ` with a schema that requires, per field, a page number and a verbatim snippet. Fields: line items, part number or NSN, quantity, unit, required delivery, key clauses.
  - Done when: the demo solicitation returns every line item, and output that fails validation is rejected, not stored.
- [ ] **A06** Citation check with RapidFuzz: mark each field `verified` or `needs_review` and store the snippet's word boxes.
  - Done when: unit tests cover an exact snippet, a hyphenated or line-broken snippet, and a snippet on the wrong page.
- [ ] **A07** Gap and ambiguity pass (`MODEL_READ`, reasoning effort high): flags such as a missing packaging spec, an unclear unit of issue or conflicting dates, each linked to its clause.
  - Done when: flags appear with clause links on the demo solicitation.
- [ ] **A08** Solicitation screen: requirements table with verified or needs-review badges; clicking a row jumps the PDF viewer to the highlighted passage; AI results labeled with their model.
  - Done when: a screenshot shows a highlighted passage after clicking a row.
- [ ] **A09** Fictional quote files from `data/quotes/*.json` (the three suppliers in `docs/PLAN.md`): a PDF quote and an email-screenshot image, each marked fictional.
  - Done when: both files exist and every number matches `docs/PLAN.md`.
- [ ] **H06** Print the third fictional quote (Brightline) and photograph it with a phone into `data/quotes/`.
- [ ] **H07** Hand-label expected fields for the three solicitations in `eval/expected/<solicitation-id>.json`. An agent may draft these; a human must check every value.
- [ ] **Gate 1 (human):** the demo solicitation extracts with verified citations.

## Wed Oct 28: compare quotes

- [ ] **A10** Quote extraction: one schema reads the PDF, the phone photo and the email screenshot.
  - Done when: all three quotes produce matching structured records.
- [ ] **A11** Requirement checks in code: delivery date against the requirement, and the sourcing clause (for example country of origin) against each quote.
  - Done when: Alder fails on delivery, Cobalt fails on sourcing, Brightline passes.
- [ ] **A12** Cost engine as pure, tested functions: landed cost, margin, lowest safe bid = landed cost ÷ (1 − target margin), cash exposure. Use `Decimal` for money.
  - Done when: tests reproduce the plan's numbers: landed costs $42,100 / $44,150 / $46,900; margins 22.0% / 18.2% / 13.1% at a $54,000 bid; lowest safe bid $52,111 for $46,900 at 10%.
- [ ] **A13** Quote comparison screen: side-by-side quotes with pass or fail checks; a bid-price input that recomputes margins live; supplier selection; a one-page printable sourcing package.
  - Done when: changing the bid updates every margin without a model call.
- [ ] **A14** Award reveal view: KounOS's lowest safe bid next to the actual award's total, date and offers received, with three caveats on screen (only totals are public; today's quotes reflect today's prices; one award is one data point).
  - Done when: it reads `data/awards/` and shows all three caveats.
- [ ] **H08** 5 pm quote cut-off. Add any real quotes that arrived with written permission, labeled real.
- [ ] **A15** Eval script `python -m eval.run`: per-field accuracy and citation-verified rate for each labeled solicitation, printed as a Markdown table.
  - Done when: it runs on all three solicitations.

## Thu Oct 29: monitor the order

- [ ] **A16** Seed data: the simulated award (award Nov 2, 2026; delivery due Dec 17; Brightline ships Nov 30, arrives Dec 3) plus four background orders in healthy or minor-issue states. `POST /demo/reset` restores it.
  - Done when: reset restores the exact seeded state, and every order screen shows the "Simulated award" banner.
- [ ] **A17** Order timeline screen linking customer commitment, supplier PO, shipment, invoice and payment.
- [ ] **H09** Record the 20-second Brightline voicemail (backorder; shipping moves 16 days to Dec 16) into `data/voicemail/`, plus the same message as an email for backup.
- [ ] **A18** Voicemail to event: `MODEL_TRANSCRIBE` transcribes the audio, then `MODEL_READ` extracts supplier, PO, affected items, new ship date and confidence into an `Event`. The email backup goes through the same extraction.
  - Done when: the recorded voicemail produces an event with ship date Dec 16.
- [ ] **A19** Rules engine in code: delivery slip past the required date, margin below a floor, cash exposure.
  - Done when: a test shows the delay event yields arrival Dec 19, two days late, and raises a flag.
- [ ] **A20** End-to-end demo-path test (browser automation) from upload to the delay flag.
  - Done when: it passes locally from a reset.
- [ ] **Gate 2 (human):** the whole story runs end to end, rough edges allowed. Stretch work starts only after this.

## Fri Oct 30: explain and assist

- [ ] **A21** Read-only agent tools (order, commitments, alternate quotes, margin, cash gap) and the impact analysis on `MODEL_IMPACT` with priced options: expedite (about $1,100 overnight, on time, margin 13.1% to 11.1%), request a two-day extension, partial shipment if allowed, and why switching suppliers fails. Falls back to `MODEL_READ` if `MODEL_IMPACT` is unavailable.
  - Done when: the analysis names all four options with numbers that match the cost engine.
- [ ] **A22** Number-grounding check: reject any explanation containing a figure no tool returned, and show the plain rule-based flag instead.
  - Done when: a test with an invented number is rejected.
- [ ] **A23** Draft note to the contracting officer or supplier for a person to edit. No send capability anywhere.
- [ ] **A24** Ask KounOS panel: answers "Which orders need attention today?" from read-only tools across the five seeded orders, linking every record used.
- [ ] **H10** Create hosting accounts and secrets for the front end and API.
- [ ] **A25** Deploy the front end and API; run the end-to-end test against the live link.

## Sat Oct 31: polish and stretch

- [ ] **A26** Polish the three screens, including loading and error states; run `/taste` on each.
- [ ] **A27** Replay mode (`DEMO_MODE=replay`) serving stored responses for the scripted path, with a visible indicator in the UI.
- [ ] **A28** Stretch, only after Gate 2: shutdown scenario toggle that pushes government payment dates out and shows cash exposure per order.

## Sun Nov 1: harden

- [ ] **A29** Stretch: award backtest on 5 to 10 more past awards using public list prices; chart lowest safe bid against each actual award for the README.
- [ ] **A30** Fix every blocking issue from reviews; the end-to-end test passes on the live link from a fresh browser.
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
