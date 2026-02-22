"""A sequencer track: 16 steps + engine assignment + MIDI routing."""

from .step import Step

N_STEPS = 16


class Track:
    def __init__(self, track_idx: int, engine_name: str = "fm"):
        self.track_idx = track_idx
        self.engine_name = engine_name
        self.steps: list[Step] = [Step() for _ in range(N_STEPS)]
        self.midi_channel: int = track_idx  # 0-based
        self.midi_out_enabled: bool = False
        self.muted: bool = False

    def set_engine(self, engine_name: str):
        self.engine_name = engine_name

    def step_at(self, idx: int) -> Step:
        return self.steps[idx % N_STEPS]

    def active_steps(self) -> list[tuple[int, Step]]:
        return [(i, s) for i, s in enumerate(self.steps) if s.active]
