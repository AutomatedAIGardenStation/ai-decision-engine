"""Tests for recognition -> feature vector conversion."""
import sys
from pathlib import Path

# Add project root so "src" is importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.decision.features import recognition_to_features, FEATURE_NAMES, _ripeness_str_to_float


def test_feature_vector_length() -> None:
    rec = {"species": "tomato", "ripeness": 0.5, "confidence": 0.9}
    vec = recognition_to_features(rec)
    assert len(vec) == len(FEATURE_NAMES)
    assert all(isinstance(x, (int, float)) for x in vec)


def test_species_encoding() -> None:
    rec = {"species": "cucumber", "ripeness": 0.0, "confidence": 0.0}
    vec = recognition_to_features(rec)
    assert vec[0] == 1  # cucumber -> 1


def test_ripeness_clamped() -> None:
    rec = {"species": "tomato", "ripeness": 1.5, "confidence": 0.5}
    vec = recognition_to_features(rec)
    assert vec[1] == 1.0
    rec["ripeness"] = -0.1
    vec2 = recognition_to_features(rec)
    assert vec2[1] == 0.0


def test_confidence_clamped() -> None:
    rec = {"species": "tomato", "ripeness": 0.5, "confidence": 2.0}
    vec = recognition_to_features(rec)
    assert vec[2] == 1.0


def test_from_fixture_file() -> None:
    fixture = Path(__file__).parent / "fixtures" / "sample_recognition.json"
    if not fixture.exists():
        return
    import json
    rec = json.loads(fixture.read_text(encoding="utf-8"))
    vec = recognition_to_features(rec)
    assert len(vec) == 3
    assert vec[0] >= 0
    assert 0 <= vec[1] <= 1
    assert 0 <= vec[2] <= 1

def test_ripeness_str_mapping() -> None:
    assert _ripeness_str_to_float("unripe") == 0.25
    assert _ripeness_str_to_float("green") == 0.25
    assert _ripeness_str_to_float("ripe") == 0.75
    assert _ripeness_str_to_float("ready") == 0.75
    assert _ripeness_str_to_float("overripe") == 1.0
    assert _ripeness_str_to_float("over") == 1.0
    assert _ripeness_str_to_float("0.5") == 0.5
    assert _ripeness_str_to_float("invalid") == 0.5 # RIPENESS_DEFAULT
    assert _ripeness_str_to_float("") == 0.5

def test_recognition_to_features_invalid_ripeness_type() -> None:
    data = {
        "species": "tomato",
        "ripeness": [], # Invalid type
        "confidence": 0.8
    }
    features = recognition_to_features(data)
    # species: 0.0, ripeness defaults to 0.5, confidence 0.8
    assert features == [0.0, 0.5, 0.8]

def test_recognition_to_features_str_ripeness() -> None:
    data = {
        "species": "pepper",
        "ripeness": "green",
        "confidence": 0.5
    }
    features = recognition_to_features(data)
    # species: 2.0 (pepper), ripeness 0.25, confidence 0.5
    assert features == [2.0, 0.25, 0.5]
