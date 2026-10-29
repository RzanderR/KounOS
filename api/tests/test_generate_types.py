"""Generated-types freshness test (A03): the web file matches the generator."""

from scripts.generate_types import OUT_PATH, render_file


def test_generated_types_are_current() -> None:
    """Fail on drift: rerun ``python scripts/generate_types.py`` from api/."""
    assert OUT_PATH.is_file(), "Run python scripts/generate_types.py from api/ first."
    assert OUT_PATH.read_text(encoding="utf-8") == render_file()
