"""A single sequencer step."""

from dataclasses import dataclass, field


@dataclass
class Step:
    active: bool = False
    note: int = 60        # MIDI note (middle C)
    velocity: int = 100   # 0..127
    length: float = 0.5   # note length in steps (0.0..1.0)
    param_locks: dict = field(default_factory=dict)  # {param_name: value}

    def toggle(self):
        self.active = not self.active

    def set_param_lock(self, param: str, value):
        self.param_locks[param] = value

    def clear_param_lock(self, param: str):
        self.param_locks.pop(param, None)
