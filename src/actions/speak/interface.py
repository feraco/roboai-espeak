from dataclasses import dataclass
from typing import Optional

from actions.base import Interface


@dataclass
class SpeakInput:
    sentence: str
    language: Optional[str] = "en"  # Language code: en, es, ru


@dataclass
class Speak(Interface[SpeakInput, SpeakInput]):
    """
    This action allows you to speak in multiple languages.
    
    Supported languages:
    - en: English (default)
    - es: Spanish 
    - ru: Russian
    
    The TTS voice will be selected automatically based on the language.
    """

    input: SpeakInput
    output: SpeakInput
