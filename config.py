import board
from microcontroller import Pin
from adafruit_hid.consumer_control_code import ConsumerControlCode

# USB HID usage for CC Power
CC_POWER_CODE = 0x30

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
analog_ins: dict[str,  Pin ] = {
    'a1'    : board.A1,
    'a2'    : board.A2,
    'a3'    : board.A3,
}

"""
All available digital inputs on the board
Keys can be anything you like
Keys are referenced by serial command interface. 
Be sure to update default_button_pins below to match if you change them
"""
digital_ins: dict[str, Pin] = {
    'd0'    : board.GP0,
    'd1'    : board.GP1,
    'd2'    : board.GP2,
    'd3'    : board.GP3,
    'd4'    : board.GP4,
    'd5'    : board.GP5,
    'd6'    : board.GP6,
    'd7'    : board.GP7,
    'd26'   : board.GP26,
}
    
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
# CC Volume handled by buttons outside gamepad button range
BUTTON_VOL_UP       = ConsumerControlCode.VOLUME_INCREMENT
BUTTON_VOL_DOWN     = ConsumerControlCode.VOLUME_DECREMENT
BUTTON_VOL_MUTE     = ConsumerControlCode.MUTE
BUTTON_POWER        = CC_POWER_CODE

# These are the default mappings of buttons to digital inputs
default_button_pins: dict[int, str] = {
    BUTTON_NORTH_X  : 'd26',
    BUTTON_SELECT   : 'd5',
    BUTTON_START    : 'd6',
    BUTTON_WEST_Y   : 'd7',
    BUTTON_VOL_MUTE : 'd2',
}

# These are the default mappings of analog axes for joysticks:
default_joystick_pins: dict[str, str] = {
    'x'     : 'a2',
    'y'     : 'a1',
    'z'     : 'a3',
}

# These are the default rotary-encoder mappings:
default_rotary_encoder_pins: dict[str: (str, str, int, int)] = {
    'rot_vol': ('d0', 'd1', BUTTON_VOL_DOWN, BUTTON_VOL_UP),
}