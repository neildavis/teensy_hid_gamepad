import usb_hid

from adafruit_hid.consumer_control import ConsumerControl

from hid_gamepad import Gamepad
from config import BUTTON_VOL_UP, BUTTON_VOL_DOWN, BUTTON_VOL_MUTE

# Gamepad & Volume pressed buttons
pressed_buttons = set()
gp_valid_buttons = set(range(0,16))
vol_valid_buttons = set((BUTTON_VOL_UP, BUTTON_VOL_DOWN, BUTTON_VOL_MUTE))
# Gamepad joystick axes values
gamepad_axes_values = {'x':0, 'y':0, 'z':0, 'r_z':0}

# Gamepad
gp = Gamepad(usb_hid.devices)
# Consumer Control
cc = ConsumerControl(usb_hid.devices)
