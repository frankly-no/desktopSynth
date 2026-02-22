"""Chamberlin State Variable Filter (LP / HP / BP)."""

import numpy as np
import math

SAMPLE_RATE = 44100


class SVFilter:
    """
    Two-pole Chamberlin state variable filter.
    Provides simultaneous LP, HP, and BP outputs.
    Cutoff: 20..20000 Hz   Resonance: 0.0 (none) .. ~0.99 (self-oscillation)
    """

    def __init__(self, cutoff: float = 1000.0, resonance: float = 0.5, mode: str = "lp"):
        self.cutoff = cutoff
        self.resonance = resonance  # 0..1
        self.mode = mode  # "lp", "hp", "bp"
        self._low = 0.0
        self._band = 0.0

    def reset(self):
        self._low = 0.0
        self._band = 0.0

    def render_block(self, signal: np.ndarray) -> np.ndarray:
        """Filter signal in-place and return filtered float32 array."""
        n = len(signal)
        out = np.empty(n, dtype=np.float32)

        # Limit cutoff to safe range
        fc = min(max(self.cutoff, 20.0), SAMPLE_RATE * 0.49)
        f = 2.0 * math.sin(math.pi * fc / SAMPLE_RATE)
        # Map resonance 0..1 → q 2.0..0.01 (lower q = more resonant)
        q = 2.0 - 1.99 * self.resonance

        low = self._low
        band = self._band

        for i in range(n):
            s = float(signal[i])
            low = low + f * band
            high = s - low - q * band
            band = f * high + band
            if self.mode == "lp":
                out[i] = low
            elif self.mode == "hp":
                out[i] = high
            else:  # bp
                out[i] = band

        self._low = low
        self._band = band
        return out
