from dataclasses import dataclass
from enum import Enum

from actions.base import Interface


class FaceAction(str, Enum):
    HAPPY = "happy"
    CONFUSED = "confused"
    CURIOUS = "curious"
    EXCITED = "excited"
    SAD = "sad"
    THINK = "think"


@dataclass
class FaceInput:
    action: FaceAction


@dataclass
class Face(Interface[FaceInput, FaceInput]):
    """
    This action allows you to show facial expressions.
    """

    input: FaceInput
    output: FaceInput
