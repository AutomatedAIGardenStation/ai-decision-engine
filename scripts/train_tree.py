"""
Train DecisionTreeClassifier from data/processed CSV and save to models/.
CSV must have columns: species_encoded, ripeness, confidence (features) and action (label).
"""
import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder


FEATURE_NAMES = ["species_encoded", "ripeness", "confidence"]
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Train decision tree for GardenStation AI")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "processed",
        help="Directory containing CSV (e.g. decisions.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "models",
        help="Where to save decision_tree.pkl and tree_metadata.json",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="decisions.csv",
        help="CSV filename inside data-dir",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Max depth of the tree",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="1.0",
        help="Version string for metadata",
    )
    args = parser.parse_args()

    csv_path = args.data_dir / args.csv
    if not csv_path.exists():
        raise SystemExit(f"Data not found: {csv_path}. Create a CSV with columns: {FEATURE_NAMES + ['action']}")

    df = pd.read_csv(csv_path)
    for col in FEATURE_NAMES:
        if col not in df.columns:
            raise SystemExit(f"Missing feature column: {col}")
    if "action" not in df.columns:
        raise SystemExit("Missing label column: action")

    X = df[FEATURE_NAMES].astype(float)
    le = LabelEncoder()
    le.fit(ACTION_CLASSES)
    y = le.transform(df["action"].astype(str).str.strip())

    clf = DecisionTreeClassifier(max_depth=args.max_depth, random_state=42)
    clf.fit(X, y)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pkl_path = args.output_dir / "decision_tree.pkl"
    joblib.dump(clf, pkl_path)

    metadata = {
        "feature_names": FEATURE_NAMES,
        "action_classes": list(le.classes_),
        "version": args.version,
        "max_depth": args.max_depth,
    }
    meta_path = args.output_dir / "tree_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Saved {pkl_path} and {meta_path}")
    print("action_classes:", list(le.classes_))
