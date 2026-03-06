# GardenStation AI Decision Engine API Contract

The AI Decision Engine exposes a stateless API for evaluating the current state of the garden and generating canonical firmware primitives to execute on the hardware.

## Endpoint

`POST /decide`

- **Request Body:** `StateSnapshot` (JSON)
- **Response Body:** `ActionList` (JSON)

## Request: StateSnapshot

The `StateSnapshot` represents the current conditions of the system. It supports two modes of operation, depending on whether the decision is driven by a scheduled loop (Legacy Payload) or an explicit event (Lightweight Event Payload).

### Legacy Payload Fields
For scheduled background evaluations, providing the full state.

- `sensor_readings` (Optional[SensorReadings]): Current chamber/zone readings.
- `ml_results` (Optional[List[MLResult]]): ML inference results.
- `plant_profiles` (Optional[List[PlantProfile]]): Crop configurations.
- `queue_state` (Optional[QueueState]): Pending/active tasks.
- `system_config` (Optional[SystemConfig]): Configuration parameters.
- `history` (Optional[History]): Historical operation records.
- `timestamp` (Optional[string]): Timestamp of snapshot.

### Lightweight Event Payload Fields
For reactive, event-driven decision making.

- `trigger_event` (Optional[string]): Event that triggered this evaluation (e.g., `EVT:SOIL_DRY`).
- `tool_state` (Optional[string]): Current active tool attached to the arm.
- `current_position` (Optional[Position]): Arm 3D coordinates.
- `sensor_snapshot` (Optional[SensorSnapshot]): Lightweight sensor readings for the event.
- `plant_targets` (Optional[List[PlantTarget]]): Specific plants related to the event.
- `harvest_queue` (Optional[List[int]]): Queue of IDs to harvest.
- `last_watered_at` (Optional[string]): Timestamp.

## Response: ActionList

The decision engine returns a list of canonical firmware primitives with execution parameters and metadata.

- `actions` (List[Action]): List of commands to execute.
  - `action` (string): Primitive name (e.g., `PUMP_RUN`).
  - `parameters` (dict): Primitive parameters.
  - `reason` (string): Human-readable explanation.
  - `priority` (string: `"high" | "medium" | "low"`): Execution priority.
- `metadata` (DecisionMetadata): Response metadata.
  - `decision_time_ms` (integer): Time taken in ms.
  - `engine_version` (string): Version string.

## Canonical Firmware Primitives

The engine generates direct instructions (primitives) for the hardware or orchestrator. The mapped actions layer is deprecated. Examples of primitives:

- `WATER_STOP`: Stop water flow.
- `PUMP_RUN`: Run water pump.
- `LIGHT_SET`: Set lighting channel and percentage.
- `FAN_SET`: Control fan speed.
- `DOSE_RECIPE`: Add nutrient dose.
- `WATER_FLUSH`: Flush water system.
- `TOOL_RELEASE`: Release the currently equipped tool.
- `TOOL_DOCK`: Return to tool dock and equip tool.
- `ARM_MOVE_TO`: Move arm to coordinates.
- `GRIPPER_CLOSE`: Close end effector gripper.

## Examples

### Legacy Payload Request Example

```json
{
  "sensor_readings": {
    "temp": 25.0,
    "humidity": 50.0,
    "ph": 6.0,
    "ec": 1.5,
    "soil_moisture": [40.0],
    "tank_level_pct": 80.0
  },
  "ml_results": [
    {
      "plant_id": 1,
      "ripeness": "unripe",
      "disease": null,
      "confidence": 0.9
    }
  ],
  "plant_profiles": [
    {
      "id": 1,
      "name": "Tomato",
      "species": "Solanum lycopersicum",
      "moisture_target": 60.0,
      "ec_target": 1.5,
      "ph_min": 5.5,
      "ph_max": 6.5,
      "pollination_window": {
        "start_hour": 0,
        "end_hour": 23,
        "interval_days": 1
      }
    }
  ],
  "queue_state": {
    "harvest_pending_ids": [],
    "active_harvest_id": null
  },
  "system_config": {
    "maintenance_mode": false,
    "zone_count": 1,
    "max_pump_time_s": 60,
    "temp_min": 18.0,
    "temp_max": 30.0,
    "light_schedule": []
  },
  "history": {
    "last_watering": {},
    "last_pollination": "2020-01-01T00:00:00Z"
  },
  "timestamp": "2023-10-27T10:00:00Z"
}
```

### Lightweight Event Payload Request Example

```json
{
  "trigger_event": "EVT:SOIL_DRY",
  "tool_state": "CAMERA",
  "current_position": {
    "x": 100,
    "y": 200,
    "z": 50
  },
  "sensor_snapshot": {
    "ec": 1.8,
    "ph": 6.2,
    "water_temp": 22.0,
    "air_temp": 25.0,
    "air_humidity": 60.0
  },
  "plant_targets": [
    {
      "plant_id": 1,
      "x": 100,
      "y": 200,
      "z": 50,
      "ec_target": 2.0,
      "ph_target": 6.0
    }
  ],
  "harvest_queue": [1],
  "last_watered_at": "2020-01-01T00:00:00Z"
}
```

### Response Example

```json
{
  "actions": [
    {
      "action": "TOOL_DOCK",
      "parameters": {
        "tool": "WATERING_NOZZLE"
      },
      "reason": "Must equip WATERING_NOZZLE for watering",
      "priority": "high"
    },
    {
      "action": "PUMP_RUN",
      "parameters": {
        "duration_s": 10,
        "volume_ml": 500
      },
      "reason": "Event EVT:SOIL_DRY triggered for plant 1",
      "priority": "high"
    }
  ],
  "metadata": {
    "decision_time_ms": 15,
    "engine_version": "0.1.0"
  }
}
```

## Compatibility Notes

1.  **Stateless API**: The decision engine is entirely stateless and does not cache previous events. It relies purely on the state provided in the `StateSnapshot`.
2.  **Backwards Compatibility**: Both the legacy scheduling system and the new event-driven orchestrator can interact with the same `/decide` endpoint. If `trigger_event` is present, the engine switches to the lightweight event evaluators. Otherwise, it falls back to the legacy stateful evaluations. Optional fields ensure older clients are not broken by newer additions.
3.  **Side Effects**: Serial communication and hardware side effects are completely isolated to the optional CLI adapter. The API endpoint strictly returns an action list and performs no direct hardware manipulation.
