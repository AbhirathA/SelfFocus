from __future__ import annotations

import random

from PySide6.QtCore import QObject, Signal

from selffocus.state import AppState
from selffocus.utils.prompts import PROMPTS


class OverlayController(QObject):
    prompt_changed = Signal(str)

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

    def choose_prompt(self) -> str:
        index = random.randrange(len(PROMPTS))
        self.state.overlay_prompt_index = index
        prompt = PROMPTS[index]
        self.prompt_changed.emit(prompt)
        return prompt
