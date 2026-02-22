"""Basic oscillators with band-limited wavetable lookup."""

import numpy as np

SAMPLE_RATE = 44100
TABLE_SIZE = 2048

# Pre-computed wavetables (normalized -1..1)
_SINE_TABLE = np.sin(2.0 * np.pi * np.arange(TABLE_SIZE) / TABLE_SIZE).astype(np.float32)

# Naive saw (will alias at high frequencies — acceptable for prototype)
_SAW_TABLE = (2.0 * np.arange(TABLE_SIZE) / TABLE_SIZE - 1.0).astype(np.float32)

# Square
_SQ = np.ones(TABLE_SIZE, dtype=np.float32)
_SQ[TABLE_SIZE // 2 :] = -1.0
_SQUARE_TABLE = _SQ

# Triangle
_tri_x = np.arange(TABLE_SIZE)
_TRIANGLE_TABLE = (
    2.0 * np.abs(2.0 * _tri_x / TABLE_SIZE - 1.0) - 1.0
).astype(np.float32)

WAVE_TABLES = {
    "sine": _SINE_TABLE,
    "saw": _SAW_TABLE,
    "square": _SQUARE_TABLE,
    "triangle": _TRIANGLE_TABLE,
}

WAVE_NAMES = ["sine", "saw", "square", "triangle"]


def midi_to_hz(note: int) -> float:
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


class WavetableOscillator:
    """Single wavetable oscillator with phase accumulator."""

    def __init__(self, wave: str = "sine"):
        self.wave = wave
        self._phase = 0.0  # 0..TABLE_SIZE

    def set_wave(self, wave: str):
        self.wave = wave

    def render_block(self, freq: float, n_frames: int) -> np.ndarray:
        """Return float32 array of length n_frames."""
        table = WAVE_TABLES[self.wave]
        phase_inc = freq * TABLE_SIZE / SAMPLE_RATE
        out = np.empty(n_frames, dtype=np.float32)
        phase = self._phase
        for i in range(n_frames):
            idx = int(phase) % TABLE_SIZE
            frac = phase - int(phase)
            # Linear interpolation
            next_idx = (idx + 1) % TABLE_SIZE
            out[i] = table[idx] + frac * (table[next_idx] - table[idx])
            phase += phase_inc
        self._phase = phase % TABLE_SIZE
        return out

    def reset_phase(self):
        self._phase = 0.0


class NoiseOscillator:
    """White noise source."""

    def render_block(self, n_frames: int) -> np.ndarray:
        return np.random.uniform(-1.0, 1.0, n_frames).astype(np.float32)
