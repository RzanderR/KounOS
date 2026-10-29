# Stored live-model outputs (demo solicitation 1232SA26Q0557)

Real outputs from Meta's Model API (`MODEL_READ=muse-spark-1.3`), run live on
2026-10-28 from `api/` with the repo-root `.env`. These are model output, not
the hand-checked answer key (`data/solicitations/1232SA26Q0557.json`, which is
eval scoring input only and is never displayed on screen).

- `1232SA26Q0557_extraction.json` — served by
  `GET /solicitations/1232SA26Q0557` via `api/app/demo_solicitation.py`, with
  every passage re-checked by the A06 citation checker at request time.
  Command: `python scripts/extract_solicitation.py`. Returns CLINs 0001 + 1001
  (58 EA each, PTB8850LS41) and the 60-day delivery term.
- `1232SA26Q0557_gaps.json` — A07 gap pass output (8 flags, evidence only, not
  served). Caveat: the model invented its own file names
  ("Solicitation 1232SA26Q0557.pdf"); the real attachments are
  `1232SA26Q0557_specifications.pdf` and `1232SA26Q0557_terms_and_clauses.pdf`.
- `smoke_1232SA26Q0557.txt` — A02 smoke test stdout (Pydantic-validated, token
  usage printed). Command: `python scripts/smoke_meta.py` with
  `PYTHONPATH=.`.
