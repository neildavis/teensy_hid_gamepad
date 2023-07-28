from analogio import AnalogIn
from digitalio import DigitalInOut
import usb_hid

from adafruit_hid.consumer_control import ConsumerControl

from hid_gamepad import Gamepad


# DO NOT manually manipulate these dictionaries!
# Use inputs.set_joystick_mappings() & inputs.set_button_mappings() to maintain consistency
# The ACTIVE set of joystick inputs: gamepad axis -> AnalogIo
joystick_ais: dict[str, AnalogIn] = {}
# The ACTIVE set of button inputs: button ID -> DigitalInOut
button_dios: dict[int, DigitalInOut] = {}

# Gamepad pressed buttons
pressed_buttons = set()
# Gamepad joystick axes values
gamepad_axes_values = {'x':0, 'y':0, 'z':0, 'r_z':0}

# Gamepad
gp = Gamepad(usb_hid.devices)
# Consumer Control
cc = ConsumerControl(usb_hid.devices)
