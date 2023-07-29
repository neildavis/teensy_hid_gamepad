from config import BUTTON_VOL_UP, BUTTON_VOL_DOWN, BUTTON_VOL_MUTE
from globals import *

def report():
    # Report Gamepad buttons
    gp_pressed_buttons = gp_valid_buttons.intersection(pressed_buttons)
    gp_released_buttons = gp_valid_buttons.difference(pressed_buttons)
    gp.press_buttons(*gp_pressed_buttons)
    gp.release_buttons(*gp_released_buttons)
    # Report Gamepad joystick axes
    gp.move_joysticks(**gamepad_axes_values)
    # Report CC (Volume) events
    vol_pressed_buttons = vol_valid_buttons.intersection(pressed_buttons)
    # - for sanity sake we'll only report one volume key at a time!
    if len(vol_pressed_buttons) > 0:
        cc.press(list(vol_pressed_buttons)[0])
    else:
        cc.release()


