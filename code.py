# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# You must add a gamepad HID device inside your boot.py file
# in order to use this example.
# See this Learn Guide for details:
# https://learn.adafruit.com/customizing-usb-devices-in-circuitpython/hid-devices#custom-hid-devices-3096614-9

import board
import digitalio
import analogio
import usb_hid

import adafruit_matrixkeypad
from hid_gamepad import Gamepad

# Classic 4x4 matrix keypad
rows = [digitalio.DigitalInOut(x) for x in (board.D0, board.D1, board.D2, board.D3)]
cols = [digitalio.DigitalInOut(x) for x in (board.D4, board.D5, board.D6, board.D7)]
keypad_gp_nums = ((1,2,3,13),
                (4,5,6,14),
                (7,8,9,15),
                (10,11,12,16))
kp = adafruit_matrixkeypad.Matrix_Keypad(rows, cols, keypad_gp_nums)

# Gamepad
gp = Gamepad(usb_hid.devices)

# Create a button. 
button_pin = digitalio.DigitalInOut(board.D21)
button_pin.direction = digitalio.Direction.INPUT
button_pin.pull = digitalio.Pull.UP
button_gp_num = 1 # dups' one of the 4x4 keypad buttons

# Connect an analog two-axis joystick to A8 and A9.
ax = analogio.AnalogIn(board.A9)
ay = analogio.AnalogIn(board.A8)
# Connect an analog single-axis 'throttle' to A6
az = analogio.AnalogIn(board.A6)

# Equivalent of Arduino's map() function.
def range_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min


while True:
    # Keypad
    kp_pressed = kp.pressed_keys
    kp_released = set(range(1,17)).difference(kp_pressed)
    # Ignore the keypad button that dups the joystick button
    try:
        kp_pressed.remove(button_gp_num)
        kp_released.remove(button_gp_num)
    except:
        pass
    # report keypad buttons
    gp.press_buttons(*kp_pressed)
    gp.release_buttons(*kp_released)
 
    # Buttons are grounded when pressed (.value = False).
    if button_pin.value:
        gp.release_buttons(button_gp_num)
    else:
        gp.press_buttons(button_gp_num)
    # Since stick button dup's a keypad button we don't have to release it

    # Analog Stick. Convert range[0, 65535] to -127 to 127
    xm = range_map(ax.value, 0, 65535, -127, 127)
    ym = range_map(ay.value, 0, 65535, -127, 127)
    zm = range_map(az.value, 0, 65535, -127, 127)
    gp.move_joysticks(
        x=xm,
        y=ym,
        z=zm,
    )
    print(" x:", xm, "y:", ym, "z:", zm, "kpp:", kp_pressed, "kpr:", kp_released)
    
