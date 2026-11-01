"""Replay mode (A27): stored model responses for the scripted demo path.

With ``DEMO_MODE=replay`` the two model calls on the scripted path (the
Tallgrass email read and the recovery-options explanation) return the
stored responses in ``data/replay/`` instead of calling a model. Only the
model's answer is replayed: code still builds the event, prices the
options and checks every figure, exactly as it does live.
"""

import json
from typing import Any

from app.config import REPO_ROOT

REPLAY_DIR = REPO_ROOT / "data" / "replay"


class NoReplay(RuntimeError):
    """Replay mode has no stored response for this step."""

    def __init__(self, name: str) -> None:
        super().__init__(
            f"Replay mode has no stored response for {name}; "
            "only the scripted demo path is replayed. Set DEMO_MODE=live to call the models."
        )


def stored(name: str) -> dict[str, Any]:
    """The stored record ``data/replay/<name>.json``: ``response`` plus provenance."""
    path = REPLAY_DIR / f"{name}.json"
    if not path.is_file():
        raise NoReplay(name)
    record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return record
