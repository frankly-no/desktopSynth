"""Single voice: wraps a SynthEngine with note allocation state."""

import numpy as np
from .engines import SynthEngine, make_engine


class Voice:
    def __init__(self, engine_name: str = "fm"):
        self.engine: SynthEngine = make_engine(engine_name)
        self.current_note: int | None = None
        self.active: bool = False
        self.velocity: int = 100
        self._engine_name = engine_name

    def change_engine(self, engine_name: str):
        if engine_name != self._engine_name:
            self._engine_name = engine_name
            self.engine = make_engine(engine_name)
            self.current_note = None
            self.active = False

    def note_on(self, note: int, velocity: int):
        self.current_note = note
        self.velocity = velocity
        self.active = True
        self.engine.note_on(note, velocity)

    def note_off(self):
        self.engine.note_off()

    def render(self, n_frames: int) -> np.ndarray:
        if not self.engine.is_active:
            self.active = False
            return np.zeros(n_frames, dtype=np.float32)
        return self.engine.render_block(n_frames)

    @property
    def is_free(self) -> bool:
        return not self.active and not self.engine.is_active
