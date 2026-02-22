"""Abstract base class for synthesis engines."""

import numpy as np
from abc import ABC, abstractmethod


class SynthEngine(ABC):
    """
    All synth engines share this interface.
    Engines are stateful — one instance per voice.
    """

    name: str = "base"

    @abstractmethod
    def note_on(self, note: int, velocity: int):
        """Start a note (MIDI note 0-127, velocity 0-127)."""

    @abstractmethod
    def note_off(self):
        """Release the note."""

    @abstractmethod
    def render_block(self, n_frames: int) -> np.ndarray:
        """
        Render n_frames of audio.
        Returns float32 mono array in range roughly -1..1.
        """

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """True while the envelope is still producing sound."""

    @abstractmethod
    def get_params(self) -> dict:
        """Return current parameter dict {name: value}."""

    @abstractmethod
    def set_param(self, name: str, value):
        """Set a parameter by name."""

    def set_params(self, params: dict):
        for k, v in params.items():
            self.set_param(k, v)
