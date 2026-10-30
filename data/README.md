# Demo data provenance

## Real public records (no permission needed)

- **Solicitation 1232SA26Q0557** (USDA ARS, greenhouse light fixtures, Fargo ND): facts in
  `solicitations/1232SA26Q0557.json`; the two PDFs were downloaded from the SAM.gov
  notice (`sam_url` in that file) and stored under `solicitations/` under their
  original SAM names. `confirmed_from_attachments` in the JSON records what was
  verified by hand from the PDFs, with page numbers; `known_ambiguities` records
  the three genuine conflicts between the documents. Both are the answer key for
  extraction work, not model output.
- **Award 1232SA26P0357** (`awards/1232SA26Q0557.json`): USAspending.gov award data
  (FPDS), retrieved 2026-10-27. Real award to MORGAN INGLAND LLC, $91,880.12.

## Fictional quotes (labeled, do not treat as real)

Larkspur, Ninebark and Tallgrass are invented suppliers; every contact name,
phone, email, address and signature in `quotes/*.json` and `quotes/docs/` is
fictional and each JSON says so explicitly. Formats mirror real life (a PDF
quote, an email screenshot, a print-and-photograph) so ingest is exercised;
the Tallgrass photo itself is still to be taken (H06). Option CLIN corrected
to 1001 per the solicitation schedule (terms p.1).

## Expected results

`expected_kounos_results` in each quote JSON is the intended KounOS output for
this demo (compliance flags, landed-cost math, margins). It is the answer key
for cost-engine tests, not model output.
