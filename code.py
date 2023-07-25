# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# You must add a gamepad HID device inside your boot.py file
# in order to use this example.
# See this Learn Guide for details:
# https://learn.adafruit.com/customizing-usb-devices-in-circuitpython/hid-devices#custom-hid-devices-3096614-9

import board
from digitalio import DigitalInOut, Pull
from analogio import AnalogIn
import usb_hid
import usb_cdc
from time import sleep
import supervisor

from adafruit_datetime import datetime
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from hid_gamepad import Gamepad

# Disable auto reload
supervisor.runtime.autoreload = False

# USB HID usage for CC Power
CC_POWER_CODE = 0x30
# Holding 'Start' button for this period will send a Power Off command
START_BUTTON_HOLD_FOR_SHUTDOWN_SECS = 3

# USB CDC Serial input
usb_cdc.data.timeout = 0
# Gamepad
gp = Gamepad(usb_hid.devices)
# Consumer Control
cc = ConsumerControl(usb_hid.devices)

# Configure the board with available analog/digital inputs

'''
All available analog inputs on the board.
Keys can be anything you like except core commands, [btn{N}, x, y, z, r_z, v, hold, pre, post]
Keys are referenced by serial command interface. 
Be sure to update default_joystick_pins below to match if you change them
'''
analog_ins: dict[str, AnalogIn] = {
    'a0'    : AnalogIn(board.A0),
    'a1'    : AnalogIn(board.A1),
    'a2'    : AnalogIn(board.A2),
    'a3'    : AnalogIn(board.A3),
}
'''
All available digital inputs on the board
Keys can be anything you like
Keys are referenced by serial command interface. 
Be sure to update default_button_pins below to match if you change them
'''
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

# The ACTIVE set of joystick inputs: gamepad axis -> AnalogIo
joystick_ais: dict[str, AnalogIn] = {}

def set_joystick_mappings(js_maps: dict[str, str]) -> None:
    '''
    Modify the ACTIVE set of joystick inputs
    '''
    global joystick_ais
    for axis, ai_key in js_maps.items():
        # Look up the AnalogIn for the key matching axis
        analog_in = analog_ins.get(ai_key)
        if None != analog_in:
            joystick_ais[axis] = analog_in

# The ACTIVE set of button inputs: button ID -> DigitalInOut
button_dios: dict[int, DigitalInOut] = {}

def set_button_mappings(but_maps: dict[int, str]) -> None:
    '''
    Modify the ACTIVE set of button inputs
    '''
    global button_dios
    for btn, di_key in but_maps.items():
        # Look up the DigitalInOut for the key matching btn
        dio = digital_ins.get(di_key)
        if None != dio:
            button_dios[btn] = dio

# Set the default joystick input mappings
set_joystick_mappings(default_joystick_pins)
# Set the default button input mappings
set_button_mappings(default_button_pins)

# Gamepad pressed buttons
pressed_buttons = set()
# Gamepad joystick axes values
gamepad_axes_values = {'x':0, 'y':0, 'z':0, 'r_z':0}

# Clear any existing pending serial data
usb_cdc.data.reset_input_buffer()

# Equivalent of Arduino's map() function.
def range_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

# Simple range clamp func
def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

def handle_button_input_command(btn:str, value:str):
    global pressed_buttons
    try:
        butIdx = int(btn)
        value = int(value)
        if value > 0:
            pressed_buttons.add(butIdx + 1)
    except Exception as e:
        print(f'Error reading button command ({btn}={value}): {e}')

def handle_joystick_axis_input_command(axis:str, value:str):
    global gamepad_axes_values
    try:
        value = int(value)
        gamepad_axes_values[axis] = value
    except Exception as e:
        print(f'Error reading joystick axes command ({axis}={value}): {e}')

def handle_button_mapping_command(digital_in:str, btn_str:str) -> None:
    global digital_ins, button_dios
    btn = 0
    try:
        btn = int(btn_str)
    except ValueError as ve:
        print(f'Error mapping button command ({digital_in}={btn_str}): {ve}')
        return
    dio = digital_ins.get(digital_in)
    if None != dio:
        button_dios[btn] = dio

