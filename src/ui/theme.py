"""
Dark hardware-inspired theme for Dear PyGui.
Color palette inspired by Elektron Digitone: dark grey chassis, teal accents.
"""

import dearpygui.dearpygui as dpg


# Color palette (R, G, B, A)
COL_BG = (18, 18, 22, 255)          # Window background
COL_PANEL = (26, 26, 32, 255)        # Panel/child bg
COL_STEP_OFF = (40, 40, 50, 255)     # Inactive step
COL_STEP_ON = (0, 180, 160, 255)     # Active step (teal)
COL_STEP_PLAY = (255, 200, 50, 255)  # Playhead
COL_ACCENT = (0, 180, 160, 255)      # Teal accent
COL_TEXT = (210, 210, 220, 255)      # Primary text
COL_TEXT_DIM = (100, 100, 120, 255)  # Secondary text
COL_KNOB_BG = (35, 35, 45, 255)
COL_KNOB_ACTIVE = (0, 160, 140, 255)
COL_BUTTON = (50, 50, 65, 255)
COL_BUTTON_ACTIVE = (0, 160, 140, 255)
COL_BUTTON_HOVER = (60, 60, 80, 255)
COL_BORDER = (55, 55, 70, 255)

# Sizes
STEP_BTN_SIZE = 38
STEP_BTN_SPACING = 4
PANEL_PADDING = 10
KNOB_SIZE = 55


def apply_theme():
    """Call once after dpg.create_context() to apply the global theme."""
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, COL_BG)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, COL_PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, COL_PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_Text, COL_TEXT)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, COL_TEXT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_Border, COL_BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, COL_KNOB_BG)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, COL_KNOB_ACTIVE)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, COL_BUTTON_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_Button, COL_BUTTON)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, COL_BUTTON_ACTIVE)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, COL_BUTTON_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, COL_ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, COL_KNOB_ACTIVE)
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, COL_ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_Header, COL_BUTTON)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, COL_BUTTON_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, COL_BUTTON_ACTIVE)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, COL_PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, COL_BG)
            dpg.add_theme_color(dpg.mvThemeCol_Tab, COL_BUTTON)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, COL_BUTTON_ACTIVE)
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, COL_BUTTON_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, COL_BG)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, COL_BUTTON)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 6, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, PANEL_PADDING, PANEL_PADDING)

    dpg.bind_theme(global_theme)


def make_step_button_theme(active: bool, is_playhead: bool = False) -> int:
    """Return a theme tag for a step button in the given state."""
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvButton):
            if is_playhead:
                color = COL_STEP_PLAY
            elif active:
                color = COL_STEP_ON
            else:
                color = COL_STEP_OFF
            dpg.add_theme_color(dpg.mvThemeCol_Button, color)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, color)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, color)
    return t
