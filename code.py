import board
from analogio import AnalogIn
from digitalio import DigitalInOut, Pull

import usb_hid
from hid_gamepad import Gamepad

# Joystick X,Y are analog axis from joystick module
joystickX = AnalogIn(board.A3)
joystickY = AnalogIn(board.A2)
# Joystick Fire (Vulcan & Missiles) are Digital IO - Pulled up and grounded when pressed
joystickV = DigitalInOut(board.GP3)     # HID button 1
joystickM = DigitalInOut(board.GP4)     # HID button 2
joystickV.switch_to_input(Pull.UP)
joystickM.switch_to_input(Pull.UP)
# Throttle is tri-state Digital IO - Pulled up and grounded when connected
throttleL = DigitalInOut(board.GP0)
throttleH = DigitalInOut(board.GP2)
throttleL.switch_to_input(Pull.UP)
throttleH.switch_to_input(Pull.UP)
# Select/Start are Digital IO - Pulled up and grounded when pressed
buttonSelect = DigitalInOut(board.GP5)  # HID button 9
buttonStart = DigitalInOut(board.GP6)   # HID button 10
buttonSelect.switch_to_input(Pull.UP)
buttonStart.switch_to_input(Pull.UP)

# Gamepad
gp = Gamepad(usb_hid.devices)

# Equivalent of Arduino's map() function.
def range_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

while True:
    # Read analog joystick inputs
    x = range_map(joystickX.value, 0, 65535, -32767, 32767)
    y = range_map(joystickY.value, 0, 65535, -32767, 32767)
    # Read digital throttle inputs and map to an analog value
    z = 0
    if not throttleL.value:
        z = -32767
    elif not throttleH.value:
        z = 32767
    # Read buttons
    pressed_buttons = []
    # Joystick Vulcan Gun button
    if not joystickV.value:
        pressed_buttons.append(1)
    # Joystick Missile button
    if not joystickM.value:
        pressed_buttons.append(2)
    # Select button
    if not buttonSelect.value:
        pressed_buttons.append(9)
    # Start button
    if not buttonStart.value:
        pressed_buttons.append(10)
    
    released_buttons = set(range(1,17)).difference(pressed_buttons)

    # Update gamepad joystick values
    gp.move_joysticks(x = x, y = y, z = z, r_z=0)
    # Update gamepad button values
    gp.press_buttons(*pressed_buttons)
    gp.release_buttons(*released_buttons)

    print(" x: {:5d} y: {:5d} z: {:5d} bp: {} br: {}".format(x, y, z, pressed_buttons, released_buttons))