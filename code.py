import board
from analogio import AnalogIn
from digitalio import DigitalInOut, Pull

import usb_hid
import busio

from hid_gamepad import Gamepad
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.mouse import Mouse
from as5600 import AS5600

# Constants
RAW_ANGLE_DELTA_THRESHOLD = 2 # Debounce AS5600 raw angle input
START_BUTTON_HID_NUM = 10 # Start button is button number 10 on our gamepad
# RP2040 & AS5600 support I2C 'fast-mode plus' with freq <= 1 MHz
AS5600_I2C_FREQUENCY = 1000000

# Mouse
mouse = Mouse(usb_hid.devices)
# Gamepad
gp = Gamepad(usb_hid.devices)
# Consumer Control
cc = ConsumerControl(usb_hid.devices)

# Setup AS5600
i2c = busio.I2C(scl=board.GP27, sda=board.GP26, frequency=AS5600_I2C_FREQUENCY)
z = AS5600(i2c, 0x36)
if z.scan():
    print(f'AS5600 found: {z.magnet_status()}')
else:
    print('AS5600 NOT found')

# X-axis is Throttle from potentiometer on ADC2
throttle = AnalogIn(board.A2)
# Start button is Digital IO - Pulled up and grounded when pressed
button_start = DigitalInOut(board.GP29)
button_start.switch_to_input(Pull.UP)

# Volume Up/Down buttons are digital IO - Pulled up and grounded when pressed
button_vol_up = DigitalInOut(board.GP1)
button_vol_down = DigitalInOut(board.GP2)
button_vol_up.switch_to_input(Pull.UP)
button_vol_down.switch_to_input(Pull.UP)

# Equivalent of Arduino's map() function.
def range_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

last_raw_angle = -1
while True:
    # Read AS5600
    new_raw_angle = z.RAWANGLE
    if last_raw_angle < 0:
        last_raw_angle = new_raw_angle
    angle_diff = new_raw_angle - last_raw_angle
    # Correct the zero crossover glitch. If abs(angle_diff) is > 3/4 of range in a single reading,
    # then assume we have crossed zero position.
    if angle_diff < -0xc00:
        angle_diff += 0xfff
    elif angle_diff > 0xc00:
        angle_diff -= 0xfff
    if abs(angle_diff) > RAW_ANGLE_DELTA_THRESHOLD:
        # Move the mouse
        mouse.move(x=angle_diff)
        last_raw_angle = new_raw_angle

    # Read analog inputs
    throttle_val = range_map(throttle.value, 0, 65535, -32767, 32767)
    # Read buttons
    pressed_buttons = []
    # Start button
    if not button_start.value:
        pressed_buttons.append(START_BUTTON_HID_NUM)
    released_buttons = set(range(1,17)).difference(pressed_buttons)
    # Update gamepad joystick axis values
    gp.move_joysticks(x = throttle_val)
    # Update gamepad button values
    gp.press_buttons(*pressed_buttons)
    gp.release_buttons(*released_buttons)

    # Read Volume controls
    volUpPressed = not button_vol_up.value
    volDownPressed = not button_vol_down.value
    # Send Consumer Control events for Volume
    if volDownPressed:
       cc.press(ConsumerControlCode.VOLUME_DECREMENT)
    elif volUpPressed:
        cc.press(ConsumerControlCode.VOLUME_INCREMENT)
    else:
        cc.release()

   