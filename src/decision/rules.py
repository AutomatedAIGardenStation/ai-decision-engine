"""
Evaluate optional override rules from config before falling back to the tree.
"""
from pathlib import Path
from typing import Any

import yaml

# Feature key in recognition dict (and in rules) -> index in feature vector for numeric compare.
FEATURE_TO_INDEX: dict[str, int] = {
    "species_encoded": 0,
    "ripeness": 1,
    "confidence": 2,
}
# Also allow recognition keys directly for rule conditions.
RECOGNITION_KEYS = ("species", "ripeness", "confidence", "zone_id")

OPERATORS = ("lt", "le", "eq", "ne", "ge", "gt", "in", "not_in")


def _config_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "config"


def load_rules(config_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load decision_rules.yaml and return the list of rules."""
    base = config_dir or _config_dir()
    path = base / "decision_rules.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return []
    return data.get("rules", [])


def _get_value(features_dict: dict[str, Any], feature_name: str) -> Any:
    """Resolve feature value from recognition-like dict or feature vector index."""
    if feature_name in features_dict:
        return features_dict[feature_name]
    idx = FEATURE_TO_INDEX.get(feature_name)
    if idx is not None and "feature_vector" in features_dict:
        vec = features_dict["feature_vector"]
        if idx < len(vec):
            return vec[idx]
    return None


def _evaluate_condition(features_dict: dict[str, Any], cond: dict) -> bool:
    op = (cond.get("operator") or "").strip().lower()
    feat = cond.get("feature")
    val = cond.get("value")
    if not feat or op not in OPERATORS:
        return False
    actual = _get_value(features_dict, feat)
    if actual is None and op not in ("eq", "in", "not_in"):
        return False
    if op == "lt":
        return float(actual) < float(val)
    if op == "le":
        return float(actual) <= float(val)
    if op == "eq":
        return actual == val
    if op == "ne":
        return actual != val
    if op == "ge":
        return float(actual) >= float(val)
    if op == "gt":
        return float(actual) > float(val)
    if op == "in":
        return actual in (val if isinstance(val, (list, tuple)) else [val])
    if op == "not_in":
        return actual not in (val if isinstance(val, (list, tuple)) else [val])
    return False


def evaluate_rules(
    features_dict: dict[str, Any],
    config_dir: Path | None = None,
) -> str | None:
    """
    Evaluate rules. features_dict can be the recognition dict (and optionally
    include "feature_vector" for numeric conditions). Returns action if a
    rule matches, else None.
    """
    rules = load_rules(config_dir)
    for rule in rules:
        conditions = rule.get("conditions") or []
        if not conditions:
            continue
        if all(_evaluate_condition(features_dict, c) for c in conditions):
            action = rule.get("action")
            if action:
                return str(action).strip()
    return None
