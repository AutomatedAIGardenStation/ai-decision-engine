from fastapi import APIRouter
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import ActionList
from src.router import DecisionRouter

router = APIRouter()

@router.post("/decide", response_model=ActionList)
def decide(state: StateSnapshot):
    return DecisionRouter().evaluate(state)
