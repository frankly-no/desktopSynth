"""
Per-voice parameter panels — one panel per track.
Shows engine-selector combo + engine-specific parameter knobs/sliders.
"""

import dearpygui.dearpygui as dpg
from typing import Callable

from src.audio.engines import ENGINE_NAMES
from src.audio.engines.fm import N_ALGORITHMS
from src.audio.oscillator import WAVE_NAMES
from .theme import COL_ACCENT, COL_TEXT_DIM

N_TRACKS = 4
TRACK_COLORS = [
    (0, 180, 160, 255),   # teal
    (180, 80, 200, 255),  # purple
    (220, 130, 0, 255),   # orange
    (60, 160, 230, 255),  # blue
]


class VoicePanel:
    """Panel for one voice/track."""

    def __init__(
        self,
        track_idx: int,
        engine_name: str,
        on_engine_change: Callable[[int, str], None],
        on_param_change: Callable[[int, str, object], None],
    ):
        self.track_idx = track_idx
        self.engine_name = engine_name
        self._on_engine_change = on_engine_change
        self._on_param_change = on_param_change
        self._param_group_tag: int | None = None
        self._panel_tag: int | None = None

    def build(self, parent):
        color = TRACK_COLORS[self.track_idx % len(TRACK_COLORS)]
        with dpg.child_window(
            parent=parent,
            width=200,
            height=380,
            border=True,
        ) as self._panel_tag:
            dpg.add_text(f"VOICE {self.track_idx + 1}", color=color)
            dpg.add_separator()
            dpg.add_combo(
                items=ENGINE_NAMES,
                default_value=self.engine_name,
                width=-1,
                callback=self._engine_changed,
                tag=f"engine_combo_{self.track_idx}",
            )
            dpg.add_separator()
            # Param group (rebuilt when engine changes)
            with dpg.group(tag=f"params_{self.track_idx}") as self._param_group_tag:
                self._build_engine_params()

    def _engine_changed(self, sender, value):
        self.engine_name = value
        self._on_engine_change(self.track_idx, value)
        # Rebuild params
        dpg.delete_item(f"params_{self.track_idx}", children_only=True)
        self._build_engine_params()

    def _build_engine_params(self):
        parent = f"params_{self.track_idx}"
        t = self.track_idx
        if self.engine_name == "fm":
            self._build_fm_params(parent, t)
        elif self.engine_name == "vector":
            self._build_vector_params(parent, t)
        elif self.engine_name == "subtractive":
            self._build_sub_params(parent, t)

    # ------------------------------------------------------------------
    def _p(self, parent, label, tag, default, mn, mx, fmt="%.2f", is_int=False):
        """Helper: add a slider param."""
        if is_int:
            dpg.add_slider_int(
                label=label, tag=tag, parent=parent,
                default_value=int(default), min_value=int(mn), max_value=int(mx),
                width=-1,
                callback=lambda s, v: self._on_param_change(self.track_idx, tag.split("__")[1], v),
            )
        else:
            dpg.add_slider_float(
                label=label, tag=tag, parent=parent,
                default_value=float(default), min_value=float(mn), max_value=float(mx),
                format=fmt, width=-1,
                callback=lambda s, v: self._on_param_change(self.track_idx, tag.split("__")[1], v),
            )

    def _ptag(self, param: str) -> str:
        return f"t{self.track_idx}__{param}"

    # ------------------------------------------------------------------
    def _build_fm_params(self, parent, t):
        dpg.add_text("FM Engine", parent=parent, color=COL_ACCENT)
        dpg.add_slider_int(
            label="Algorithm", tag=self._ptag("algorithm"), parent=parent,
            default_value=0, min_value=0, max_value=N_ALGORITHMS - 1, width=-1,
            callback=lambda s, v: self._on_param_change(t, "algorithm", v),
        )
        dpg.add_separator(parent=parent)
        for i in range(4):
            dpg.add_text(f"  Op {i}", parent=parent, color=COL_TEXT_DIM)
            self._p(parent, "Ratio", self._ptag(f"op{i}_ratio"), 1.0, 0.01, 16.0)
            self._p(parent, "Level", self._ptag(f"op{i}_level"), 0.7, 0.0, 1.0)
            if i == 0:
                self._p(parent, "Feedback", self._ptag(f"op{i}_feedback"), 0.0, 0.0, 1.0)
            self._p(parent, "A", self._ptag(f"op{i}_attack"), 0.005, 0.001, 4.0)
            self._p(parent, "D", self._ptag(f"op{i}_decay"), 0.2, 0.001, 4.0)
            self._p(parent, "S", self._ptag(f"op{i}_sustain"), 0.5, 0.0, 1.0)
            self._p(parent, "R", self._ptag(f"op{i}_release"), 0.4, 0.001, 4.0)

    def _build_vector_params(self, parent, t):
        dpg.add_text("Vector Engine", parent=parent, color=COL_ACCENT)
        for name, label in [("osc_a", "Osc A"), ("osc_b", "Osc B"),
                             ("osc_c", "Osc C"), ("osc_d", "Osc D")]:
            dpg.add_combo(
                items=WAVE_NAMES, default_value=WAVE_NAMES[0],
                label=label, tag=self._ptag(name), parent=parent, width=-1,
                callback=lambda s, v, n=name: self._on_param_change(
                    t, n, WAVE_NAMES.index(v)
                ),
            )
        dpg.add_separator(parent=parent)
        self._p(parent, "X", self._ptag("xy_x"), 0.5, 0.0, 1.0)
        self._p(parent, "Y", self._ptag("xy_y"), 0.5, 0.0, 1.0)
        self._p(parent, "LFO Rate", self._ptag("lfo_rate"), 0.5, 0.01, 20.0)
        self._p(parent, "LFO Depth", self._ptag("lfo_depth"), 0.0, 0.0, 1.0)
        dpg.add_separator(parent=parent)
        self._p(parent, "Cutoff", self._ptag("filter_cutoff"), 4000.0, 20.0, 20000.0, "%.0f")
        self._p(parent, "Resonance", self._ptag("filter_res"), 0.2, 0.0, 0.99)
        dpg.add_separator(parent=parent)
        dpg.add_text("ADSR", parent=parent, color=COL_TEXT_DIM)
        self._p(parent, "A", self._ptag("attack"), 0.01, 0.001, 4.0)
        self._p(parent, "D", self._ptag("decay"), 0.2, 0.001, 4.0)
        self._p(parent, "S", self._ptag("sustain"), 0.6, 0.0, 1.0)
        self._p(parent, "R", self._ptag("release"), 0.5, 0.001, 4.0)

    def _build_sub_params(self, parent, t):
        dpg.add_text("Subtractive Engine", parent=parent, color=COL_ACCENT)
        for name, label in [("osc1_wave", "Osc 1"), ("osc2_wave", "Osc 2")]:
            dpg.add_combo(
                items=WAVE_NAMES, default_value=WAVE_NAMES[0],
                label=label, tag=self._ptag(name), parent=parent, width=-1,
                callback=lambda s, v, n=name: self._on_param_change(
                    t, n, WAVE_NAMES.index(v)
                ),
            )
        self._p(parent, "Mix", self._ptag("osc_mix"), 0.5, 0.0, 1.0)
        self._p(parent, "Detune", self._ptag("detune"), 0.0, -24.0, 24.0)
        self._p(parent, "Octave", self._ptag("octave"), 0, -2, 2, is_int=True)
        dpg.add_separator(parent=parent)
        dpg.add_text("Filter", parent=parent, color=COL_TEXT_DIM)
        self._p(parent, "Cutoff", self._ptag("filter_cutoff"), 2000.0, 20.0, 20000.0, "%.0f")
        self._p(parent, "Res", self._ptag("filter_res"), 0.3, 0.0, 0.99)
        self._p(parent, "Env Amt", self._ptag("filter_env_amt"), 0.5, 0.0, 1.0)
        dpg.add_separator(parent=parent)
        dpg.add_text("Amp ADSR", parent=parent, color=COL_TEXT_DIM)
        self._p(parent, "A", self._ptag("amp_attack"), 0.005, 0.001, 4.0)
        self._p(parent, "D", self._ptag("amp_decay"), 0.15, 0.001, 4.0)
        self._p(parent, "S", self._ptag("amp_sustain"), 0.7, 0.0, 1.0)
        self._p(parent, "R", self._ptag("amp_release"), 0.3, 0.001, 4.0)
        dpg.add_separator(parent=parent)
        dpg.add_text("Arpeggiator", parent=parent, color=COL_TEXT_DIM)
        from src.audio.engines.subtractive import ARP_MODES
        dpg.add_combo(
            items=ARP_MODES, default_value="off",
            label="Mode", tag=self._ptag("arp_mode_combo"), parent=parent, width=-1,
            callback=lambda s, v: self._on_param_change(t, "arp_mode", ARP_MODES.index(v)),
        )
        self._p(parent, "Oct", self._ptag("arp_octaves"), 1, 1, 4, is_int=True)
