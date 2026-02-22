"""
Sequencer grid view: 4 tracks × 16 steps.

Each step is a toggle button. The playhead step is highlighted in yellow.
Left-click: toggle step on/off.
Right-click: open a small param-lock popup (note, velocity, length).
"""

import dearpygui.dearpygui as dpg
from typing import Callable

from .theme import (
    STEP_BTN_SIZE, COL_STEP_OFF, COL_STEP_ON, COL_STEP_PLAY, COL_TEXT_DIM, COL_ACCENT
)

N_TRACKS = 4
N_STEPS = 16
TRACK_LABELS = ["T1", "T2", "T3", "T4"]


def _step_color(active: bool, playhead: bool) -> tuple:
    if playhead:
        return COL_STEP_PLAY
    return COL_STEP_ON if active else COL_STEP_OFF


class SequencerView:
    def __init__(self, pattern, on_step_toggle: Callable[[int, int], None]):
        self.pattern = pattern
        self._on_step_toggle = on_step_toggle
        # Button tags: _btn_tags[track][step]
        self._btn_tags: list[list[int]] = [[] for _ in range(N_TRACKS)]
        self._playhead = -1

    def build(self, parent):
        with dpg.child_window(
            parent=parent,
            height=N_TRACKS * (STEP_BTN_SIZE + 10) + 20,
            border=False,
        ):
            for t in range(N_TRACKS):
                track_tags = []
                with dpg.group(horizontal=True):
                    # Track label
                    dpg.add_text(TRACK_LABELS[t], color=COL_ACCENT)
                    dpg.add_spacer(width=4)
                    for s in range(N_STEPS):
                        step = self.pattern.track(t).step_at(s)
                        tag = dpg.add_button(
                            label=" ",
                            width=STEP_BTN_SIZE,
                            height=STEP_BTN_SIZE,
                            callback=self._make_toggle_cb(t, s),
                        )
                        # Right-click handler
                        with dpg.item_handler_registry() as handler:
                            dpg.add_item_clicked_handler(
                                button=1,
                                callback=self._make_right_click_cb(t, s, tag),
                            )
                        dpg.bind_item_handler_registry(tag, handler)
                        track_tags.append(tag)
                        self._apply_step_style(tag, step.active, False)
                        # Group steps 4 at a time
                        if (s + 1) % 4 == 0 and s < N_STEPS - 1:
                            dpg.add_spacer(width=6)
                self._btn_tags[t] = track_tags
                dpg.add_spacer(height=4)

    def _make_toggle_cb(self, t: int, s: int):
        def cb(sender, app_data):
            self._on_step_toggle(t, s)
            step = self.pattern.track(t).step_at(s)
            self._apply_step_style(
                self._btn_tags[t][s], step.active, self._playhead == s
            )
        return cb

    def _make_right_click_cb(self, t: int, s: int, btn_tag: int):
        def cb(sender, app_data):
            self._open_step_popup(t, s)
        return cb

    def _open_step_popup(self, t: int, s: int):
        step = self.pattern.track(t).step_at(s)
        popup_tag = f"step_popup_{t}_{s}"
        if dpg.does_item_exist(popup_tag):
            dpg.delete_item(popup_tag)
        with dpg.window(
            tag=popup_tag,
            label=f"Track {t+1} Step {s+1}",
            popup=True,
            width=220,
            no_resize=True,
        ):
            dpg.add_text(f"Track {t+1}  Step {s+1}", color=COL_ACCENT)
            dpg.add_separator()
            dpg.add_slider_int(
                label="Note",
                tag=f"sp_note_{t}_{s}",
                default_value=step.note,
                min_value=0, max_value=127,
                callback=lambda sender, val: self._set_step_note(t, s, val),
            )
            dpg.add_slider_int(
                label="Velocity",
                tag=f"sp_vel_{t}_{s}",
                default_value=step.velocity,
                min_value=1, max_value=127,
                callback=lambda sender, val: self._set_step_vel(t, s, val),
            )
            dpg.add_slider_float(
                label="Length",
                tag=f"sp_len_{t}_{s}",
                default_value=step.length,
                min_value=0.05, max_value=1.0,
                format="%.2f",
                callback=lambda sender, val: self._set_step_len(t, s, val),
            )

    def _set_step_note(self, t, s, val):
        self.pattern.track(t).step_at(s).note = val

    def _set_step_vel(self, t, s, val):
        self.pattern.track(t).step_at(s).velocity = val

    def _set_step_len(self, t, s, val):
        self.pattern.track(t).step_at(s).length = val

    def update_playhead(self, step: int):
        """Highlight the current playhead step."""
        old = self._playhead
        self._playhead = step
        for t in range(N_TRACKS):
            if old >= 0 and old < N_STEPS:
                old_step = self.pattern.track(t).step_at(old)
                if old < len(self._btn_tags[t]):
                    self._apply_step_style(self._btn_tags[t][old], old_step.active, False)
            if step < len(self._btn_tags[t]):
                cur_step = self.pattern.track(t).step_at(step)
                self._apply_step_style(self._btn_tags[t][step], cur_step.active, True)

    def refresh_step(self, t: int, s: int):
        """Refresh a single step button's visual state."""
        step = self.pattern.track(t).step_at(s)
        self._apply_step_style(
            self._btn_tags[t][s], step.active, self._playhead == s
        )

    def _apply_step_style(self, tag: int, active: bool, is_playhead: bool):
        color = _step_color(active, is_playhead)
        with dpg.theme() as t:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, color)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, color)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, color)
        dpg.bind_item_theme(tag, t)
