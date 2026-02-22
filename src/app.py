"""
App: top-level controller that wires together:
  - Audio engine (voice pool + sounddevice)
  - Sequencer (pattern + clock)
  - MIDI I/O
  - UI (Dear PyGui)

Threading model:
  Main thread  → Dear PyGui render loop
  Audio thread → sounddevice callback
  Clock thread → BPM step ticks
  MIDI-in      → rtmidi callback
"""

import threading
import queue

from src.audio.engine import AudioEngine
from src.sequencer.pattern import Pattern
from src.sequencer.clock import Clock
from src.midi.input import MidiInput
from src.midi.output import MidiOutput
from src.ui.main_window import MainWindow


class App:
    def __init__(self):
        # Core state
        self.pattern = Pattern()

        # Sub-systems
        self.audio = AudioEngine()
        self.clock = Clock(bpm=120.0)
        self.midi_in = MidiInput()
        self.midi_out = MidiOutput()

        # Thread-safe queue for playhead UI updates
        # (clock fires from a non-UI thread; DPG must be updated on main thread)
        self._ui_queue: queue.Queue = queue.Queue()

        # Build UI
        self.window = MainWindow(
            pattern=self.pattern,
            on_play=self._on_play,
            on_stop=self._on_stop,
            on_bpm_change=self._on_bpm_change,
            on_swing_change=self._on_swing_change,
            on_step_toggle=self._on_step_toggle,
            on_engine_change=self._on_engine_change,
            on_param_change=self._on_param_change,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def run(self):
        self.window.setup()
        self._setup_midi()
        self.audio.start()

        # Register sequencer clock callback
        self.clock.add_step_callback(self._on_step_tick)

        # Main render loop
        while self.window.is_running():
            # Drain UI updates queued from background threads
            while True:
                try:
                    fn = self._ui_queue.get_nowait()
                    fn()
                except queue.Empty:
                    break
            self.window.run_frame()

        self._shutdown()

    def _shutdown(self):
        self.clock.stop()
        self.audio.stop()
        self.midi_in.close()
        self.midi_out.close()
        self.window.teardown()

    # ------------------------------------------------------------------
    # MIDI setup
    # ------------------------------------------------------------------

    def _setup_midi(self):
        self.midi_in.set_callbacks(
            note_on=self._midi_note_on,
            note_off=self._midi_note_off,
        )
        in_ports = self.midi_in.list_ports()
        if in_ports:
            self.midi_in.open_port(0)

        out_ports = self.midi_out.list_ports()
        if out_ports:
            self.midi_out.open_port(0)

    # ------------------------------------------------------------------
    # Transport callbacks (called from UI thread)
    # ------------------------------------------------------------------

    def _on_play(self):
        self.clock.start()

    def _on_stop(self):
        self.clock.stop()
        # Send note-offs for all tracks
        for t in range(4):
            for step in self.pattern.track(t).steps:
                if step.active:
                    self.audio.note_off(t, step.note)
                    if self.pattern.track(t).midi_out_enabled:
                        self.midi_out.note_off(self.pattern.track(t).midi_channel, step.note)

    def _on_bpm_change(self, bpm: float):
        self.clock.bpm = bpm
        self.pattern.bpm = bpm

    def _on_swing_change(self, swing: float):
        self.clock.swing = swing
        self.pattern.swing = swing

    # ------------------------------------------------------------------
    # Sequencer step tick (called from clock thread)
    # ------------------------------------------------------------------

    def _on_step_tick(self, step_idx: int):
        for track_idx in range(4):
            track = self.pattern.track(track_idx)
            if track.muted:
                continue
            s = track.step_at(step_idx)

            # Send note-off for previous step on this track
            prev_idx = (step_idx - 1) % self.pattern.n_steps
            prev_step = track.step_at(prev_idx)
            if prev_step.active:
                self.audio.note_off(track_idx, prev_step.note)
                if track.midi_out_enabled:
                    self.midi_out.note_off(track.midi_channel, prev_step.note)

            if s.active:
                # Apply parameter locks before triggering
                for param, val in s.param_locks.items():
                    self.audio.set_param(track_idx, param, val)
                self.audio.note_on(track_idx, s.note, s.velocity)
                if track.midi_out_enabled:
                    self.midi_out.note_on(track.midi_channel, s.note, s.velocity)

        # Queue playhead update for the UI thread
        self._ui_queue.put_nowait(lambda idx=step_idx: self.window.update_playhead(idx))

    # ------------------------------------------------------------------
    # UI parameter callbacks (UI thread)
    # ------------------------------------------------------------------

    def _on_step_toggle(self, track_idx: int, step_idx: int):
        self.pattern.track(track_idx).step_at(step_idx).toggle()

    def _on_engine_change(self, track_idx: int, engine_name: str):
        self.pattern.track(track_idx).set_engine(engine_name)
        self.audio.set_engine(track_idx, engine_name)

    def _on_param_change(self, track_idx: int, param: str, value):
        self.audio.set_param(track_idx, param, value)

    # ------------------------------------------------------------------
    # MIDI input callbacks (MIDI thread → audio thread)
    # ------------------------------------------------------------------

    def _midi_note_on(self, note: int, velocity: int):
        # Incoming MIDI plays on voice 0 by default (auto-allocate)
        self.audio.note_on(None, note, velocity)

    def _midi_note_off(self, note: int):
        self.audio.note_off(None, note)
