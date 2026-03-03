"""Tests for decision flow: rules and tree prediction."""
import sys
from pathlib import Path

# Add project root so "src" is importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.decision.features import recognition_to_features
from src.decision.tree import predict_action, DEFAULT_ACTION, ACTION_CLASSES
from src.decision.rules import load_rules, evaluate_rules


def test_predict_action_without_model_returns_default() -> None:
    # No model trained yet -> default action
    vec = [0.0, 0.5, 0.9]
    action = predict_action(vec)
    assert action == DEFAULT_ACTION


def test_predict_action_returns_known_action() -> None:
    vec = [0.0, 0.5, 0.9]
    action = predict_action(vec)
    assert action in ACTION_CLASSES


def test_rules_load_empty() -> None:
    rules = load_rules()
    assert isinstance(rules, list)


def test_evaluate_rules_no_match_returns_none() -> None:
    rec = {"species": "tomato", "ripeness": 0.5, "confidence": 0.9}
    rec["feature_vector"] = recognition_to_features(rec)
    action = evaluate_rules(rec)
    assert action is None


def test_decision_flow_integration() -> None:
    rec = {"species": "tomato", "ripeness": 0.75, "confidence": 0.92}
    vec = recognition_to_features(rec)
    rec["feature_vector"] = vec
    action_from_rules = evaluate_rules(rec)
    action_from_tree = predict_action(vec)
    final = action_from_rules or action_from_tree
    assert final in ACTION_CLASSES
