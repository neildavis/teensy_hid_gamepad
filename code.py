from time import sleep

import board
from analogio import AnalogIn
from digitalio import DigitalInOut, Pull

import usb_hid
import usb_cdc
import busio

from adafruit_datetime import datetime
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.mouse import Mouse
from hid_gamepad import Gamepad
from as5600 import AS5600

# Constants
RAW_ANGLE_DELTA_THRESHOLD = 2   # Debounce AS5600 raw angle input
THROTTLE_DELTA_THRESHOLD = 160   # Debounce throttle pot' ADC input
START_BUTTON_HID_NUM = 10       # Start button is button number 10 on our gamepad
GEAR_BUTTON_HID_NUM = 3         # Gear button is button number 3 on our gamepad
# 'Turbo' has a tri-state digital throttle none/mid/max which we map from analog range and convert to button inputs
TURBO_THROTTLE_MID_HID_NUM = 1
TURBO_THROTTLE_MID_THRESHOLD = -10922
TURBO_THROTTLE_MAX_HID_NUM = 2
TURBO_THROTTLE_MAX_THRESHOLD = 10922
# Physically constrained range of Pot' movement from testing
THROTTLE_RANGE_RAW=range(80, 34704)
# Mapped range of throttle
THROTTLE_RANGE_MAPPED=range(-32767, 32767)
CC_POWER_CODE = 0x30    # USB HID usage for CC Power
# RP2040 & AS5600 support I2C 'fast-mode plus' with freq <= 1 MHz
AS5600_I2C_FREQUENCY = 1000000
# Holding 'Start' button for this period will send a Power Off command
START_BUTTON_HOLD_FOR_SHUTDOWN_SECS = 3

# USB CDC Serial input
usb_cdc.data.timeout = 0
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
# Start button & Gear are Digital IO - Pulled up and grounded when pressed
button_start = DigitalInOut(board.GP29)
button_start.switch_to_input(Pull.UP)
button_gear = DigitalInOut(board.GP7)
button_gear.switch_to_input(Pull.UP)

# Volume Up/Down buttons are digital IO - Pulled up and grounded when pressed
button_vol_up = DigitalInOut(board.GP1)
button_vol_down = DigitalInOut(board.GP3)
button_vol_up.switch_to_input(Pull.UP)
button_vol_down.switch_to_input(Pull.UP)

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

def read_cmd_from_serial():
    global pressed_buttons
    num_bytes_to_read =  usb_cdc.data.in_waiting
    if num_bytes_to_read > 0:
        cdc_data = usb_cdc.data.readline()
        cdc_str = cdc_data.decode("utf-8")[0:-1]
        print(f'Read {len(cdc_data)} bytes from usb_cdc.data: {cdc_str}')
        #e.g cdc_str = "B1=0;B2=1; ... ;x=32767;y=-32767;z=0;r_z="
        try:
            cmds = dict(item.split("=") for item in cdc_str.split(";"))
        except:
            return False
        if len(cmds) > 0:  
            print(f'Decoded cmds: {cmds}')
            pressed_buttons.clear()
            gamepad_axes_values = {'x':0, 'y':0, 'z':0, 'r_z':0}
            hold_time=0.5
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
                elif input == 'hold':
                    hold_time=value
            released_buttons = set(range(1,17)).difference(pressed_buttons)
            # debug
            print(f'pressed_buttons={pressed_buttons} : released_buttons={released_buttons}')
            print(f'gamepad_axes_values={gamepad_axes_values}')
            # Update gamepad button values
            gp.press_buttons(*pressed_buttons)
            gp.release_buttons(*released_buttons)
            # update gamepad axes
            if len(gamepad_axes_values) > 0:
                gp.move_joysticks(**gamepad_axes_values) 
            # hold before releasing all buttons and centring axes
            sleep(hold_time)
            pressed_buttons.clear()
            gp.release_all_buttons()
            gp.move_joysticks(0,0,0,0)
            return True
    return False

last_raw_angle = -1
def update_mouse_from_as5600():
    # Read AS5600
    global last_raw_angle
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

last_raw_throttle = 0
def update_gamepad_axis_from_adc():
    # Read analog inputs
    global last_raw_throttle
    global pressed_buttons
    throttle_val_raw = throttle.value
    if abs(throttle_val_raw - last_raw_throttle) > THROTTLE_DELTA_THRESHOLD:
        last_raw_throttle = throttle_val_raw
        throttle_val_clamped = clamp(throttle_val_raw, THROTTLE_RANGE_RAW.start, THROTTLE_RANGE_RAW.stop)
        throttle_val_mapped = range_map(throttle_val_clamped, \
            THROTTLE_RANGE_RAW.start, THROTTLE_RANGE_RAW.stop, \
            THROTTLE_RANGE_MAPPED.start, THROTTLE_RANGE_MAPPED.stop)
        #print(f'throttle: (raw, clamped, mapped): {throttle_val_raw}, {throttle_val_clamped}, {throttle_val_mapped}')
        # Update gamepad joystick axis values
        gp.move_joysticks(y = throttle_val_mapped)
        # 'Turbo' throttle is composed of two digital switches for half/full throttle. Map analog throttle range to these
        if throttle_val_mapped > TURBO_THROTTLE_MAX_THRESHOLD:
            pressed_buttons.add(TURBO_THROTTLE_MAX_HID_NUM)
            pressed_buttons.discard(TURBO_THROTTLE_MID_HID_NUM)
        elif throttle_val_mapped > TURBO_THROTTLE_MID_THRESHOLD:
            pressed_buttons.add(TURBO_THROTTLE_MID_HID_NUM)
            pressed_buttons.discard(TURBO_THROTTLE_MAX_HID_NUM)
        else:
            pressed_buttons.discard(TURBO_THROTTLE_MAX_HID_NUM)
            pressed_buttons.discard(TURBO_THROTTLE_MID_HID_NUM)
        # Update gamepad button values occurs in update_gamepad_buttons_from_digital_inputs

def update_volume_controls():
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


start_button_down = None
power_cmd_sent = False
def update_gamepad_buttons_from_digital_inputs():
    global start_button_down
    global power_cmd_sent
    # Read buttons
    global pressed_buttons
    # - Start button
    if not button_start.value:
        pressed_buttons.add(START_BUTTON_HID_NUM)
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
        pressed_buttons.discard(START_BUTTON_HID_NUM)
        start_button_down = None
        power_cmd_sent = False
    # - Gear button
    if not button_gear.value:
        pressed_buttons.add(GEAR_BUTTON_HID_NUM)
    else:
        pressed_buttons.discard(GEAR_BUTTON_HID_NUM)
    # Update gamepad button values
    released_buttons = set(range(1,17)).difference(pressed_buttons)
    gp.press_buttons(*pressed_buttons)
    gp.release_buttons(*released_buttons)


while True:
    # First try to read simulated input values via commands from serial:
    if not read_cmd_from_serial():
        # Only read our physical inputs if no simulated input command received
        update_mouse_from_as5600()
        update_gamepad_axis_from_adc()
        update_gamepad_buttons_from_digital_inputs()
        update_volume_controls()
