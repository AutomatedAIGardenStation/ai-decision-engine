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

def test_load_tree_with_missing_files(tmp_path):
    from src.decision.tree import load_tree
    # Provided a directory with no models
    estimator, metadata = load_tree(tmp_path)
    assert estimator is None
    assert metadata == {}

class FakeEstimator:
    def predict(self, X):
        return [0]

class FakeEstimatorFeed:
    def predict(self, X):
        return [1]

class FakeEstimatorError:
    def predict(self, X):
        raise ValueError("predict failed")

def test_load_tree_with_existing_files(tmp_path):
    from src.decision.tree import load_tree
    import joblib
    import json

    # Create fake model
    pkl_path = tmp_path / "decision_tree.pkl"
    meta_path = tmp_path / "tree_metadata.json"

    joblib.dump(FakeEstimator(), pkl_path)
    meta_path.write_text(json.dumps({"action_classes": ["water", "feed"]}))

    estimator, metadata = load_tree(tmp_path)
    assert estimator is not None
    assert metadata == {"action_classes": ["water", "feed"]}

def test_predict_action_with_mock_estimator(tmp_path):
    import joblib
    import json

    # Create fake model
    pkl_path = tmp_path / "decision_tree.pkl"
    meta_path = tmp_path / "tree_metadata.json"

    joblib.dump(FakeEstimatorFeed(), pkl_path)
    meta_path.write_text(json.dumps({"action_classes": ["water", "feed"]}))

    action = predict_action([0.0, 0.5, 0.9], models_dir=tmp_path)
    assert action == "feed"

def test_predict_action_exception_fallback(tmp_path):
    import joblib

    # Create fake model that raises exception on predict
    pkl_path = tmp_path / "decision_tree.pkl"

    joblib.dump(FakeEstimatorError(), pkl_path)

    action = predict_action([0.0, 0.5, 0.9], models_dir=tmp_path)
    assert action == DEFAULT_ACTION


def test_rules_load_empty() -> None:
    rules = load_rules()
    assert isinstance(rules, list)


def test_evaluate_rules_no_match_returns_none() -> None:
    rec = {"species": "tomato", "ripeness": 0.5, "confidence": 0.9}
    rec["feature_vector"] = recognition_to_features(rec)
    action = evaluate_rules(rec)
    assert action is None

def test_load_rules_with_yaml(tmp_path):
    import yaml

    rules_file = tmp_path / "decision_rules.yaml"
    rules_data = {
        "rules": [
            {
                "action": "feed",
                "conditions": [
                    {"operator": "lt", "feature": "ripeness", "value": 0.3}
                ]
            }
        ]
    }
    rules_file.write_text(yaml.dump(rules_data))

    loaded = load_rules(tmp_path)
    assert len(loaded) == 1
    assert loaded[0]["action"] == "feed"

def test_load_rules_invalid_yaml(tmp_path):
    rules_file = tmp_path / "decision_rules.yaml"
    rules_file.write_text("invalid yaml")

    loaded = load_rules(tmp_path)
    # The current code returns [] if the yaml doesn't parse to a dict with "rules"
    assert loaded == []

def test_evaluate_rules_matches(tmp_path):
    import yaml

    rules_file = tmp_path / "decision_rules.yaml"
    rules_data = {
        "rules": [
            {
                "action": "water",
                "conditions": [
                    {"operator": "eq", "feature": "species", "value": "cucumber"},
                    {"operator": "gt", "feature": "confidence", "value": 0.8}
                ]
            }
        ]
    }
    rules_file.write_text(yaml.dump(rules_data))

    rec = {"species": "cucumber", "confidence": 0.9}
    action = evaluate_rules(rec, tmp_path)
    assert action == "water"

def test_evaluate_rules_all_operators(tmp_path):
    import yaml

    rules_file = tmp_path / "decision_rules.yaml"
    rules_data = {
        "rules": [
            {
                "action": "test_action",
                "conditions": [
                    {"operator": "lt", "feature": "val", "value": 10},
                    {"operator": "le", "feature": "val", "value": 5},
                    {"operator": "eq", "feature": "val", "value": 5},
                    {"operator": "ne", "feature": "val", "value": 6},
                    {"operator": "ge", "feature": "val", "value": 5},
                    {"operator": "gt", "feature": "val", "value": 4},
                    {"operator": "in", "feature": "val", "value": [5, 6]},
                    {"operator": "not_in", "feature": "val", "value": [7, 8]}
                ]
            }
        ]
    }
    rules_file.write_text(yaml.dump(rules_data))

    rec = {"val": 5}
    action = evaluate_rules(rec, tmp_path)
    assert action == "test_action"

def test_evaluate_rules_missing_feature(tmp_path):
    from src.decision.rules import _evaluate_condition

    # Missing feature should return False for gt, but can return True for eq if val is None
    assert not _evaluate_condition({}, {"operator": "gt", "feature": "val", "value": 5})
    assert _evaluate_condition({}, {"operator": "eq", "feature": "val", "value": None})

def test_evaluate_rules_with_feature_vector(tmp_path):
    from src.decision.rules import _get_value

    # _get_value falls back to FEATURE_TO_INDEX and "feature_vector"
    rec = {"feature_vector": [1.0, 0.5, 0.9]} # species_encoded, ripeness, confidence
    assert _get_value(rec, "species_encoded") == 1.0
    assert _get_value(rec, "ripeness") == 0.5
    assert _get_value(rec, "confidence") == 0.9


def test_decision_flow_integration() -> None:
    rec = {"species": "tomato", "ripeness": 0.75, "confidence": 0.92}
    vec = recognition_to_features(rec)
    rec["feature_vector"] = vec
    action_from_rules = evaluate_rules(rec)
    action_from_tree = predict_action(vec)
    final = action_from_rules or action_from_tree
    assert final in ACTION_CLASSES
