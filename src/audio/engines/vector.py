"""
Vector synthesis engine.
Four wavetable oscillators (A/B/C/D) crossfaded via an XY position:

         C
         |
    A ---+--- B
         |
         D

XY = (0.5, 0.5) → equal mix of all four.
XY = (0.0, 0.5) → pure A.
XY = (1.0, 0.5) → pure B.
XY = (0.5, 0.0) → pure C.
XY = (0.5, 1.0) → pure D.

Optional LFO modulates the XY position over time.
Output passes through a Chamberlin SVF + ADSR amp envelope.
"""

import numpy as np
import math
from .base import SynthEngine
from ..envelope import ADSREnvelope
from ..oscillator import WavetableOscillator, midi_to_hz, WAVE_NAMES
from ..filter import SVFilter

SAMPLE_RATE = 44100


class VectorEngine(SynthEngine):
    name = "vector"

    def __init__(self):
        # Four corner oscillators
        self.oscs = [WavetableOscillator(w) for w in ("sine", "saw", "square", "triangle")]
        self.xy = [0.5, 0.5]  # x: A↔B, y: C↔D

        # LFO
        self.lfo_rate = 0.5     # Hz
        self.lfo_depth = 0.0    # 0..1
        self._lfo_phase = 0.0

        # Filter
        self.filt = SVFilter(cutoff=4000.0, resonance=0.2, mode="lp")

        # Envelope
        self.env = ADSREnvelope(attack=0.01, decay=0.2, sustain=0.6, release=0.5)

        self._note_freq = 440.0
        self._velocity_scale = 1.0

    @property
    def is_active(self) -> bool:
        return self.env.is_active

    def note_on(self, note: int, velocity: int):
        self._note_freq = midi_to_hz(note)
        self._velocity_scale = velocity / 127.0
        self.env.note_on()
        for osc in self.oscs:
            osc.reset_phase()

    def note_off(self):
        self.env.note_off()

    def render_block(self, n_frames: int) -> np.ndarray:
        # Render all 4 oscillators
        osc_bufs = [osc.render_block(self._note_freq, n_frames) for osc in self.oscs]

        # LFO
        lfo_inc = self.lfo_rate / SAMPLE_RATE
        lfo = np.empty(n_frames, dtype=np.float32)
        ph = self._lfo_phase
        for i in range(n_frames):
            lfo[i] = math.sin(2.0 * math.pi * ph)
            ph += lfo_inc
        self._lfo_phase = ph % 1.0

        # Mix based on XY + LFO
        x_base = self.xy[0]
        y_base = self.xy[1]
        out = np.empty(n_frames, dtype=np.float32)
        for i in range(n_frames):
            lfo_offset = lfo[i] * self.lfo_depth * 0.5
            x = min(max(x_base + lfo_offset, 0.0), 1.0)
            y = min(max(y_base + lfo_offset, 0.0), 1.0)
            # A (left) ↔ B (right) along X; C (top) ↔ D (bottom) along Y
            ab = osc_bufs[0][i] * (1.0 - x) + osc_bufs[1][i] * x
            cd = osc_bufs[2][i] * (1.0 - y) + osc_bufs[3][i] * y
            out[i] = (ab + cd) * 0.5

        # Filter
        out = self.filt.render_block(out)

        # Envelope
        env_buf = self.env.render_block(n_frames)
        out *= env_buf * self._velocity_scale
        return out

    def get_params(self) -> dict:
        return {
            "osc_a": WAVE_NAMES.index(self.oscs[0].wave),
            "osc_b": WAVE_NAMES.index(self.oscs[1].wave),
            "osc_c": WAVE_NAMES.index(self.oscs[2].wave),
            "osc_d": WAVE_NAMES.index(self.oscs[3].wave),
            "xy_x": self.xy[0],
            "xy_y": self.xy[1],
            "lfo_rate": self.lfo_rate,
            "lfo_depth": self.lfo_depth,
            "filter_cutoff": self.filt.cutoff,
            "filter_res": self.filt.resonance,
            "filter_mode": ["lp", "hp", "bp"].index(self.filt.mode),
            "attack": self.env.attack,
            "decay": self.env.decay,
            "sustain": self.env.sustain,
            "release": self.env.release,
        }

    def set_param(self, name: str, value):
        if name.startswith("osc_"):
            idx = {"osc_a": 0, "osc_b": 1, "osc_c": 2, "osc_d": 3}.get(name)
            if idx is not None:
                self.oscs[idx].set_wave(WAVE_NAMES[int(value) % len(WAVE_NAMES)])
        elif name == "xy_x":
            self.xy[0] = float(value)
        elif name == "xy_y":
            self.xy[1] = float(value)
        elif name == "lfo_rate":
            self.lfo_rate = max(0.01, float(value))
        elif name == "lfo_depth":
            self.lfo_depth = float(value)
        elif name == "filter_cutoff":
            self.filt.cutoff = float(value)
        elif name == "filter_res":
            self.filt.resonance = float(value)
        elif name == "filter_mode":
            self.filt.mode = ["lp", "hp", "bp"][int(value) % 3]
        elif name == "attack":
            self.env.attack = max(0.001, float(value))
        elif name == "decay":
            self.env.decay = max(0.001, float(value))
        elif name == "sustain":
            self.env.sustain = float(value)
        elif name == "release":
            self.env.release = max(0.001, float(value))
