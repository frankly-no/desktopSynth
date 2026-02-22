"""
4-voice pool with round-robin allocation and oldest-note stealing.
Each of the 4 slots has an independently configurable engine type.
"""

import numpy as np
import threading
from .voice import Voice

N_VOICES = 4


class VoicePool:
    def __init__(self):
        # Each voice defaults to a different engine for demonstration
        defaults = ["fm", "vector", "subtractive", "fm"]
        self.voices = [Voice(engine) for engine in defaults]
        self._lock = threading.Lock()
        # Round-robin allocation counter
        self._next_voice = 0

    # ------------------------------------------------------------------
    # Engine configuration
    # ------------------------------------------------------------------

    def set_track_engine(self, track_idx: int, engine_name: str):
        """Change the engine type for a specific track/voice slot."""
        with self._lock:
            self.voices[track_idx].change_engine(engine_name)

    def set_track_param(self, track_idx: int, param: str, value):
        with self._lock:
            self.voices[track_idx].engine.set_param(param, value)

    # ------------------------------------------------------------------
    # Note events
    # ------------------------------------------------------------------

    def note_on(self, track_idx: int | None, note: int, velocity: int):
        """
        Trigger a note.
        If track_idx is None, auto-allocate a free voice (for MIDI input).
        If track_idx is given, use that specific voice slot.
        """
        with self._lock:
            if track_idx is not None:
                voice = self.voices[track_idx % N_VOICES]
            else:
                voice = self._allocate()
            voice.note_on(note, velocity)

    def note_off(self, track_idx: int | None, note: int):
        with self._lock:
            if track_idx is not None:
                v = self.voices[track_idx % N_VOICES]
                if v.current_note == note:
                    v.note_off()
            else:
                # Release any voice playing this note
                for v in self.voices:
                    if v.current_note == note:
                        v.note_off()

    def _allocate(self) -> Voice:
        """Find a free voice; steal the oldest if all busy."""
        # Prefer voices that are truly idle
        for v in self.voices:
            if v.is_free:
                return v
        # All busy — steal round-robin
        v = self.voices[self._next_voice % N_VOICES]
        self._next_voice = (self._next_voice + 1) % N_VOICES
        return v

    # ------------------------------------------------------------------
    # Audio rendering
    # ------------------------------------------------------------------

    def render(self, n_frames: int) -> np.ndarray:
        """Mix all 4 voices into a single mono float32 buffer."""
        out = np.zeros(n_frames, dtype=np.float32)
        with self._lock:
            for voice in self.voices:
                out += voice.render(n_frames)
        # Soft clip to prevent hard clipping on summing
        np.clip(out, -1.0, 1.0, out=out)
        return out
