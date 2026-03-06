from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict

class Action(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """An individual action to be executed by the system."""
    action: str = Field(..., description="The name or type of the action to perform")
    parameters: dict = Field(..., description="Key-value parameters for the action")
    reason: str = Field(..., description="A short explanation of why this action was taken")
    priority: Literal["high", "medium", "low"] = Field(..., description="Execution priority level")

class DecisionMetadata(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """Metadata regarding the decision-making process."""
    decision_time_ms: int = Field(..., description="Time taken to make the decision in milliseconds")
    engine_version: str = Field(..., description="Version of the decision engine")

class ActionList(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """The complete response from the decision engine, including actions and metadata."""
    actions: List[Action] = Field(..., description="List of actions to execute")
    metadata: DecisionMetadata = Field(..., description="Decision metadata")
