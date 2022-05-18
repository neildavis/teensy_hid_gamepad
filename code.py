import board
from analogio import AnalogIn
from digitalio import DigitalInOut, Pull

import usb_hid
from hid_gamepad import Gamepad
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Joystick X,Y are analog axis from joystick module
joystickX = AnalogIn(board.A3)
joystickY = AnalogIn(board.A2)
# Joystick Fire (Vulcan & Missiles) are Digital IO - Pulled up and grounded when pressed
joystickV = DigitalInOut(board.GP2)     # HID button 1
joystickM = DigitalInOut(board.GP3)     # HID button 2
joystickV.switch_to_input(Pull.UP)
joystickM.switch_to_input(Pull.UP)
# Throttle is tri-state Digital IO - Pulled up and grounded when connected
throttleL = DigitalInOut(board.GP0)
throttleH = DigitalInOut(board.GP1)
throttleL.switch_to_input(Pull.UP)
throttleH.switch_to_input(Pull.UP)
# Select/Start are Digital IO - Pulled up and grounded when pressed
buttonSelect = DigitalInOut(board.GP4)  # HID button 9
buttonStart = DigitalInOut(board.GP5)   # HID button 10
buttonSelect.switch_to_input(Pull.UP)
buttonStart.switch_to_input(Pull.UP)
# Volume Up/Down are digital IO - Pulled up and grounded when pressed
buttonVolUp = DigitalInOut(board.GP6)
buttonVolDown = DigitalInOut(board.GP7)
buttonVolUp.switch_to_input(Pull.UP)
buttonVolDown.switch_to_input(Pull.UP)

# Gamepad
gp = Gamepad(usb_hid.devices)
# Consumer Control
cc = ConsumerControl(usb_hid.devices)

# Equivalent of Arduino's map() function.
def range_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

while True:
    # Read analog joystick inputs
    x = range_map(joystickX.value, 0, 65535, -32767, 32767)
    y = range_map(joystickY.value, 0, 65535, -32767, 32767)
    # Read digital throttle inputs and map to an analog value
    t = 0
    if not throttleL.value:
        t = -32767
    elif not throttleH.value:
        t = 32767
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
    gp.move_joysticks(x = x, y = y, z = t, r_z=0)
    # Update gamepad button values
    gp.press_buttons(*pressed_buttons)
    gp.release_buttons(*released_buttons)

    # Volume controls
    volUpPressed = not buttonVolUp.value
    volDownPressed = not buttonVolDown.value
    vol = "--"
    if volDownPressed:
       cc.press(ConsumerControlCode.VOLUME_DECREMENT)
       vol = "DOWN"
    elif volUpPressed:
        cc.press(ConsumerControlCode.VOLUME_INCREMENT)
        vol = "UP"
    else:
        cc.release()

    print(" x: {:6d} y: {:6d} t: {:6d} bp: {} vol: {}".format(x, y, t, pressed_buttons, vol))
