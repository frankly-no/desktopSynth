"""
Main application window built with Dear PyGui.
Composes transport, sequencer grid, and voice panels.
"""

import dearpygui.dearpygui as dpg
from typing import Callable

from .theme import apply_theme
from .transport import TransportPanel
from .sequencer_view import SequencerView
from .voice_panel import VoicePanel
from src.sequencer.pattern import Pattern

N_TRACKS = 4


class MainWindow:
    def __init__(
        self,
        pattern: Pattern,
        on_play: Callable,
        on_stop: Callable,
        on_bpm_change: Callable[[float], None],
        on_swing_change: Callable[[float], None],
        on_step_toggle: Callable[[int, int], None],
        on_engine_change: Callable[[int, str], None],
        on_param_change: Callable[[int, str, object], None],
    ):
        self.pattern = pattern
        self._seq_view: SequencerView | None = None

        self._transport = TransportPanel(
            on_play=on_play,
            on_stop=on_stop,
            on_bpm_change=on_bpm_change,
            on_swing_change=on_swing_change,
        )
        self._seq_view = SequencerView(
            pattern=pattern,
            on_step_toggle=on_step_toggle,
        )
        self._voice_panels = [
            VoicePanel(
                track_idx=i,
                engine_name=pattern.track(i).engine_name,
                on_engine_change=on_engine_change,
                on_param_change=on_param_change,
            )
            for i in range(N_TRACKS)
        ]

    def setup(self):
        dpg.create_context()
        apply_theme()

        with dpg.font_registry():
            pass  # Use default font

        with dpg.window(tag="main_window", label="desktopSynth"):
            # Header
            with dpg.group(horizontal=True):
                dpg.add_text("desktopSynth", color=(0, 180, 160, 255))
                dpg.add_text("  multivoice synthesizer + sequencer",
                             color=(100, 100, 120, 255))
            dpg.add_separator()

            self._transport.build(parent="main_window")
            dpg.add_separator()

            # Sequencer grid
            dpg.add_text("SEQUENCER", color=(100, 100, 120, 255))
            self._seq_view.build(parent="main_window")
            dpg.add_separator()

            # Voice panels in a horizontal row
            dpg.add_text("VOICES", color=(100, 100, 120, 255))
            with dpg.group(horizontal=True) as voice_row:
                for vp in self._voice_panels:
                    vp.build(parent=voice_row)

        dpg.create_viewport(
            title="desktopSynth",
            width=920,
            height=720,
            min_width=900,
            min_height=600,
        )
        dpg.setup_dearpygui()
        dpg.set_primary_window("main_window", True)
        dpg.show_viewport()

    def update_playhead(self, step: int):
        """Called from sequencer clock (must be thread-safe — DPG is main-thread only)."""
        if self._seq_view:
            self._seq_view.update_playhead(step)

    def run_frame(self):
        """Render one frame. Call in the main loop."""
        dpg.render_dearpygui_frame()

    def is_running(self) -> bool:
        return dpg.is_dearpygui_running()

    def teardown(self):
        dpg.destroy_context()
