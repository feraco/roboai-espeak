from dataclasses import dataclass
from enum import Enum

from actions.base import Interface


class MoveToPeerAction(str, Enum):
    IDLE = "idle"
    NAVIGATE = "navigate"


@dataclass
class MoveToPeerInput:
    action: MoveToPeerAction


@dataclass
class MoveToPeer(Interface[MoveToPeerInput, MoveToPeerInput]):
    """
    Instruct Unitree to move toward the nearest peer discovered,
    or do nothing if idle.
    """

    input: MoveToPeerInput
    output: MoveToPeerInput
