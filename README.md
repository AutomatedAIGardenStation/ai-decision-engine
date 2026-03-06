# Python AI – GardenStation

Stateless Decision Engine. Receives a Lightweight Event Context Snapshot from the Backend, applies domain evaluators (Watering, EC/pH, Harvest, Climate, Pollination), and returns an Action Queue of firmware-primitive commands (Cartesian coordinates, valve timings, pump durations).

## Module Contract

| | |
|---|---|
| **Input** | Lightweight Event Context Snapshot (JSON via `POST /decide`) — sensors, vision results, plant profiles, cooldowns, tool state |
| **Output** | Action Queue — array of firmware-primitive commands: `ARM_MOVE_TO`, `DOSE_RECIPE`, `PUMP_RUN`, `VALVE_SET`, `TOOL_DOCK`, `TOOL_RELEASE`, `WRIST_SET`, `GRIPPER_*`, `ARM_HOME`, `ESCALATE` |
| **Constraint** | 100% stateless. No database access, no serial connections, no ML inference calls. |

## Setup

```bash
conda create -p .conda python=3.10
conda activate .conda
pip install -r requirements.txt
```

## Project structure

- `config/` — `decision_config.yaml` (thresholds, cooldowns), `arduino_commands.yaml` (action → firmware-primitive mapping)
- `data/raw/`, `data/processed/`, `data/samples/` — datasets and samples; put training CSV in `data/processed/`
- `models/` — `decision_tree.pkl` and `tree_metadata.json` (written by training script)
- `src/decision/` — `engine.py` (main evaluator router), `evaluators/` (one per domain: watering, ec_ph, harvest, climate, pollination), `features.py`, `rules.py`, `tree.py`
- `src/api/` — `server.py` (FastAPI, single `POST /decide` endpoint)
- `src/recognition/` — `reader.py` (recognition result parser)
- `src/arduino/` — `writer.py` (serial output, used in legacy CLI mode)
- `scripts/` — `train_tree.py` to train the decision tree
- `tests/` — unit tests and fixtures

## How it works

1. Backend sends a Lightweight Event Context Snapshot (sensors, vision results, plant profiles, cooldowns, tool state) to `POST /decide`.
2. Engine routes the snapshot to domain evaluators (Watering, EC/pH, Harvest, Climate, Pollination).
3. Each evaluator returns zero or more actions using firmware-primitive commands (e.g., `ARM_MOVE_TO`, `DOSE_RECIPE`, `PUMP_RUN`).
4. Constraints gate (cooldowns, safety limits) filters the action list.
5. Returns the Action Queue to the backend for execution.

## Usage

Run the FastAPI decision server:

```bash
python -m src.api.server
```

Test with a snapshot:

```bash
curl -X POST http://localhost:8002/decide \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/sample_snapshot.json
```

Legacy CLI mode (stub recognition, no server):

```bash
python -m src.main --dry-run
```

## Training

The decision tree is one possible evaluator implementation. To train it, create a CSV in `data/processed/` with columns: `species_encoded`, `ripeness`, `confidence`, `action`. Then:

```bash
python scripts/train_tree.py --data-dir data/processed --output-dir models --csv decisions.csv
```

This writes `models/decision_tree.pkl` and `models/tree_metadata.json`.

## Config

- **decision_config.yaml** — Thresholds and cooldowns per domain evaluator.
- **arduino_commands.yaml** — Maps action labels to firmware-primitive commands. Actions map to `ARM_MOVE_TO`, `PUMP_RUN`, `DOSE_RECIPE`, `VALVE_SET`, etc. — not legacy shortcodes.

## Tests

```bash
python -m pytest tests/ -v
```
