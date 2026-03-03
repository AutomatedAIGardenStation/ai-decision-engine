"""
Load the trained decision tree and predict action from a feature vector.
"""
from pathlib import Path
from typing import Any

import joblib

# Default actions when model is missing or predict fails.
DEFAULT_ACTION = "no_action"
ACTION_CLASSES = [
    "water",
    "feed",
    "pollinate",
    "harvest",
    "adjust_light",
    "notify_user",
    "no_action",
    "move_to_zone",
]


def _models_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "models"


def load_tree(models_dir: Path | None = None):
    """
    Load DecisionTreeClassifier from models/decision_tree.pkl.
    Returns (estimator, metadata_dict) or (None, {}) if file missing.
    """
    base = models_dir or _models_dir()
    pkl_path = base / "decision_tree.pkl"
    meta_path = base / "tree_metadata.json"

    if not pkl_path.exists():
        return None, {}

    estimator = joblib.load(pkl_path)
    metadata: dict[str, Any] = {}
    if meta_path.exists():
        import json
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    return estimator, metadata


def predict_action(
    feature_vector: list[float],
    models_dir: Path | None = None,
) -> str:
    """
    Predict action from feature vector. Uses tree if available and metadata
    for class names; otherwise returns DEFAULT_ACTION.
    """
    import numpy as np

    estimator, metadata = load_tree(models_dir)
    if estimator is None:
        return DEFAULT_ACTION

    classes = metadata.get("action_classes", ACTION_CLASSES)
    try:
        X = np.asarray([feature_vector], dtype=float)
        idx = estimator.predict(X)[0]
        if 0 <= idx < len(classes):
            return classes[int(idx)]
    except Exception:
        pass
    return DEFAULT_ACTION
