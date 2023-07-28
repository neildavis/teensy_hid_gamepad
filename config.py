import board
from digitalio import DigitalInOut, Pull
from analogio import AnalogIn

"""
Holding 'Start' button for this period will send a Power Off command
"""
START_BUTTON_HOLD_FOR_SHUTDOWN_SECS = 3

# Configure the board with available analog/digital inputs:

"""
All available analog inputs on the board.
Keys can be anything you like except core commands, [btn{N}, x, y, z, r_z, v, hold, pre, post]
Keys are referenced by serial command interface. 
Be sure to update default_joystick_pins below to match if you change them
"""
analog_ins: dict[str, AnalogIn] = {
    'a0'    : AnalogIn(board.A0),
    'a1'    : AnalogIn(board.A1),
    'a2'    : AnalogIn(board.A2),
    'a3'    : AnalogIn(board.A3),
}

"""
All available digital inputs on the board
Keys can be anything you like
Keys are referenced by serial command interface. 
Be sure to update default_button_pins below to match if you change them
"""
digital_ins: dict[str, DigitalInOut] = {
    'd0'    : DigitalInOut(board.GP0),
    'd1'    : DigitalInOut(board.GP1),
    'd2'    : DigitalInOut(board.GP2),
    'd3'    : DigitalInOut(board.GP3),
    'd4'    : DigitalInOut(board.GP4),
    'd5'    : DigitalInOut(board.GP5),
    'd6'    : DigitalInOut(board.GP6),
    'd7'    : DigitalInOut(board.GP7),
}
for dio in digital_ins.values():
    dio.switch_to_input(Pull.UP)
    
# Enumerate all our digital io inputs as HID button IDs (0-15)
BUTTON_WEST_Y       = 0
BUTTON_SOUTH_B      = 1
BUTTON_EAST_A       = 2
BUTTON_NORTH_X      = 3
BUTTON_SHOULDER_L   = 4
BUTTON_SHOULDER_R   = 5
BUTTON_TRIGGER_L    = 6
BUTTON_TRIGGER_R    = 7
BUTTON_SELECT       = 8
BUTTON_START        = 9
BUTTON_THUMB_L      = 10
BUTTON_THUMB_R      = 11
BUTTON_HAT_UP       = 12
BUTTON_HAT_DOWN     = 13
BUTTON_HAT_LEFT     = 14
BUTTON_HAT_RIGHT    = 15
BUTTON_MAX          = BUTTON_HAT_RIGHT
# CC Volume handled by buttons outside gamepad button range
BUTTON_VOL_UP       = 20
BUTTON_VOL_DOWN     = 21
BUTTON_VOL_MUTE     = 22

# These are the default mappings of buttons to digital inputs
default_button_pins: dict[int, str] = {
    BUTTON_VOL_UP   : 'd0',
    BUTTON_VOL_DOWN : 'd1',
    BUTTON_START    : 'd2',
    BUTTON_SELECT   : 'd3',
    BUTTON_SOUTH_B  : 'd4',
    BUTTON_WEST_Y   : 'd5',
    BUTTON_EAST_A   : 'd6',
    BUTTON_NORTH_X  : 'd7',
}
# These are the default mappings of analog axes for joysticks:
default_joystick_pins: dict[str, str] = {
    'x'     : 'a0',
    'y'     : 'a1',
    'z'     : 'a2',
    'r_z'   : 'a3',
}
