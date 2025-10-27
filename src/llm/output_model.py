from typing import Union
from pydantic import BaseModel, Field


class Action(BaseModel):
    """
    Executable action with its argument.

    Parameters
    ----------
    type : str
        Type of action to execute, such as 'move' or 'speak'
    value : str | dict
        The action argument, such as the magnitude of a movement or the sentence to speak.
        Can be a string for simple actions or a dict for complex actions (e.g., with language parameter).
    """

    type: str = Field(
        ..., description="The specific type of action, such as 'move' or 'speak'"
    )
    value: Union[str, dict] = Field(..., description="The action argument")


class CortexOutputModel(BaseModel):
    """
    Output model for the Cortex LLM responses.

    Parameters
    ----------
    actions : list[Action]
        List of actions to be executed
    """

    actions: list[Action] = Field(..., description="List of actions to execute")
