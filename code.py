# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# You must add a gamepad HID device inside your boot.py file
# in order to use this example.
# See this Learn Guide for details:
# https://learn.adafruit.com/customizing-usb-devices-in-circuitpython/hid-devices#custom-hid-devices-3096614-9

import board
from digitalio import DigitalInOut, Pull
import analogio
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

# Analog axes for joysticks:
analog_ins = {
    'x'     : analogio.AnalogIn(board.A0),
    'y'     : analogio.AnalogIn(board.A1),
    'z'     : analogio.AnalogIn(board.A2),
    'r_z'   : analogio.AnalogIn(board.A3),
}

# Enumerate all our digital io inputs as HID button IDs (1-16)
BUTTON_WEST_Y       = 1
BUTTON_SOUTH_B      = 2
BUTTON_EAST_A       = 3
BUTTON_NORTH_X      = 4
BUTTON_SHOULDER_L   = 5
BUTTON_SHOULDER_R   = 6
BUTTON_TRIGGER_L    = 7
BUTTON_TRIGGER_R    = 8
BUTTON_SELECT       = 9
BUTTON_START        = 10
BUTTON_THUMB_L      = 11
BUTTON_THUMB_R      = 12
BUTTON_HAT_UP       = 13
BUTTON_HAT_DOWN     = 14
BUTTON_HAT_LEFT     = 15
BUTTON_HAT_RIGHT    = 16
# TODO: Add a further digital io buttons with unique HID button ids in range 1-16 if required
BUTTON_MAX          = BUTTON_HAT_RIGHT

# CC Volume handled by buttons outside gamepad button range
BUTTON_VOL_UP       = 20
BUTTON_VOL_DOWN     = 21

# All of our buttons are digital IO - Pulled up and grounded when pressed. Map to GPIO pins here:
button_pins = {
    BUTTON_VOL_UP   : board.GP0,
    BUTTON_VOL_DOWN : board.GP1,
    BUTTON_START    : board.GP2,
    BUTTON_SELECT   : board.GP3,
    BUTTON_SOUTH_B  : board.GP4,
    BUTTON_WEST_Y   : board.GP5,
    BUTTON_EAST_A   : board.GP6,
    BUTTON_NORTH_X  : board.GP7,
}

# populate map of DigitalInOut that we poll
button_dios = {}
for btn, pin in button_pins.items():
    dio = DigitalInOut(pin)
    dio.switch_to_input(Pull.UP)
    button_dios[btn] = dio

# Gamepad pressed buttons
pressed_buttons = set()

# Clear any existing pending serial data
num_bytes_to_read =  usb_cdc.data.in_waiting
if num_bytes_to_read > 0:
    usb_cdc.data.read(num_bytes_to_read)

# Equivalent of Arduino's map() function.
def range_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

# Simple range clamp func
def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

def process_commands(**cmds):
    global pressed_buttons
    pressed_buttons.clear()
    gamepad_axes_values = {'x':0, 'y':0, 'z':0, 'r_z':0}
    pre_wait = 0.0
    post_wait = 0.0
    hold_time = 0.5
    cc_vol = 0
    for input, value in cmds.items():
        try:
            value = int(value)
        except:
            continue
        if input[0] == 'b':
            # This is a digital button input value, i.e. b1/b2/ ... /b15/b16
            if int(value) > 0:
                pressed_buttons.add(int(input[1:]))
        elif input in ['x', 'y', 'z', 'r_z']:
            # This is an analog input axis value, i.e. x/y/z/r_x
            gamepad_axes_values[input] = value
        elif input == 'v':
            # This is a volume value, +ve or -ve
            cc_vol = value
        elif input == 'hold':
            # Hold control(s) for a period of time
            hold_time = value
        elif input == 'pre':
            # Hold control(s) for a period of time
            pre_wait = value
        elif input == 'post':
            # Hold control(s) for a period of time
            post_wait = value
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
    gp.move_joysticks(0,0,0,0)
    cc.release()
    # post-wait period
    sleep(post_wait)
    

def read_cmd_from_serial():
    num_bytes_to_read =  usb_cdc.data.in_waiting
    if num_bytes_to_read > 0:
        cdc_data = usb_cdc.data.readline()
        cdc_str = cdc_data.decode("utf-8")[0:-1]
        print(f'Read {len(cdc_data)} bytes from usb_cdc.data: {cdc_str}')
        if cdc_str == 'conf_es':
            configure_emulation_station()
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
    for axis, analog_in in analog_ins.items():
        axes_values[axis] = range_map(analog_in.value, 0, 65535, -32767, 32767)
    # Update gamepad joystick axis values
    gp.move_joysticks(**axes_values)

def update_volume_controls():
    # Read Volume controls
    volUpPressed = not button_dios[BUTTON_VOL_UP].value
    volDownPressed = not button_dios[BUTTON_VOL_DOWN].value
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
            pressed_buttons.add(btn)
        else:
            pressed_buttons.discard(btn)
        if BUTTON_START == btn:
            # handle 'Hold start btn for shutdown'
            check_start_button_held_for_shutdown(btn_pressed)

    # Update gamepad button values
    released_buttons = set(range(1,17)).difference(pressed_buttons)
    gp.press_buttons(*pressed_buttons)
    gp.release_buttons(*released_buttons)

def configure_emulation_station():
    '''
    Send the necessary commands to automate an Input Configuration in EmulationStation
    '''
    cmds = [
        { f'b{BUTTON_SELECT}'       :1, 'hold'  : 3, 'post' : 1 },   # Initial 'hold any button'
        { f'b{BUTTON_HAT_UP}'       : 1, 'post' : 1 },
        { f'b{BUTTON_HAT_DOWN}'     : 1, 'post' : 1 },
        { f'b{BUTTON_HAT_LEFT}'     : 1, 'post' : 1 },
        { f'b{BUTTON_HAT_RIGHT}'    : 1, 'post' : 1 },
        { f'b{BUTTON_START}'        : 1, 'post' : 1 },
        { f'b{BUTTON_SELECT}'       : 1, 'post' : 1 },
        { f'b{BUTTON_EAST_A}'       : 1, 'post' : 1 },
        { f'b{BUTTON_SOUTH_B}'      : 1, 'post' : 1 },
        { f'b{BUTTON_NORTH_X}'      : 1, 'post' : 1 },
        { f'b{BUTTON_WEST_Y}'       : 1, 'post' : 1 },
        { f'b{BUTTON_SHOULDER_L}'   : 1, 'post' : 1 },
        { f'b{BUTTON_SHOULDER_R}'   : 1, 'post' : 1 },
        { f'b{BUTTON_TRIGGER_L}'    : 1, 'post' : 1 },
        { f'b{BUTTON_TRIGGER_R}'    : 1, 'post' : 1 },
        { f'b{BUTTON_THUMB_L}'      : 1, 'post' : 1 },
        { f'b{BUTTON_THUMB_R}'      : 1, 'post' : 1 },
        { 'y'                       : -32767, 'post' : 1 },
        { 'y'                       : 32767, 'post' : 1 },
        { 'x'                       : -32767, 'post' : 1 },
        { 'x'                       : 32767, 'post' : 1 },
        { 'r_z'                     : -32767, 'post' : 1 },
        { 'r_z'                     : 32767, 'post' : 1 },
        { 'z'                       : -32767, 'post' : 1 },
        { 'z'                       : 32767, 'post' : 1 },
        { f'b{BUTTON_SELECT}'       : 1, 'post' : 1 },              # Hotkey
        { f'b{BUTTON_EAST_A}'       : 1 },  # 'OK' / Finish
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
