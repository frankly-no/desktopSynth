"""
BPM clock.  Fires a step_callback(step_index) on each 16th-note step.
Uses time.perf_counter for sub-millisecond accuracy.
"""

import threading
import time
from typing import Callable


class Clock:
    def __init__(self, bpm: float = 120.0):
        self.bpm = bpm
        self._running = False
        self._thread: threading.Thread | None = None
        self._step: int = 0
        self.n_steps: int = 16
        self.swing: float = 0.0  # 0..1

        # Callbacks registered by external code
        self._step_callbacks: list[Callable[[int], None]] = []

    def add_step_callback(self, cb: Callable[[int], None]):
        self._step_callbacks.append(cb)

    def remove_step_callback(self, cb: Callable[[int], None]):
        self._step_callbacks.remove(cb)

    def start(self):
        if self._running:
            return
        self._running = True
        self._step = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        self._step = 0

    def reset(self):
        self._step = 0

    def _step_duration(self, step: int) -> float:
        """
        Duration of one 16th-note step in seconds, with optional swing.
        Odd steps (every other) get slightly longer/shorter for swing feel.
        """
        base = 60.0 / self.bpm / 4.0  # 16th note duration
        if self.swing == 0.0:
            return base
        # Swing: even steps get (1 + swing) × base, odd get (1 - swing) × base
        swing_amount = self.swing * 0.33  # max ±33% swing
        if step % 2 == 0:
            return base * (1.0 + swing_amount)
        else:
            return base * (1.0 - swing_amount)

    def _run(self):
        next_tick = time.perf_counter()
        while self._running:
            step = self._step
            # Fire callbacks
            for cb in self._step_callbacks:
                try:
                    cb(step)
                except Exception:
                    pass

            duration = self._step_duration(step)
            self._step = (step + 1) % self.n_steps
            next_tick += duration

            # Sleep precisely
            sleep_time = next_tick - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