def handle_joystick_mapping_command(analog_in:str, axis:str) -> None:
    global analog_ins, joystick_ais
    if axis in ['x', 'y', 'z', 'r_z']:
        ai = analog_ins.get(analog_in)
        if None != ai:
            joystick_ais[axis] = ai

def parse_int_value(value:str) -> int:
    try:
        value = int(value)
    except Exception as e:
        print(e)
        return 0
    return value

def parse_float_value(value:str) -> float:
    try:
        value = float(value)
    except Exception as e:
        print(e)
        return 0.0
    return value


def process_commands(**cmds):
    global pressed_buttons, gamepad_axes_values
    global digital_ins, analog_ins
    pressed_buttons.clear()
    pre_wait = 0.0
    post_wait = 0.5
    hold_time = 0.5
    cc_vol = 0
    for input, value in cmds.items():
        if len(input) > 3 and input[0:3] == 'btn':
            # This is a digital button input value, i.e. btn1/btn2/ ... /btn15/btn16
            handle_button_input_command(input[3:], value)
        elif input in ['x', 'y', 'z', 'r_z']:
            # This is an analog input axis value, i.e. x/y/z/r_x
            handle_joystick_axis_input_command(input, value)
        elif input in analog_ins.keys():
            handle_joystick_mapping_command(input, value)
        elif input in digital_ins.keys():
            handle_button_mapping_command(input, value)
        elif input == 'vol':
            # This is a volume value, +ve or -ve
            cc_vol = parse_int_value(value)
        elif input == 'hold':
            # Hold control(s) for a period of time
            hold_time = parse_float_value(value)
        elif input == 'pre':
            # Wait for a period of time BEFORE changing any values
            pre_wait = parse_float_value(value)
        elif input == 'post':
            # Wait for a period of time AFTER changing (and resetting) any values
            post_wait = parse_float_value(value)
    released_buttons = set(range(1,17)).difference(pressed_buttons)

    # pre-wait period
    sleep(pre_wait)
    # debug
    print(f'pressed_buttons={pressed_buttons} : released_buttons={released_buttons}')
    print(f'gamepad_axes_values={gamepad_axes_values}')
    print(f'cc_vol={cc_vol}')
    # update gamepad button values
    gp.press_buttons(*pressed_buttons)
    gp.release_buttons(*released_buttons)
    # update gamepad axes
    gp.move_joysticks(**gamepad_axes_values) 
    # update CC volume
    if cc_vol > 0:
        cc.press(ConsumerControlCode.VOLUME_INCREMENT)
    elif cc_vol < 0:
        cc.press(ConsumerControlCode.VOLUME_DECREMENT)
    # hold before releasing all buttons and centring axes
    sleep(hold_time)
    pressed_buttons.clear()
    gp.release_all_buttons()
    gamepad_axes_values = {'x':0, 'y':0, 'z':0, 'r_z':0}
    gp.move_joysticks(**gamepad_axes_values) 
    cc.release()
    # post-wait period
    sleep(post_wait)


cdc_data = bytearray()
def read_cdc_line_from_serial() -> str:
    '''
    Read data from usb_cdc.data into cdc_data until CR (0xd) or LF(0xa) are found
    Backspaces (0x8) will remove the last char read prior to a CR/LF
    '''
    global cdc_data
    cdc_str = None
    while usb_cdc.data.in_waiting > 0:
        # Read serial data into cdc_data until we hit a newline
        next_byte = usb_cdc.data.read(1)
        if len(next_byte) > 0:
            # Break on CR/LF
            if next_byte[0] == 0xd or next_byte[0] == 0xa:
                if len(cdc_data) > 0:
                    # Decode buffer
                    cdc_str = cdc_data.decode("utf-8")
                    # Reset buffer for next sequence
                    cdc_data = bytearray()
                break
            # handle backspace
            if next_byte[0] == 0x8 and len(cdc_data) > 0:
                cdc_data = cdc_data[0:-1]
                continue
            # Add byte to cdc_data buffer
            cdc_data += next_byte
    return cdc_str

