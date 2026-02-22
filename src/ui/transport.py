"""Transport controls: Play, Stop, BPM, Swing."""

import dearpygui.dearpygui as dpg
from typing import Callable


class TransportPanel:
    def __init__(
        self,
        on_play: Callable,
        on_stop: Callable,
        on_bpm_change: Callable[[float], None],
        on_swing_change: Callable[[float], None],
    ):
        self._on_play = on_play
        self._on_stop = on_stop
        self._on_bpm_change = on_bpm_change
        self._on_swing_change = on_swing_change

    def build(self, parent):
        with dpg.group(horizontal=True, parent=parent):
            dpg.add_button(label="  PLAY  ", callback=self._on_play, height=32, width=90)
            dpg.add_button(label="  STOP  ", callback=self._on_stop, height=32, width=90)
            dpg.add_spacer(width=20)
            dpg.add_text("BPM")
            dpg.add_slider_float(
                tag="transport_bpm",
                default_value=120.0,
                min_value=40.0,
                max_value=240.0,
                width=120,
                callback=lambda s, a: self._on_bpm_change(a),
            )
            dpg.add_spacer(width=20)
            dpg.add_text("Swing")
            dpg.add_slider_float(
                tag="transport_swing",
                default_value=0.0,
                min_value=0.0,
                max_value=1.0,
                width=100,
                format="%.2f",
                callback=lambda s, a: self._on_swing_change(a),
            )
