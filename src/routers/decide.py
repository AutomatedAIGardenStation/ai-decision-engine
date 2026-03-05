from fastapi import APIRouter
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import ActionList, DecisionMetadata
from src.evaluators.watering import WateringEvaluator

router = APIRouter()

@router.post("/decide", response_model=ActionList)
def decide(state: StateSnapshot):
    actions = WateringEvaluator.evaluate(state)

    return ActionList(
        actions=actions,
        metadata=DecisionMetadata(
            engine_version="0.1.0",
            decision_time_ms=0
        )
    )
