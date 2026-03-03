"""
Read recognition result (species, ripeness, confidence) from a source.
First implementation: JSON file or stub for local/simulation use.
"""
from pathlib import Path
from typing import Any
import json


def read_recognition(source: str | Path | None = None) -> dict[str, Any]:
    """
    Read one recognition result. If source is a path to a JSON file, load it.
    Otherwise return a stub dict for testing (or later: socket/queue/API).
    """
    if source is not None:
        path = Path(source)
        if path.exists() and path.suffix.lower() in (".json",):
            return json.loads(path.read_text(encoding="utf-8"))
    return _stub_recognition()


def _stub_recognition() -> dict[str, Any]:
    """Default stub when no source is provided (e.g. simulation)."""
    return {
        "species": "tomato",
        "ripeness": 0.5,
        "confidence": 0.9,
    }
