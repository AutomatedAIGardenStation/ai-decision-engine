"""
Convert recognition output dict to a fixed-size numeric feature vector
for the decision tree. Feature order must match tree_metadata.json.
"""
from typing import Any

# Canonical feature names (same order as vector); sync with train_tree and metadata.
FEATURE_NAMES = ["species_encoded", "ripeness", "confidence"]

# Species label encoding: index = value for tree. Extend as recognition classes grow.
SPECIES_TO_ID: dict[str, int] = {
    "tomato": 0,
    "cucumber": 1,
    "pepper": 2,
    "unknown": 3,
}
DEFAULT_SPECIES_ID = SPECIES_TO_ID["unknown"]

# Ripeness: expect 0.0..1.0 or map from string.
RIPENESS_DEFAULT = 0.5


def recognition_to_features(recognition: dict[str, Any]) -> list[float]:
    """
    Build feature vector from recognition result.
    recognition may contain: species (str), ripeness (float 0-1 or str), confidence (float).
    """
    species = (recognition.get("species") or "unknown").lower().strip()
    species_encoded = SPECIES_TO_ID.get(species, DEFAULT_SPECIES_ID)

    raw_ripeness = recognition.get("ripeness", RIPENESS_DEFAULT)
    if isinstance(raw_ripeness, (int, float)):
        ripeness = float(raw_ripeness)
    elif isinstance(raw_ripeness, str):
        ripeness = _ripeness_str_to_float(raw_ripeness)
    else:
        ripeness = RIPENESS_DEFAULT
    ripeness = max(0.0, min(1.0, ripeness))

    confidence = float(recognition.get("confidence", 0.0))
    confidence = max(0.0, min(1.0, confidence))

    return [float(species_encoded), ripeness, confidence]


def _ripeness_str_to_float(s: str) -> float:
    s = (s or "").lower().strip()
    if s in ("unripe", "green"):
        return 0.25
    if s in ("ripe", "ready"):
        return 0.75
    if s in ("overripe", "over"):
        return 1.0
    try:
        return float(s)
    except (TypeError, ValueError):
        return RIPENESS_DEFAULT
