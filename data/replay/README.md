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

Any other step answers 503 in replay mode instead of calling a model.
