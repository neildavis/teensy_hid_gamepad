from analogio import AnalogIn
from digitalio import DigitalInOut
from microcontroller import Pin
import usb_hid

from adafruit_hid.consumer_control import ConsumerControl

from hid_gamepad import Gamepad

# Gamepad pressed buttons
pressed_buttons = set()
# Gamepad joystick axes values
gamepad_axes_values = {'x':0, 'y':0, 'z':0, 'r_z':0}

# Gamepad
gp = Gamepad(usb_hid.devices)
# Consumer Control
cc = ConsumerControl(usb_hid.devices)
