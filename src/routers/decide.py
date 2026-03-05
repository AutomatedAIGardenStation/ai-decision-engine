from fastapi import APIRouter

router = APIRouter()

@router.post("/decide")
def decide():
    return {
        "actions": [],
        "metadata": {
            "engine_version": "0.1.0",
            "decision_time_ms": 0
        }
    }
