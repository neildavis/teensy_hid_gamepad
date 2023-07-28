# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# You must add a gamepad HID device inside your boot.py file
# in order to use this example.
# See this Learn Guide for details:
# https://learn.adafruit.com/customizing-usb-devices-in-circuitpython/hid-devices#custom-hid-devices-3096614-9

import supervisor

# Client configuration/APIs are in the config.py module
import inputs
import serial

# Do initial setup
inputs.init()
serial.init()

# Disable auto reload
supervisor.runtime.autoreload = False

while True:
    # First try to read simulated input values via commands from serial:
    if not serial.read_cmd_from_serial():
        # Only read our physical inputs if no simulated input command received
        inputs.update_gamepad_axis_from_adc()
        inputs.update_gamepad_buttons_from_digital_inputs()
        inputs.update_volume_controls()
