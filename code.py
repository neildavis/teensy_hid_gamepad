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
cols = [digitalio.DigitalInOut(x) for x in (board.D0, board.D1, board.D2, board.D3)]
rows = [digitalio.DigitalInOut(x) for x in (board.D4, board.D5, board.D6, board.D7)]
keypad_gp_nums = ((1,2,3,13),
                (4,5,6,14),
                (7,8,9,15),
                (10,11,12,16))
kp = adafruit_matrixkeypad.Matrix_Keypad(rows, cols, keypad_gp_nums)

# Gamepad
gp = Gamepad(usb_hid.devices)

# Create a button. 
button_pin = digitalio.DigitalInOut(board.D8)
button_pin.direction = digitalio.Direction.INPUT
button_pin.pull = digitalio.Pull.UP
button_gp_num = 17

# Connect an analog two-axis joystick to A4 and A5.
ax = analogio.AnalogIn(board.A4)
ay = analogio.AnalogIn(board.A5)

# Equivalent of Arduino's map() function.
def range_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min


while True:
    # Keypad
    kp_pressed = kp.pressed_keys
    kp_released = set(list(range(1,button_gp_num))).difference(kp_pressed)
    gp.press_buttons(*kp_pressed)
    gp.release_buttons(*kp_released)
 
    # Buttons are grounded when pressed (.value = False).
    # if button_pin.value:
    #     gp.release_buttons(button_gp_num)
    # else:
    #     gp.press_buttons(button_gp_num)

    # Analog Stick. Convert range[0, 65535] to -127 to 127
    gp.move_joysticks(
        x=range_map(ax.value, 0, 65535, -127, 127),
        y=range_map(ay.value, 0, 65535, -127, 127),
    )
    print(" x", ax.value, "y", ay.value)
    
