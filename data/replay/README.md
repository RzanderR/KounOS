# Replay responses (A27)

Stored model responses served when `DEMO_MODE=replay`. Each file holds the
model's raw answer (`response`) and the stored live run it came from
(`source`). Only the model's answer is replayed: the API still builds the
event, prices the recovery options and checks every figure in code.

Suppliers, orders and the email are fictional.

- `event_tallgrass_backorder.json`: the `MODEL_READ` read of
  `data/voicemail/tallgrass_backorder.txt`, taken from the stored live event
  `data/extractions/tallgrass_backorder_event.json` (its summary carries the
  PO, items and both dates).
- `impact_ORD-001.json`: the Muse Wonder (`muse-wonder-1.0`) option summaries
  and note for the Tallgrass delay, from the stored live run
  `data/extractions/impact_ord-001.json`. The UI labels it
  "muse-wonder-1.0 (replay)".
- `ask_attention.json`: the Muse Spark (`muse-spark-1.3`) answer to Ask
  KounOS's scripted question "Which orders need attention today?", recorded
  as of 2026-11-04 after the Tallgrass ingest, from the stored live run
  `data/extractions/ask_attention.json` (`api/scripts/record_ask.py`). The
  stored tool calls are re-run against current state and the answer is
  grounded again. Replay uses the record's date unless `DEMO_TODAY` is set.
  The UI labels it "muse-spark-1.3 (replay)".

Any other step answers 503 in replay mode instead of calling a model.
