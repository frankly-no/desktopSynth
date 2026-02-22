"""ADSR envelope generator."""

import numpy as np
from enum import Enum


class EnvState(Enum):
    IDLE = 0
    ATTACK = 1
    DECAY = 2
    SUSTAIN = 3
    RELEASE = 4


SAMPLE_RATE = 44100


def _time_to_samples(seconds: float) -> int:
    return max(1, int(seconds * SAMPLE_RATE))


class ADSREnvelope:
    """Per-sample ADSR envelope. Render via render_block() for vectorized output."""

    def __init__(self, attack=0.01, decay=0.1, sustain=0.7, release=0.3):
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release

        self._state = EnvState.IDLE
        self._level = 0.0
        self._release_level = 0.0

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def note_on(self):
        self._state = EnvState.ATTACK
        # Re-trigger from current level for legato feel
        self._release_level = self._level

    def note_off(self):
        if self._state != EnvState.IDLE:
            self._release_level = self._level
            self._state = EnvState.RELEASE

    @property
    def is_active(self) -> bool:
        return self._state != EnvState.IDLE

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_block(self, n_frames: int) -> np.ndarray:
        """Return float32 array of envelope values, length n_frames."""
        out = np.empty(n_frames, dtype=np.float32)
        for i in range(n_frames):
            out[i] = self._tick()
        return out

    def _tick(self) -> float:
        if self._state == EnvState.IDLE:
            return 0.0

        elif self._state == EnvState.ATTACK:
            atk_rate = 1.0 / _time_to_samples(self.attack)
            self._level += atk_rate
            if self._level >= 1.0:
                self._level = 1.0
                self._state = EnvState.DECAY
            return self._level

        elif self._state == EnvState.DECAY:
            dec_rate = (1.0 - self.sustain) / _time_to_samples(self.decay)
            self._level -= dec_rate
            if self._level <= self.sustain:
                self._level = self.sustain
                self._state = EnvState.SUSTAIN
            return self._level

        elif self._state == EnvState.SUSTAIN:
            self._level = self.sustain
            return self._level

        elif self._state == EnvState.RELEASE:
            rel_rate = self._release_level / _time_to_samples(self.release)
            self._level -= rel_rate
            if self._level <= 0.0:
                self._level = 0.0
                self._state = EnvState.IDLE
            return self._level

        return 0.0
