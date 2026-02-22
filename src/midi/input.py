"""MIDI input: listens on an rtmidi port and routes events to the audio engine."""

import threading
from typing import Callable

try:
    import rtmidi
    RTMIDI_AVAILABLE = True
except ImportError:
    RTMIDI_AVAILABLE = False


class MidiInput:
    def __init__(self):
        self._midi_in = None
        self._port_name: str | None = None
        # Callbacks: (note, velocity) or (note,) for off
        self._note_on_cb: Callable[[int, int], None] | None = None
        self._note_off_cb: Callable[[int], None] | None = None
        self._cc_cb: Callable[[int, int], None] | None = None

    def set_callbacks(
        self,
        note_on: Callable[[int, int], None],
        note_off: Callable[[int], None],
        cc: Callable[[int, int], None] | None = None,
    ):
        self._note_on_cb = note_on
        self._note_off_cb = note_off
        self._cc_cb = cc

    def list_ports(self) -> list[str]:
        if not RTMIDI_AVAILABLE:
            return []
        midi_in = rtmidi.MidiIn()
        return list(midi_in.get_ports())

    def open_port(self, port_index: int = 0):
        if not RTMIDI_AVAILABLE:
            return
        self._midi_in = rtmidi.MidiIn()
        ports = self._midi_in.get_ports()
        if not ports:
            return
        self._midi_in.open_port(port_index % len(ports))
        self._port_name = ports[port_index % len(ports)]
        self._midi_in.set_callback(self._on_message)
        self._midi_in.ignore_types(sysex=True, timing=True, active_sense=True)

    def close(self):
        if self._midi_in:
            self._midi_in.close_port()
            self._midi_in = None

    def _on_message(self, message, data=None):
        msg, _ = message
        if not msg:
            return
        status = msg[0] & 0xF0
        if status == 0x90 and len(msg) >= 3:  # Note On
            note, velocity = msg[1], msg[2]
            if velocity == 0:
                if self._note_off_cb:
                    self._note_off_cb(note)
            else:
                if self._note_on_cb:
                    self._note_on_cb(note, velocity)
        elif status == 0x80 and len(msg) >= 3:  # Note Off
            note = msg[1]
            if self._note_off_cb:
                self._note_off_cb(note)
        elif status == 0xB0 and len(msg) >= 3:  # CC
            cc_num, cc_val = msg[1], msg[2]
            if self._cc_cb:
                self._cc_cb(cc_num, cc_val)
