# Demo contract: USDA greenhouse LED fixtures (1232SA26Q0557)

Picked Oct 27, 2026. The solicitation and award are real, public federal records. Every supplier and quote in this folder is **fictional** and labeled as such.

## The contract

| | |
| --- | --- |
| Solicitation | [1232SA26Q0557](https://sam.gov/opp/8e79b518fb1046398b4c90429d18deea/view), "Greenhouse light fixtures, brand name for the USDA, ARS, ETSARC in Fargo, ND" |
| Agency | USDA Agricultural Research Service (Edward T. Schafer Agricultural Research Center, Fargo, ND) |
| Type | Combined synopsis/solicitation (RFQ), commercial items, FAR Part 12 |
| Posted / due | June 1, 2026 / June 10, 2026 |
| Set-aside | Total small business; NAICS 335132; PSC 6210 |
| Line items | 0001: 58 LED greenhouse fixtures, 100-277V, 10-foot cord, 5-15P plug. 0002 (option): up to 58 more |
| Product awarded | PHOTOBIO CX 2125 850W, part **PTB8850LS41** (10' cord with 5-15P plug) |

## The answer key (actual award)

| | |
| --- | --- |
| Award | [1232SA26P0357](https://www.usaspending.gov/award/CONT_AWD_1232SA26P0357_12K3_-NONE-_-NONE-), signed Sept 30, 2026 |
| Winner | Morgan Ingland LLC, Morgan Hill, CA |
| Offers received | **26** |
| Base (58 fixtures) | $45,940.06 |
| Option (58 fixtures, exercised the same day) | $45,940.06 |
| Total | **$91,880.12** for 116 fixtures |
| Unit price | **$792.07** |

Source: USAspending.gov award and transaction data (FPDS), retrieved Oct 27, 2026.

## Why this one

- **Neutral agency:** agricultural research, so nothing political or military.
- **Supply only:** one product on two lines (base and option), shipped to one site.
- **A real market test:** 26 competing offers, and the winning unit price can be derived exactly.
- **A real spec trap:** the solicitation names the cord and plug, and the same fixture is sold with other cords. Catching a wrong variant is exactly what KounOS's requirement check should do.
- **Public pricing to anchor the fictional quotes:** Hydrofarm lists the fixture at $999.00 SRP ([PTB8850LS42](https://www.hydrofarm.com/p/photobio-cx-2125-850w-100-277v-s4-spectrum/ptb8850ls42)); a retailer lists the 120V version at $1,159.17 ([Hydrobuilder](https://hydrobuilder.com/photobio-cx-850-watt-led-grow-light.html)). The winner bid $792.07.

## The fictional quotes

All three quote the full 116 fixtures (58 base + 58 option).

| Supplier (fictional) | Format | Part quoted | Unit | Freight | Quote total | Lead time | The catch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ninebark Lighting Supply | PDF | PTB8850LS41 | $668.00 | $1,860.00 | $79,348.00 | 12-14 weeks ARO | Cheapest, but likely too slow (see "Confirm" below) |
| Larkspur Grow Systems | Email screenshot | **PTB8850LS42** | $679.00 | included | $78,764.00 | 2-3 weeks ARO | Wrong cord: 208-240V instead of the required 5-15P plug |
| Tallgrass Horticultural Supply | Printed quote to photograph | PTB8850LS41 | $695.00 | $1,450.00 | $82,070.00 | 3-4 weeks ARO | Compliant, thinnest margin, 50% deposit ($41,035.00) |

## What KounOS should compute (test vectors)

Lowest safe bid = landed cost ÷ (1 − target margin), per unit rounded up to the cent.

| Supplier | Landed cost | Per unit | Lowest safe bid at 10% (per unit / total) | Margin if bid at the actual award price |
| --- | --- | --- | --- | --- |
| Ninebark | $79,348.00 | $684.03 | $760.04 / $88,164.64 | 13.6% |
| Larkspur | $78,764.00 | $679.00 | $754.45 / $87,516.20 | 14.3% |
| Tallgrass | $82,070.00 | $707.50 | **$786.12 / $91,189.92** | 10.7% |

**The reveal:** with the only compliant, on-time supplier, KounOS says "pursue at $786.12 per fixture." The government paid $792.07. At a 10% margin, Koun would have undercut the winner by $5.95 per fixture (0.75%): competitive, but only just.

## Confirmed from the attachments (Oct 28)

Both PDFs are in `data/solicitations/` as `1232SA26Q0557_specifications.pdf` (2 pages) and `1232SA26Q0557_terms_and_clauses.pdf` (16 pages). Page references are in `solicitations/1232SA26Q0557.json`.

1. **Delivery: all items within 60 days after award** (terms, p. 12). Ninebark's 12-14 weeks (up to 98 days) misses it, so its quote stays as designed.
2. **Brand name only.** "Equal" products are technically unacceptable (terms, p. 12). Larkspur's PTB8850LS42 fails.
3. **FOB destination,** delivered to USDA-ARS ETSARC BRL, 1616 Albrecht Blvd N, Fargo ND 58102. The quotes match.
4. **Sourcing clause: FAR 52.225-3 Buy American, Free Trade Agreements** (terms, p. 4), with the 52.225-4 certificate (p. 14). All three quotes leave country of origin unstated, so KounOS should flag it as "needs confirmation" on every quote.
5. **Evaluation: lowest price, technically acceptable,** with price evaluated on base plus option (terms, pp. 11-12). This makes the bid recommendation a pure price race among compliant quotes.
6. **The option line is CLIN 1001,** not 0002.

**Real ambiguities in the documents (good material for A07's gap pass):**

- Cord length: the specifications say a 10-foot cord, but the technical table says "1- foot cord" (terms, p. 11).
- Quantity split: the schedule says 58 + 58, but the technical table says 96 and 20 (the same 116 total).
- Delivery: the specifications say base 2 months after award and option within 180 days (specs, p. 2), but the terms say all items within 60 days.

## Adapting the plan's story

- The simulated award and voicemail still work: "the LED drivers are backordered, and shipping moves 16 days."
- The plan's placeholder numbers ($54,000 bid, $46,900 landed, $52,111 safe bid) are replaced by the table above. This is decision D01 in `docs/DECISIONS.md`.
- The 50% deposit sets up the cash-exposure flag.

## Triage batch candidates

Recent civilian awards found during the search, all competed. The real triage factors (set-aside, products, delivery) need Koun's company profile.

| Notice | Agency | Award | Offers | Likely triage result |
| --- | --- | --- | --- | --- |
| 1232SA26Q0557, greenhouse LED fixtures (the demo) | USDA ARS, Fargo ND | $91,880.12 | 26 | Pursue |
| 140P8526Q0068, residential electrical supplies (five bundles) | NPS, Yosemite NP | $86,598.30 | 14 | Pursue, if Koun sells general electrical |
| 140R1726Q0043, wire cable STJ 16-6 | Bureau of Reclamation, Grand Coulee | $80,400.00 | 14 | Depends on product fit |
| 140FS226Q0070, 50 UV lamps for a fish hatchery | U.S. Fish and Wildlife Service, MI | $22,436.40 | 18 | Pass if under Koun's minimum value |
| 36C24726Q0552, power strips | VA, Charleston SC | $36,040.00 | 7 | Pass unless Koun is service-disabled-veteran-owned (SDVOSB set-aside) |
| 1232SA26Q1198, horticultural LED systems | USDA ARS | $139,278.00 | 1 | Pass: sole-source intent to one vendor |

## Files

```
data/solicitations/1232SA26Q0557.json      solicitation facts (add the two PDFs here)
data/awards/1232SA26Q0557.json             award record: the answer key
data/quotes/ninebark.json                  quote data + expected KounOS results
data/quotes/larkspur.json
data/quotes/tallgrass.json
data/quotes/docs/ninebark_quote.pdf        PDF quote
data/quotes/docs/larkspur_email.png        email screenshot
data/quotes/docs/tallgrass_quote_PRINT_AND_PHOTOGRAPH.pdf   print it, photograph it with a phone (task H06)
```
