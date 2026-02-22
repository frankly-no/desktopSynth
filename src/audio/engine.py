"""
Audio engine: sounddevice OutputStream driving the voice pool.
Runs in a dedicated audio callback thread (called by sounddevice).
"""

import numpy as np
import queue
import sounddevice as sd
from .voice_pool import VoicePool

SAMPLE_RATE = 44100
BLOCK_SIZE = 256   # ~5.8 ms latency


class AudioEngine:
    def __init__(self):
        self.voice_pool = VoicePool()
        self._stream: sd.OutputStream | None = None
        self._running = False
        # Events queued from other threads (note-on/off, param changes)
        self._event_queue: queue.Queue = queue.Queue()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        if self._running:
            return
        self._running = True
        self._stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=2,
            dtype="float32",
            blocksize=BLOCK_SIZE,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    # ------------------------------------------------------------------
    # Event API (safe to call from any thread)
    # ------------------------------------------------------------------

    def note_on(self, track_idx: int | None, note: int, velocity: int):
        self._event_queue.put_nowait(("note_on", track_idx, note, velocity))

    def note_off(self, track_idx: int | None, note: int):
        self._event_queue.put_nowait(("note_off", track_idx, note))

    def set_engine(self, track_idx: int, engine_name: str):
        self._event_queue.put_nowait(("set_engine", track_idx, engine_name))

    def set_param(self, track_idx: int, param: str, value):
        self._event_queue.put_nowait(("set_param", track_idx, param, value))

    # ------------------------------------------------------------------
    # Audio callback (runs in sounddevice's audio thread — no GIL calls)
    # ------------------------------------------------------------------

    def _callback(self, outdata: np.ndarray, frames: int, time, status):
        # Drain event queue first
        while True:
            try:
                event = self._event_queue.get_nowait()
            except queue.Empty:
                break
            self._handle_event(event)

        mono = self.voice_pool.render(frames)
        # Broadcast mono to stereo
        outdata[:, 0] = mono
        outdata[:, 1] = mono

    def _handle_event(self, event: tuple):
        kind = event[0]
        if kind == "note_on":
            _, track_idx, note, velocity = event
            self.voice_pool.note_on(track_idx, note, velocity)
        elif kind == "note_off":
            _, track_idx, note = event
            self.voice_pool.note_off(track_idx, note)
        elif kind == "set_engine":
            _, track_idx, engine_name = event
            self.voice_pool.set_track_engine(track_idx, engine_name)
        elif kind == "set_param":
            _, track_idx, param, value = event
            self.voice_pool.set_track_param(track_idx, param, value)
