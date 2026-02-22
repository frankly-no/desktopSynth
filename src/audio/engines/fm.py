"""
4-operator FM synthesis engine.

Operators are numbered 0-3.  Each operator has:
  - frequency ratio (relative to note frequency)
  - amplitude level (0..1)
  - feedback amount (only op 0 self-modulates)
  - ADSR envelope

Six algorithms define operator routing (carrier vs modulator relationships).
Algorithm diagram notation: mod → carrier  (mod feeds carrier)

Algorithm 0:  3→2→1→0  (all series)
Algorithm 1:  (2→0) + (3→1→0)
Algorithm 2:  (1→0) + (2→0) + (3→0)
Algorithm 3:  3→(2→0) + (2→1) [2 modulates both 0 and 1]
Algorithm 4:  (1→0) + (2→0) + 3 [3 is carrier]
Algorithm 5:  0+1+2+3  (all carriers / additive)
"""

import numpy as np
import math
from .base import SynthEngine
from ..envelope import ADSREnvelope
from ..oscillator import midi_to_hz

SAMPLE_RATE = 44100


# Each algorithm is a list of (modulator_indices, carrier_flag) per operator.
# Carrier operators contribute to the final output sum.
# Representation: list of 4 entries, each: (list_of_mod_sources, is_carrier)
ALGORITHMS = [
    # 0: 3→2→1→0 full series
    [([],    False),   # op0: modulated by op1, not carrier
     ([0],   False),   # op1: modulated by op2
     ([1],   False),   # op2: modulated by op3
     ([2],   True)],   # op3: carrier
    # 1: (2→1→0) + (3→0)
    [([],    False),
     ([0],   False),
     ([1],   True),
     ([0],   True)],
    # 2: (1→0) + (2→0) + 3
    [([],    False),
     ([0],   True),
     ([0],   True),
     ([],    True)],
    # 3: 3→2→(0+1)
    [([],    True),
     ([],    True),
     ([0,1], False),
     ([2],   False)],
    # 4: (1→0)+(2→0)+3
    [([],    False),
     ([0],   True),
     ([0],   True),
     ([],    True)],
    # 5: additive — all carriers
    [([],    True),
     ([],    True),
     ([],    True),
     ([],    True)],
]

N_OPS = 4
N_ALGORITHMS = len(ALGORITHMS)


class FMOperator:
    def __init__(self):
        self.ratio = 1.0       # freq = note_freq * ratio
        self.level = 0.7       # output amplitude 0..1
        self.feedback = 0.0    # self-feedback (op0 only)
        self.env = ADSREnvelope(attack=0.005, decay=0.2, sustain=0.5, release=0.4)
        self._phase = 0.0
        self._last_out = 0.0   # for feedback

    def render_sample(self, freq_hz: float, mod_input: float, env_val: float) -> float:
        phase_inc = freq_hz * self.ratio / SAMPLE_RATE
        self._phase += phase_inc
        self._phase -= math.floor(self._phase)
        total_mod = mod_input + self.feedback * self._last_out
        sample = self.level * env_val * math.sin(2.0 * math.pi * self._phase + 2.0 * math.pi * total_mod)
        self._last_out = sample
        return sample

    def note_on(self):
        self.env.note_on()
        self._phase = 0.0
        self._last_out = 0.0

    def note_off(self):
        self.env.note_off()


class FMEngine(SynthEngine):
    name = "fm"

    def __init__(self):
        self.ops = [FMOperator() for _ in range(N_OPS)]
        self.ops[0].ratio = 1.0
        self.ops[1].ratio = 2.0
        self.ops[2].ratio = 3.0
        self.ops[3].ratio = 1.0
        self.algorithm = 0
        self._note_freq = 440.0
        self._velocity_scale = 1.0

    # ------------------------------------------------------------------
    @property
    def is_active(self) -> bool:
        return any(op.env.is_active for op in self.ops)

    def note_on(self, note: int, velocity: int):
        self._note_freq = midi_to_hz(note)
        self._velocity_scale = velocity / 127.0
        for op in self.ops:
            op.note_on()

    def note_off(self):
        for op in self.ops:
            op.note_off()

    # ------------------------------------------------------------------
    def render_block(self, n_frames: int) -> np.ndarray:
        alg = ALGORITHMS[self.algorithm]
        out = np.zeros(n_frames, dtype=np.float32)

        # Pre-render envelopes for all ops
        env_blocks = [op.env.render_block(n_frames) for op in self.ops]
        op_outputs = [np.zeros(n_frames, dtype=np.float32) for _ in range(N_OPS)]

        # Render per sample in dependency order (op 0 first, then 1, 2, 3)
        for i in range(n_frames):
            for op_idx in range(N_OPS):
                mod_sources, is_carrier = alg[op_idx]
                mod_input = sum(op_outputs[src][i] for src in mod_sources)
                env_val = env_blocks[op_idx][i]
                sample = self.ops[op_idx].render_sample(
                    self._note_freq, mod_input, env_val
                )
                op_outputs[op_idx][i] = sample
                if is_carrier:
                    out[i] += sample

        # Normalize by carrier count and apply velocity
        n_carriers = sum(1 for _, is_carrier in alg if is_carrier)
        if n_carriers > 1:
            out /= n_carriers
        out *= self._velocity_scale
        return out

    # ------------------------------------------------------------------
    def get_params(self) -> dict:
        params = {"algorithm": self.algorithm}
        for i, op in enumerate(self.ops):
            params[f"op{i}_ratio"] = op.ratio
            params[f"op{i}_level"] = op.level
            params[f"op{i}_feedback"] = op.feedback
            params[f"op{i}_attack"] = op.env.attack
            params[f"op{i}_decay"] = op.env.decay
            params[f"op{i}_sustain"] = op.env.sustain
            params[f"op{i}_release"] = op.env.release
        return params

    def set_param(self, name: str, value):
        if name == "algorithm":
            self.algorithm = int(value) % N_ALGORITHMS
            return
        # op0_ratio, op1_level, etc.
        parts = name.split("_", 1)
        if len(parts) == 2 and parts[0].startswith("op"):
            try:
                op_idx = int(parts[0][2:])
            except ValueError:
                return
            attr = parts[1]
            op = self.ops[op_idx]
            if attr == "ratio":
                op.ratio = max(0.01, float(value))
            elif attr == "level":
                op.level = float(value)
            elif attr == "feedback":
                op.feedback = float(value)
            elif attr == "attack":
                op.env.attack = max(0.001, float(value))
            elif attr == "decay":
                op.env.decay = max(0.001, float(value))
            elif attr == "sustain":
                op.env.sustain = float(value)
            elif attr == "release":
                op.env.release = max(0.001, float(value))
