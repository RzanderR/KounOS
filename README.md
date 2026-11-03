# KounOS

**An AI operating system for small government suppliers.** KounOS helps a supplier decide which contracts are worth pursuing, then keeps every awarded order on track until it's delivered and paid. It reads the solicitation worth chasing, compares supplier quotes, recommends whether to bid and at what price, and watches the order after award, so a supplier delay gets caught before it becomes a missed delivery. (Triage of notice batches is not in this prototype: the screen exists but the batch hasn't landed, so it shows "No notices yet".)

Built by Koun Logistics LLC for **[HACKATHON NAME]** on Meta's Muse models through the Meta Model API.

**[▶ Demo video](TODO)** · **[Live demo](https://kounos-web.vercel.app)** · **[What we built this week](#built-during-the-hackathon)**

> **Hackathon prototype.** Everything in this repository was built between October 26 and November 4, 2026. The solicitation and award record are public federal documents. Suppliers, quotes, orders and the delay email are fictional unless marked otherwise, and the awarded order is simulated. KounOS never submits bids or sends messages; people do.

<!-- TODO before submission: the only placeholders left are [HACKATHON NAME], the problem statement, the demo video link, Team names, [LICENSE NAME], and "Real supplier quotes". Everything else below matches the code. -->

---

## For judges

| Criterion | Where to look |
| --- | --- |
| **Impact** | [The problem](#the-problem) · [Who benefits](#who-benefits) · [Where it's going](#where-its-going) · [Checked against a real award](#checked-against-a-real-award) |
| **Use of Meta AI tooling** | [How we use Meta AI](#how-we-use-meta-ai) |
| **Technical depth and execution** | [Architecture](#architecture) · [Engineering decisions](#engineering-decisions) · [Validation](#validation) |
| **Demo** | [Demo](#demo) · [Run it locally](#run-it-locally) |
| **Rules** | [Built during the hackathon](#built-during-the-hackathon) · [Third-party software and data](#third-party-software-and-data) |

---

## The problem

Small businesses that supply the federal government do two hard jobs with scattered information.

**Deciding what to pursue.** New notices arrive constantly, and most are a poor fit: the wrong set-aside, products the company doesn't sell, a delivery window no supplier can meet. Each one worth a look can mean dozens of pages of line items, clauses and delivery terms, plus supplier quotes that arrive as PDFs, email text and photos of printed sheets. Pricing a bid that is both competitive and profitable takes hours.

**Delivering what they win.** After award, the order lives across purchase orders, tracking emails, invoices and a spreadsheet. A miss is expensive: a late delivery can lead to termination of the contract and a poor past-performance rating that follows the company into every future bid.

Small teams make up for both with manual checking, which caps how many opportunities and orders they can take on. Koun Logistics LLC is one of those businesses. KounOS is the system we're building to run it.

**Problem statement:** [NAME THE HACKATHON PROBLEM STATEMENT THIS ADDRESSES]

### Who benefits

- **Koun's team first.** Less time reading and re-keying documents, fewer bids on contracts that were never a fit, fewer surprises after award, more opportunities handled by the same people.
- **Other small procurement and supply businesses**, as the product matures.
- **Government buyers, indirectly.** Better-checked bids and fewer late deliveries.

### Where it's going

Koun is customer zero. KounOS is built as Koun's own operating software first, and designed so any small government supplier could run on it: everything specific to a company (its certifications, the products it sells, its margin floor) lives in a company profile, not in the code. Whether to offer KounOS as a B2B product will be decided from Koun's own results with it.

---

## What KounOS does

KounOS does two jobs. The prototype proves both end to end on one real contract that has already been awarded.

### Job 1: decide what's worth pursuing

1. **Triage the notices (not in this prototype).** The triage screen and the scoring code exist, but the notice batch (H16) and the company profile values (H15) haven't landed, so it shows "No notices yet". When they land, each notice gets "pursue" or "pass", with the reason for every factor.
2. **Read the solicitation.** Open one worth pursuing. KounOS extracts line items, part numbers, quantities, the delivery requirement and key clauses. Every field links to the page and passage it came from, and code checks each quoted passage against the document before marking it verified. Gaps and ambiguities are flagged for review.
3. **Compare supplier quotes.** Drop in quotes in three formats: a PDF, an email screenshot, a printed quote (the phone photo lands with H06). KounOS normalizes them and checks each against the requirements for delivery date, compliance and price.
4. **Recommend a bid.** Landed cost, margin at a given bid price, and the lowest safe bid at a target margin, all computed in code. KounOS recommends "pursue at $X" or "pass, because...", and the user picks a supplier and gets a one-page sourcing package.
5. **Check against reality.** Because the demo contract was already awarded, KounOS's recommendation sits next to what the government actually paid.

### Job 2: keep awarded orders on track

6. **Monitor the order.** On a simulated award, KounOS links the customer commitment to the supplier PO, shipment, invoice and payment dates. When a supplier email reports a delay, KounOS turns it into an event, traces it to the customer delivery date, and prices each recovery option against margin and cash. (Draft notes are not in this prototype.)
7. **Ask KounOS (open PR #36).** "Which orders need attention today?" `POST /ask` lets Muse Spark call two read-only tools over the order records; attention is computed in code, ungrounded answers are withheld, and the record-linked panel sits on home and orders.

**People stay in charge.** KounOS recommends. Koun's team reviews supplier selections, bids and every external action. It never submits a bid or sends a message.

---

## Demo

**[▶ Demo video](TODO)** (3 minutes) · **[Live demo](https://kounos-web.vercel.app)**

| Time | What you see |
| --- | --- |
| 0:00 | The problem: a supplier's work scattered across PDFs, email and spreadsheets |
| 0:15 | Triage (not in this prototype): the screen is ready but the notice batch hasn't landed, so it shows "No notices yet" |
| 0:30 | A real USDA ARS solicitation (1232SA26Q0557, greenhouse LED fixtures for Fargo ND), awarded in September 2026, read with every field linked to its source |
| 0:55 | Three fictional quotes in three formats. Ninebark is cheapest but its 12–14 weeks miss the 60-day delivery term; Larkspur quotes the wrong cord (PTB8850LS42, not the required PTB8850LS41); Tallgrass meets every requirement at a thinner margin |
| 1:25 | The recommendation, "pursue at the lowest safe bid" with Tallgrass, next to the actual award |
| 1:40 | The contract replayed as if Koun had won, clearly labeled as a simulation |
| 1:50 | A supplier email reports the LED drivers are backordered. KounOS shows arrival moves to 2027-01-03, 2 days past the 2027-01-01 due date, and prices the fixes |
| 2:25 | "Which orders need attention today?" |
| 2:45 | What we built and what's next |

The live demo opens on the same scenario. **Reset demo** restores it at any time. When replay mode is on, the UI says so. The Render free-tier API sleeps when idle, so wake it before a demo.

---

## How we use Meta AI

KounOS uses three Meta models through the [Meta Model API](https://dev.meta.ai/docs/overview), each for the job it fits best. Every AI result in the interface is labeled with the model that produced it.

| Step | Model | Capability | How |
| --- | --- | --- | --- |
| Read the solicitation | Muse Spark 1.3 | Native PDF input, structured output | The PDF goes in as-is. A JSON schema requires a page number and a verbatim snippet for every field |
| Flag gaps and ambiguity | Muse Spark 1.3 | Reasoning effort `high` | A second pass asks what a contracting specialist would question and links each flag to its clause |
| Read quotes in any format | Muse Spark 1.3 | PDF and image input, structured output | One schema covers a PDF, a phone photo and an email screenshot |
| Turn a delay email into an event | Muse Spark 1.3 | Structured output | Email text → supplier, PO, affected items, new ship and arrival dates, confidence. The voice-transcribe step exists in code but the demo uses no voicemail |
| Explain impact and options | Muse Wonder (`muse-wonder-1.0`) | Parallel tool calling | Wonder calls read-only tools (order, commitments, alternate quotes, margin, cash gap) and writes its explanation from their results |
| Answer questions (Ask KounOS, open PR #36) | Muse Spark 1.3 | Tool calling (`list_orders`, `get_order`) | Read-only tools over the order records; attention computed in code; ungrounded answers withheld; answers link every record used |

Triage and draft notes are not in this prototype: the notice batch (H16) and drafts (A23) are still open, and the eval script (A15) hasn't run.

What's worth noticing:

- **Citations are checked, not trusted.** The model must quote its source; our code confirms the quote is really on that page before the field is marked verified.
- **One pipeline for messy inputs.** The same structured-output schema reads a PDF, a phone photo and a screenshot, which is how quotes actually arrive.
- **No fake voice.** The demo delay arrives as a supplier email, not a voicemail. The transcribe-then-extract path exists in code (`api/app/voicemail.py`), but no voicemail was recorded and the demo doesn't use Muse Voice Transcribe.
- **An agent that can't make up numbers.** Muse Wonder reasons over tool results, and any figure in its explanation that no tool returned causes the response to be rejected.
- **The right model for each step.** Muse Spark handles high-volume reading; Muse Wonder handles the one hard judgment call; reasoning effort is set per step.
- **Careful data handling.** The hosted demo uses Standard-mode model IDs only. Meta does not use Standard-mode content to train its models.

---

## Architecture

**Models read and explain. Code computes. People decide.**

```mermaid
flowchart TB
  subgraph WEB["Next.js app (browser)"]
    G["Triage view"]
    S["Solicitation view"]
    Q["Quote comparison"]
    O["Order monitor"]
    A["Ask KounOS panel"]
  end
  subgraph API["FastAPI service (Python)"]
    I["PDF ingest<br/>page text + word positions"]
    X["Extraction<br/>schema output, citation check"]
    F["Fit scoring<br/>company profile rules"]
    C["Cost engine<br/>landed cost, margin, lowest safe bid, cash gap"]
    R["Risk rules<br/>date slips, margin floor, cash exposure"]
    T["Agent tools<br/>read-only"]
  end
  STORE[("In-memory order store<br/>seeded from data/orders/seed.json")]
  subgraph META["Meta Model API"]
    MS["Muse Spark 1.3"]
    MW["Muse Wonder 1.0"]
    MV["Muse Voice Transcribe<br/>(voicemail path, unused in demo)"]
  end
  WEB <-->|"JSON + uploads"| API
  API -->|"loads at startup, reset restores"| STORE
  I --> X
  X --> F
  X --> MS
  T --> MW
  T --> MS
```

Only the extraction step and the agent tools touch a model. Every number and date comparison comes from code a reviewer can read.

### Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Front end | Next.js, Tailwind CSS, shadcn/ui | Fast to build the demo screens |
| PDF viewer | react-pdf (PDF.js) with text-layer highlights | Click a requirement and jump to its passage |
| API | Python, FastAPI, Pydantic | Pydantic models double as the JSON schemas sent for structured output |
| PDF text and positions | pdfplumber | Page text with word coordinates; MIT-licensed |
| Snippet check | RapidFuzz | Tolerates line breaks and hyphenation when matching quotes to the page |
| Order store | In-memory dict seeded from `data/orders/seed.json` | Zero setup; `POST /demo/reset` restores it |
| Model client | OpenAI Python SDK pointed at `https://api.meta.ai/v1` (Responses API) | One client for every Muse model |
| Hosting | Vercel (web) and Render free tier (API, sleeps when idle) | A live link judges can open |

### Data model

Record types (Pydantic schemas; the company-profile values land with H15): Company profile → Notice → Fit assessment (per-factor scores and reasons) → Solicitation → Award record (actual total, date, offers received) → Requirement (with source references) → Quote → Quote line → Sourcing decision → Order → Supplier PO → Shipment → Invoice → Event → Flag.

Each source reference stores the document, page, snippet, box coordinates and whether the snippet was verified.

---

## Engineering decisions

**1. Verified citations.** For every extracted field, the model returns a page number and a verbatim snippet. We extract that page's text with pdfplumber and fuzzy-match the snippet against it. A match marks the field verified and gives us word coordinates to highlight in the viewer. A miss marks it "needs review" instead of hiding the problem.

**2. Deterministic math.** Money and dates never come from a model.

| Quantity | Formula |
| --- | --- |
| Landed cost | supplier price + freight + fees |
| Margin | (bid − landed cost) ÷ bid |
| Lowest safe bid | landed cost ÷ (1 − target margin) |
| Delivery slack | required delivery date − projected arrival date |
| Cash exposure | amount paid to the supplier × days until government payment |

**3. Rules decide; models explain.** Pursue-or-pass is scored by plain rules against the company profile; the model only extracts the facts each rule needs, with citations. Likewise, delivery slips past the required date, margins below a floor and cash exposure are detected by plain rules, and Muse Wonder is called only to explain a flag and price options, using tool results.

**4. Grounded explanations.** Every number in a model explanation must match a value a tool returned. If it doesn't, the response is rejected and the plain rule-based flag is shown instead.

**5. Untrusted documents stay data.** Uploaded files can contain text aimed at the AI. Document text is passed as data, every tool the models can call is read-only, and nothing in the system can submit, send or write outside the app. Documents whose text addresses the AI are held for human review.

**6. Validated outputs.** Pydantic models define the JSON schemas. Model output is validated before anything is stored.

**7. Swappable models.** Model IDs live in configuration. Muse Wonder is in preview, so the impact step can fall back to Muse Spark 1.3, which takes the same requests on the same endpoints.

**8. A demo that holds up live.** Seed and reset endpoints restore the scenario. Replay mode serves stored responses for the scripted path if the network or API is slow, and the UI shows when it's active.

---

## Validation

### Extraction accuracy

Not run yet: the hand-labeled eval set and the eval script (A15) are still open, so there are no accuracy numbers to report. We will not invent them.

### Checked against a real award

| | Value |
| --- | --- |
| KounOS lowest safe bid (10% target margin, Tallgrass) | $91,189.92 ($786.12 per fixture) |
| Actual award total | $91,880.12 for 116 fixtures ($792.07 per fixture) |
| Award date | September 30, 2026 |
| Offers received | 26 |

How to read it:
- The safe bid comes from `app/costs.py` (`lowest_safe_bid`) on the Tallgrass quote, the same figure the contract-file screen shows. It lands $690.20 under the winning total.
- Only the award total is public, not line-item prices, so we compare totals.
- Our supplier prices reflect today's market, not prices at bid time. We chose an award from the last six months to limit drift.
- The winner had its own costs and strategy. This shows whether Koun would have been competitive, not an accuracy score.

---

## Run it locally

**Requirements:** Python 3.12+, Node.js 20+, and a Meta Model API key from [dev.meta.ai](https://dev.meta.ai/).

```bash
git clone https://github.com/RzanderR/KounOS.git
cd KounOS
cp .env.example .env          # add your MODEL_API_KEY

# API
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Web app (new terminal, from the repo root)
cd web
npm ci
npm run dev                   # http://localhost:3000
```

| Variable | Purpose | Default |
| --- | --- | --- |
| `MODEL_API_KEY` | Meta Model API key | required |
| `META_BASE_URL` | Meta Model API base URL | `https://api.meta.ai/v1` |
| `MODEL_READ` | Extraction, quotes, questions, drafts | `muse-spark-1.3` |
| `MODEL_IMPACT` | Impact analysis | `muse-wonder-1.0` |
| `MODEL_TRANSCRIBE` | Voicemail transcription | `muse-voice-transcribe-1.0` |
| `DEMO_MODE` | `live` calls the models; `replay` serves stored responses for the scripted path | `live` |
| `NEXT_PUBLIC_API_URL` | Where the web app finds the API | `http://localhost:8000` |

On Windows, activate the API venv with `.venv\Scripts\activate` (from `api/`) instead of `source .venv/bin/activate`.

### Repository layout

```
api/     FastAPI service: ingest, extraction, fit scoring, cost engine, rules, agent tools
web/     Next.js app: triage, solicitation, quotes, order monitor, Ask KounOS
data/    Demo scenario: public solicitation and award record, fictional quotes and delay email (no company profile or notice batch yet: H15/H16)
eval/    Not started: hand-labeled fields and the eval script land with A15/H07
```

---

## Built during the hackathon

All code in this repository was written between **October 26 and November 4, 2026**. No pre-existing Koun code was used. The first commit ([4d7cb3f](https://github.com/RzanderR/KounOS/commit/4d7cb3f), 2026-10-26) is a one-line README; the scaffold landed right after.

Built by Koun Logistics LLC with Muse Code (Meta), then Claude Code (Anthropic) after Oct 30; early planning briefs by Claude Code.

<!-- Triage, draft notes and the eval set are open or dropped (see TASKS.md); they stay off this list. -->

- Running scaffold: API health route and a placeholder web shell with live API status
- Solicitation reader with page-linked, verified citations and gap flags
- Quote intake from a PDF, an email screenshot and a printed quote, with requirement checks in code (Ninebark fails delivery, Larkspur fails spec, Tallgrass meets every requirement with country of origin to confirm)
- Cost engine: landed cost, margin, lowest safe bid, cash exposure
- Bid recommendation, one-page sourcing package and the award comparison
- Simulated order timeline linking commitment, PO, shipment, invoice and payment, behind a "Simulated award" banner
- Delay email-to-event pipeline (the voice-transcribe step exists in code; the demo uses the supplier email, no voicemail)
- Risk rules and Muse Wonder impact analysis with priced recovery options
- Number grounding: an explanation citing any figure no tool returned is discarded and replaced by code-written option text and the rule-based flags
- Contract-file screen: the linked solicitation-to-cash picture with click-through lineage, and the delay ripple shown before the recovery options
- Ask KounOS assistant with record-linked answers (open PR #36)
- Loading and error states with retry (open PR #37)
- Seed, reset and replay mode for the demo
- End-to-end browser test, green on the live link

---

## Third-party software and data

### Libraries

| Library | License | Used for |
| --- | --- | --- |
| Next.js, React | MIT | Web app |
| Tailwind CSS | MIT | Styling |
| shadcn/ui | MIT | UI components |
| shadcn runtime (shadcn, @base-ui/react, cn, tw-animate-css, class-variance-authority) | MIT (class-variance-authority: Apache-2.0) | shadcn/ui primitives and utils |
| react-pdf (PDF.js) | MIT (PDF.js: Apache-2.0) | PDF viewer |
| FastAPI | MIT | API |
| Pydantic | MIT | Schemas (they double as the structured-output JSON schemas) |
| SQLModel | MIT | Listed in requirements but unused; orders live in memory |
| Uvicorn | BSD-3-Clause | API server |
| pdfplumber | MIT | PDF text and word positions |
| RapidFuzz | MIT | Snippet matching |
| OpenAI Python SDK | Apache-2.0 | Client for the Meta Model API |
| Geist font | SIL Open Font License 1.1 | Typeface |
| Lucide icons | ISC | Icons |
| Pydantic Settings | MIT | Env-based API settings |
| pytest, httpx | MIT (httpx: BSD-3-Clause) | API tests |
| Playwright (Python) | Apache-2.0 | End-to-end browser test |
| ruff, mypy | MIT | API lint and typecheck |
| ESLint, TypeScript | MIT (TypeScript: Apache-2.0) | Web lint and types |

Meta's models are called as hosted services and are not bundled in this repository.

### Data and assets

- **Solicitations:** the demo solicitation, USDA ARS 1232SA26Q0557 (greenhouse LED fixtures, Fargo ND), is a public federal document: [SAM.gov notice](https://sam.gov/opp/8e79b518fb1046398b4c90429d18deea/view) (PDFs in `data/solicitations/`). There is no triage batch yet (H16). Works of the U.S. federal government are generally not subject to copyright.
- **Award records:** public award data for [1232SA26P0357](https://www.usaspending.gov/award/CONT_AWD_1232SA26P0357_12K3_-NONE-_-NONE-) (signed 2026-09-30, $91,880.12, 26 offers).
- **Company profile:** still open (H15). The schema exists; `data/company_profile.json` hasn't landed. It will hold Koun's public eligibility facts plus a demonstration margin floor, not Koun's real one.
- **Suppliers, quotes, orders and the delay email:** fictional, created by the team. No voicemail was recorded; the delay arrives as the Tallgrass backorder email. Supplier names were checked against real companies.
- **Real supplier quotes:** [NONE / list each one here, with the supplier's written permission on file].
- No real Koun customer, supplier or pricing data is in this repository.

---

## Scope and limitations

**Out of scope for the prototype:** live SAM.gov or DIBBS feeds, bid submission, sending email or messages, logins and multiple users, accounting integrations, real customer or supplier data, draft notes, and (dropped for the contract file) the shutdown toggle and award backtest.

**Known limitations:**
- Triage has no notice batch yet (H16); the screen shows "No notices yet", and scoring waits on the company profile (H15).
- Quote prices come from public list prices and fictional suppliers, not negotiated pricing.
- The award comparison covers one contract and compares totals only.
- Extraction accuracy hasn't been measured; the eval set (A15/H07) isn't run.
- Order monitoring runs on a simulated award.

---

## What's next

- Run KounOS on Koun's live opportunities and real orders, in a private production codebase
- The notice batch and company profile into triage, and award history for pricing context
- Supplier messaging, with approval before anything is sent
- Risk monitoring across all open orders
- Deciding, from Koun's own results, whether to offer KounOS to other small procurement and supply businesses

---

## Team

| Name | Role |
| --- | --- |
| [NAME] | [ROLE] |

Koun Logistics LLC

## License

[LICENSE NAME]. See [LICENSE](LICENSE).
