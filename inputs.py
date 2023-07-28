from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_datetime import datetime

from globals import *
from config import *
from utils import range_map

# USB HID usage for CC Power
CC_POWER_CODE = 0x30

def init():
    # Set the default joystick input mappings
    set_joystick_mappings(default_joystick_pins)
    # Set the default button input mappings
    set_button_mappings(default_button_pins)

def set_joystick_mappings(js_maps: dict[str, str]) -> None:
    """
    Modify the ACTIVE set of joystick inputs
    """
    global joystick_ais, analog_ins
    for axis, ai_key in js_maps.items():
        # Look up the AnalogIn for the key matching axis
        analog_in = analog_ins.get(ai_key)
        if None != analog_in:
            joystick_ais[axis] = analog_in

def set_button_mappings(but_maps: dict[int, str]) -> None:
    """
    Modify the ACTIVE set of button inputs
    """
    global button_dios, digital_ins
    for btn, di_key in but_maps.items():
        # Look up the DigitalInOut for the key matching btn
        dio = digital_ins.get(di_key)
        if None != dio:
            button_dios[btn] = dio

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
    volMutePressed = False
    # BUTTON_VOL_UP/BUTTON_VOL_DOWN might not be in button_dios so use get() instead of direct index
    volUpDIO = button_dios.get(BUTTON_VOL_UP)
    volDownDIO = button_dios.get(BUTTON_VOL_DOWN)
    volMuteDIO = button_dios.get(BUTTON_VOL_MUTE)
    if None != volUpDIO:
        volUpPressed = not volUpDIO.value
    if None != volDownDIO:
        volDownPressed = not volDownDIO.value
    if None != volMuteDIO:
        volMutePressed = not volMuteDIO.value
    # Send Consumer Control events for Volume
    if volDownPressed:
        cc.press(ConsumerControlCode.VOLUME_DECREMENT)
    elif volUpPressed:
        cc.press(ConsumerControlCode.VOLUME_INCREMENT)
    elif volMutePressed:
        cc.press(ConsumerControlCode.MUTE)
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

