# Python AI – GardenStation

Decision tree and control logic: decides what to do based on recognition results and sends commands to the Arduino (or simulation).

## Setup

```bash
conda create -p .conda python=3.10
conda activate .conda
pip install -r requirements.txt
```

## Project structure

- `config/` — `decision_rules.yaml` (optional override rules)
- `data/raw/`, `data/processed/`, `data/samples/` — datasets and samples; put training CSV in `data/processed/`
- `models/` — `decision_tree.pkl` and `tree_metadata.json` (written by training script)
- `src/` — `decision/` (features, tree, rules), `recognition/reader`, `api/server.py`
- `scripts/` — `train_tree.py` to train the tree
- `tests/` — unit tests and fixtures

## How it works

1. Read recognition output (species, ripeness, confidence) from a JSON file or stub.
2. Convert to a feature vector; optionally evaluate rules from `config/decision_rules.yaml`.
3. If no rule matches, predict action with the decision tree.
4. Output the canonical action parameters.

## Usage

Run the main controller (stub recognition, no serial by default; use `--dry-run` to avoid sending):

```bash
python -m src.api.server --dry-run
```

With a recognition JSON file and output to a file (simulation):

```bash
python -m src.api.server --recognition tests/fixtures/sample_recognition.json --port sim_out.txt --dry-run
```

With real serial port:

```bash
python -m src.api.server --port COM3 --recognition path/to/recognition.json
```

## Training

Create a CSV in `data/processed/` with columns: `species_encoded`, `ripeness`, `confidence`, `action`. Then:

```bash
python scripts/train_tree.py --data-dir data/processed --output-dir models --csv decisions.csv
```

This writes `models/decision_tree.pkl` and `models/tree_metadata.json`. Action labels must be one of: water, feed, pollinate, harvest, adjust_light, notify_user, no_action, move_to_zone.

## Config

- **decision_rules.yaml** — Optional rules (e.g. if confidence < 0.5 then notify_user) evaluated before the tree.

## Tests

```bash
python -m pytest tests/ -v
# or
python tests/test_features.py
python tests/test_decision.py
```
