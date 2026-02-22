"""
Subtractive synthesis engine with built-in arpeggiator.

Signal path:
  OSC1 + OSC2 (detune) → SVF filter → amp envelope → output

Arpeggiator modes: OFF, UP, DOWN, RANDOM, CHORD
When arp is OFF, notes play normally via note_on/off.
When arp is active, the voice pool drives the arp clock externally
by calling arp_tick() on each sequencer step.
"""

import numpy as np
import random
from .base import SynthEngine
from ..envelope import ADSREnvelope
from ..oscillator import WavetableOscillator, midi_to_hz, WAVE_NAMES
from ..filter import SVFilter

SAMPLE_RATE = 44100

ARP_MODES = ["off", "up", "down", "random", "chord"]


class SubtractiveEngine(SynthEngine):
    name = "subtractive"

    def __init__(self):
        self.osc1 = WavetableOscillator("saw")
        self.osc2 = WavetableOscillator("square")
        self.osc_mix = 0.5      # 0 = all osc1, 1 = all osc2
        self.detune = 0.0       # semitones (osc2 offset)
        self.octave = 0         # integer octave shift (-2..2)

        self.filt = SVFilter(cutoff=2000.0, resonance=0.3, mode="lp")
        self.filter_env_amt = 0.5   # how much filter env modulates cutoff (0..1)
        self.filter_base_cutoff = 2000.0

        self.amp_env = ADSREnvelope(attack=0.005, decay=0.15, sustain=0.7, release=0.3)
        self.filt_env = ADSREnvelope(attack=0.005, decay=0.25, sustain=0.3, release=0.3)

        # Arpeggiator
        self.arp_mode = "off"
        self.arp_octaves = 1     # how many octaves to span
        self._arp_notes: list[int] = []
        self._arp_index = 0

        self._note_freq = 440.0
        self._velocity_scale = 1.0
        self._held_notes: list[int] = []

    # ------------------------------------------------------------------
    @property
    def is_active(self) -> bool:
        return self.amp_env.is_active

    def note_on(self, note: int, velocity: int):
        self._velocity_scale = velocity / 127.0
        if note not in self._held_notes:
            self._held_notes.append(note)
        if self.arp_mode == "off":
            self._trigger_note(note)
        else:
            self._rebuild_arp_sequence()

    def note_off(self):
        self._held_notes.clear()
        self.amp_env.note_off()
        self.filt_env.note_off()

    def arp_tick(self):
        """Called by the sequencer clock on each arp step."""
        if self.arp_mode == "off" or not self._arp_notes:
            return
        note = self._arp_notes[self._arp_index % len(self._arp_notes)]
        self._arp_index = (self._arp_index + 1) % len(self._arp_notes)
        self._trigger_note(note)

    # ------------------------------------------------------------------
    def _trigger_note(self, note: int):
        shifted = note + self.octave * 12
        self._note_freq = midi_to_hz(shifted)
        self.amp_env.note_on()
        self.filt_env.note_on()
        self.osc1.reset_phase()
        self.osc2.reset_phase()

    def _rebuild_arp_sequence(self):
        if not self._held_notes:
            self._arp_notes = []
            return
        base = sorted(self._held_notes)
        notes = []
        for oct_shift in range(self.arp_octaves):
            notes.extend(n + oct_shift * 12 for n in base)
        if self.arp_mode == "up":
            self._arp_notes = notes
        elif self.arp_mode == "down":
            self._arp_notes = list(reversed(notes))
        elif self.arp_mode == "random":
            self._arp_notes = notes
            random.shuffle(self._arp_notes)
        elif self.arp_mode == "chord":
            # All notes triggered together — handled differently
            self._arp_notes = notes
        self._arp_index = 0

    # ------------------------------------------------------------------
    def render_block(self, n_frames: int) -> np.ndarray:
        freq1 = self._note_freq
        # detune in semitones → multiply by 2^(detune/12)
        freq2 = self._note_freq * (2.0 ** (self.detune / 12.0))

        buf1 = self.osc1.render_block(freq1, n_frames)
        buf2 = self.osc2.render_block(freq2, n_frames)
        mix = buf1 * (1.0 - self.osc_mix) + buf2 * self.osc_mix

        # Filter envelope modulates cutoff
        filt_env_buf = self.filt_env.render_block(n_frames)
        amp_env_buf = self.amp_env.render_block(n_frames)

        out = np.empty(n_frames, dtype=np.float32)
        for i in range(n_frames):
            # Modulate cutoff
            mod = filt_env_buf[i] * self.filter_env_amt
            self.filt.cutoff = self.filter_base_cutoff * (1.0 + mod * 3.0)
            # (Filter renders one sample at a time here — wrap in array)
            tmp = np.array([mix[i]], dtype=np.float32)
            out[i] = self.filt.render_block(tmp)[0]

        out *= amp_env_buf * self._velocity_scale
        return out

    # ------------------------------------------------------------------
    def get_params(self) -> dict:
        return {
            "osc1_wave": WAVE_NAMES.index(self.osc1.wave),
            "osc2_wave": WAVE_NAMES.index(self.osc2.wave),
            "osc_mix": self.osc_mix,
            "detune": self.detune,
            "octave": self.octave,
            "filter_cutoff": self.filter_base_cutoff,
            "filter_res": self.filt.resonance,
            "filter_mode": ["lp", "hp", "bp"].index(self.filt.mode),
            "filter_env_amt": self.filter_env_amt,
            "amp_attack": self.amp_env.attack,
            "amp_decay": self.amp_env.decay,
            "amp_sustain": self.amp_env.sustain,
            "amp_release": self.amp_env.release,
            "filt_attack": self.filt_env.attack,
            "filt_decay": self.filt_env.decay,
            "filt_sustain": self.filt_env.sustain,
            "filt_release": self.filt_env.release,
            "arp_mode": ARP_MODES.index(self.arp_mode),
            "arp_octaves": self.arp_octaves,
        }

    def set_param(self, name: str, value):
        if name == "osc1_wave":
            self.osc1.set_wave(WAVE_NAMES[int(value) % len(WAVE_NAMES)])
        elif name == "osc2_wave":
            self.osc2.set_wave(WAVE_NAMES[int(value) % len(WAVE_NAMES)])
        elif name == "osc_mix":
            self.osc_mix = float(value)
        elif name == "detune":
            self.detune = float(value)
        elif name == "octave":
            self.octave = int(value)
        elif name == "filter_cutoff":
            self.filter_base_cutoff = float(value)
            self.filt.cutoff = float(value)
        elif name == "filter_res":
            self.filt.resonance = float(value)
        elif name == "filter_mode":
            self.filt.mode = ["lp", "hp", "bp"][int(value) % 3]
        elif name == "filter_env_amt":
            self.filter_env_amt = float(value)
        elif name == "amp_attack":
            self.amp_env.attack = max(0.001, float(value))
        elif name == "amp_decay":
            self.amp_env.decay = max(0.001, float(value))
        elif name == "amp_sustain":
            self.amp_env.sustain = float(value)
        elif name == "amp_release":
            self.amp_env.release = max(0.001, float(value))
        elif name == "filt_attack":
            self.filt_env.attack = max(0.001, float(value))
        elif name == "filt_decay":
            self.filt_env.decay = max(0.001, float(value))
        elif name == "filt_sustain":
            self.filt_env.sustain = float(value)
        elif name == "filt_release":
            self.filt_env.release = max(0.001, float(value))
        elif name == "arp_mode":
            self.arp_mode = ARP_MODES[int(value) % len(ARP_MODES)]
        elif name == "arp_octaves":
            self.arp_octaves = max(1, int(value))