def read_cmd_from_serial() -> bool:
    '''
    Attempt to read a valid command sequence from usb_cdc.data serial
    '''
    cdc_str = read_cdc_line_from_serial()
    if None == cdc_str:
        return False
    print(f'Read cmd line from usb cdc: {cdc_str}')
    # Process cdc_str
    if cdc_str == 'conf_es':
        configure_emulation_station()
        return True
    if cdc_str == 'conf_ra':
        configure_retroarch()
        return True
    # decode 'name=value' pair commands. e.g cdc_str = "b1=0;b2=1; ... ;x=32767;y=-32767;z=0;r_z="
    try:
        cmds = dict(item.split("=") for item in cdc_str.split(";"))
    except:
        return False
    if len(cmds) > 0:  
        print(f'Decoded cmds: {cmds}')
        process_commands(**cmds)
        return True
    return False

def update_gamepad_axis_from_adc():
    # Read analog inputs
    axes_values = {}
    for axis, analog_in in joystick_ais.items():
        axes_values[axis] = range_map(analog_in.value, 0, 65535, -32767, 32767)
    # Update gamepad joystick axis values
    gp.move_joysticks(**axes_values)

def update_volume_controls():
    # Read Volume controls
    volUpPressed = False
    volDownPressed = False
    # BUTTON_VOL_UP/BUTTON_VOL_DOWN might not be in button_dios so use get() instead of direct index
    volUpDIO = button_dios.get(BUTTON_VOL_UP)
    volDownDIO = button_dios.get(BUTTON_VOL_DOWN)
    if None != volUpDIO:
        volUpPressed = not volUpDIO.value
    if None != volDownDIO:
        volDownPressed = not volDownDIO.value
    # Send Consumer Control events for Volume
    if volDownPressed:
        cc.press(ConsumerControlCode.VOLUME_DECREMENT)
    elif volUpPressed:
        cc.press(ConsumerControlCode.VOLUME_INCREMENT)
    else:
        cc.release()

# 'Hold START for shutdown' feature handling
start_button_down = None
power_cmd_sent = False

def check_start_button_held_for_shutdown(pressed : bool):
    global start_button_down
    global power_cmd_sent

    if pressed:
        if None == start_button_down:
            start_button_down = datetime.now()
        else:
            start_button_held = datetime.now() - start_button_down
            if start_button_held.seconds >= START_BUTTON_HOLD_FOR_SHUTDOWN_SECS and not power_cmd_sent:
                # Initiate system shutdown
                print(f'Start button held for {start_button_held.seconds} seconds. Sending KEY_POWER code')
                cc.send(CC_POWER_CODE)
                power_cmd_sent = True
    else:
        start_button_down = None
        power_cmd_sent = False

def update_gamepad_buttons_from_digital_inputs():
    # Read buttons
    global pressed_buttons

    for btn, dio in button_dios.items():
        if btn > BUTTON_MAX:
            continue
        btn_pressed = not dio.value
        if btn_pressed:
            pressed_buttons.add(btn + 1)
        else:
            pressed_buttons.discard(btn + 1)
        if BUTTON_START == btn:
            # handle 'Hold start btn for shutdown'
            check_start_button_held_for_shutdown(btn_pressed)

    # Update gamepad button values
    released_buttons = set(range(1,17)).difference(pressed_buttons)
    gp.press_buttons(*pressed_buttons)
    gp.release_buttons(*released_buttons)

