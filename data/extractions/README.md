# Stored live-model outputs (demo solicitation 1232SA26Q0557)

Real outputs from Meta's Model API (`MODEL_READ=muse-spark-1.3`). These are
model output, not the hand-checked answer key
(`data/solicitations/1232SA26Q0557.json`, which is eval scoring input only
and is never displayed on screen).

- `1232SA26Q0557_extraction.json` — served by
  `GET /solicitations/1232SA26Q0557` via `api/app/demo_solicitation.py`, with
  every passage re-checked by the A06 citation checker at request time.
  Re-run live 2026-10-29 (`python scripts/extract_solicitation.py`, UTF-8
  stdout: `$env:PYTHONUTF8='1'`). Returns CLINs 0001 + 1001 (58 EA each,
  PTB8850LS41), the 60-day delivery term, and the required sourcing clause
  (FAR 52.225-3, terms p.4, with the 52.225-4 certificate). Every snippet is
  a 16+ word surrounding phrase; clause lists report checked (☒) clauses
  only. All 8 served rows verify; 4 key clauses carry highlight word boxes.
- `1232SA26Q0557_gaps.json` — A07 gap pass output, run live 2026-10-28
  (8 flags, evidence only, not served). Caveat: the model invents file names
  ("Solicitation 1232SA26Q0557.pdf"); the real attachments are
  `1232SA26Q0557_specifications.pdf` and `1232SA26Q0557_terms_and_clauses.pdf`.
- `smoke_1232SA26Q0557.txt` — A02 smoke test stdout, run live 2026-10-28
  (Pydantic-validated, token usage printed). Command:
  `python scripts/smoke_meta.py` with `PYTHONPATH=.`. Caveat: the smoke
  schema sees only the specs PDF, so `solicitation_id` comes back empty.
- `quotes_ninebark.json`, `quotes_larkspur.json`, `quotes_tallgrass.json` —
  A10 quote records, run live 2026-10-29
  (`python scripts/extract_quotes.py`). One schema reads the Ninebark PDF,
  the Larkspur email PNG and the Tallgrass photographed PDF; all three
  match their `data/quotes/*.json` fixtures on supplier, total and lead
  time. Caveat: the email shows one combined line (qty 116), so the live
  Larkspur record has one line where the fixture splits base + option.
