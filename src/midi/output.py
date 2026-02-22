"""MIDI output: sends note events to an rtmidi port."""

try:
    import rtmidi
    RTMIDI_AVAILABLE = True
except ImportError:
    RTMIDI_AVAILABLE = False


class MidiOutput:
    def __init__(self):
        self._midi_out = None
        self._port_name: str | None = None

    def list_ports(self) -> list[str]:
        if not RTMIDI_AVAILABLE:
            return []
        midi_out = rtmidi.MidiOut()
        return list(midi_out.get_ports())

    def open_port(self, port_index: int = 0):
        if not RTMIDI_AVAILABLE:
            return
        self._midi_out = rtmidi.MidiOut()
        ports = self._midi_out.get_ports()
        if not ports:
            # Open a virtual port if no hardware found
            self._midi_out.open_virtual_port("desktopSynth Out")
            self._port_name = "desktopSynth Out (virtual)"
            return
        self._midi_out.open_port(port_index % len(ports))
        self._port_name = ports[port_index % len(ports)]

    def close(self):
        if self._midi_out:
            self._midi_out.close_port()
            self._midi_out = None

    def note_on(self, channel: int, note: int, velocity: int):
        if not self._midi_out:
            return
        self._midi_out.send_message([0x90 | (channel & 0x0F), note & 0x7F, velocity & 0x7F])

    def note_off(self, channel: int, note: int):
        if not self._midi_out:
            return
        self._midi_out.send_message([0x80 | (channel & 0x0F), note & 0x7F, 0])

    def send_cc(self, channel: int, cc: int, value: int):
        if not self._midi_out:
            return
        self._midi_out.send_message([0xB0 | (channel & 0x0F), cc & 0x7F, value & 0x7F])
