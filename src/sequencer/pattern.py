"""A pattern: 4 tracks, BPM, swing."""

from .track import Track

N_TRACKS = 4


class Pattern:
    def __init__(self):
        self.tracks: list[Track] = [Track(i) for i in range(N_TRACKS)]
        self.bpm: float = 120.0
        self.swing: float = 0.0      # 0..1, swing amount
        self.n_steps: int = 16

    def track(self, idx: int) -> Track:
        return self.tracks[idx % N_TRACKS]