def configure_emulation_station():
    '''
    Send the necessary commands to automate EmulationStation 'Configure Input'
    '''
    cmds = [
        { f'btn{BUTTON_SELECT}'       : 1, 'hold'  : 3, 'post' : 1 },   # Initial 'hold any button'
        { f'btn{BUTTON_HAT_UP}'       : 1, 'post' : 1 },
        { f'btn{BUTTON_HAT_DOWN}'     : 1, 'post' : 1 },
        { f'btn{BUTTON_HAT_LEFT}'     : 1, 'post' : 1 },
        { f'btn{BUTTON_HAT_RIGHT}'    : 1, 'post' : 1 },
        { f'btn{BUTTON_START}'        : 1, 'post' : 1 },
        { f'btn{BUTTON_SELECT}'       : 1, 'post' : 1 },
        { f'btn{BUTTON_EAST_A}'       : 1, 'post' : 1 },
        { f'btn{BUTTON_SOUTH_B}'      : 1, 'post' : 1 },
        { f'btn{BUTTON_NORTH_X}'      : 1, 'post' : 1 },
        { f'btn{BUTTON_WEST_Y}'       : 1, 'post' : 1 },
        { f'btn{BUTTON_SHOULDER_L}'   : 1, 'post' : 1 },
        { f'btn{BUTTON_SHOULDER_R}'   : 1, 'post' : 1 },
        { f'btn{BUTTON_TRIGGER_L}'    : 1, 'post' : 1 },
        { f'btn{BUTTON_TRIGGER_R}'    : 1, 'post' : 1 },
        { f'btn{BUTTON_THUMB_L}'      : 1, 'post' : 1 },
        { f'btn{BUTTON_THUMB_R}'      : 1, 'post' : 1 },
        { 'y'                       : -32767, 'post' : 1 },
        { 'y'                       :  32767, 'post' : 1 },
        { 'x'                       : -32767, 'post' : 1 },
        { 'x'                       :  32767, 'post' : 1 },
        { 'r_z'                     : -32767, 'post' : 1 },
        { 'r_z'                     :  32767, 'post' : 1 },
        { 'z'                       : -32767, 'post' : 1 },
        { 'z'                       :  32767, 'post' : 1 },
        { f'btn{BUTTON_SELECT}'       : 1, 'post' : 1 },              # Hotkey
        { f'btn{BUTTON_EAST_A}'       : 1 },  # 'OK' / Finish
      ]
    for cmd in cmds:
        process_commands(**cmd)

def configure_retroarch():
    '''
    Send the necessary commands to automate RetroArch 'Set All Controls' configuration
    '''
    cmds = [
        { f'btn{BUTTON_SOUTH_B}'      : 1 },
        { f'btn{BUTTON_WEST_Y}'       : 1 },
        { f'btn{BUTTON_SELECT}'       : 1 },
        { f'btn{BUTTON_START}'        : 1 },
        { f'btn{BUTTON_HAT_UP}'       : 1 },
        { f'btn{BUTTON_HAT_DOWN}'     : 1 },
        { f'btn{BUTTON_HAT_LEFT}'     : 1 },
        { f'btn{BUTTON_HAT_RIGHT}'    : 1 },
        { f'btn{BUTTON_EAST_A}'       : 1 },
        { f'btn{BUTTON_NORTH_X}'      : 1 },
        { f'btn{BUTTON_SHOULDER_L}'   : 1 },
        { f'btn{BUTTON_SHOULDER_R}'   : 1 },
        { f'btn{BUTTON_TRIGGER_L}'    : 1 },
        { f'btn{BUTTON_TRIGGER_R}'    : 1 },
        { f'btn{BUTTON_THUMB_L}'      : 1 },
        { f'btn{BUTTON_THUMB_R}'      : 1 },
        { 'x'                       :  32767 },
        { 'x'                       : -32767 },
        { 'y'                       :  32767 },
        { 'y'                       : -32767 },
        { 'z'                       :  32767 },
        { 'z'                       : -32767 },
        { 'r_z'                     :  32767 },
        { 'r_z'                     : -32767 },
      ]
    for cmd in cmds:
        process_commands(**cmd)


while True:
    # First try to read simulated input values via commands from serial:
    if not read_cmd_from_serial():
        # Only read our physical inputs if no simulated input command received
        update_gamepad_axis_from_adc()
        update_gamepad_buttons_from_digital_inputs()
        update_volume_controls()
