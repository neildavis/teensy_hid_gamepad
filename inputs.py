from microcontroller import Pin
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_datetime import datetime

from globals import *
from config import *
from utils import range_map

# DO NOT manually manipulate these dictionaries!
# Use inputs.set_joystick_mappings() & inputs.set_button_mappings() to maintain consistency
# The ACTIVE set of joystick inputs: gamepad axis -> AnalogIo
joystick_ais: dict[str, (Pin, AnalogIn)] = {}
# The ACTIVE set of button inputs: button ID -> DigitalInOut
button_dios: dict[int, (Pin, DigitalInOut)] = {}
# The ACTIVE set of Pins in use as either buttons or joystick axes
pin_ios: dict[Pin, object] = {}  # object value will be either int (button) or str (js axis)

# USB HID usage for CC Power
CC_POWER_CODE = 0x30

def init():
    # Set the default joystick input mappings
    set_joystick_mappings(default_joystick_pins)
    # Set the default button input mappings
    set_button_mappings(default_button_pins)

def release_pin(pin: Pin):
    """
    Remove any existing mappings for a pin and release underlying AnalogIo/DigitalInOut resources
    """
    global pin_ios 
    io = pin_ios.get(pin)
    if None == io:
        return
    if isinstance(io, int):
        release_button_mapping(io)
    elif isinstance(io, str):
        release_joystick_mapping(io)
    # do NOT pin_ios.pop(pin) since it will be done by funcs called above

def release_joystick_mapping(axis: str):
    """
    Remove a joystick axis mapping and release the underlying AnalogIo for Pin reuse
    """
    global joystick_ais, pin_ios
    try:
        pin, analog_in = joystick_ais.get(axis)
        print(f'Removing existing joystick mapping: {axis}->{pin}:{analog_in}')
        joystick_ais.pop(axis)
        analog_in.deinit()
        pin_ios.pop(pin)
    except:
        pass

def release_button_mapping(btn: int):
    """
    Remove a button mapping and release the underlying DigitalInOut for Pin reuse
    """
    global button_dios, pin_ios
    try:
        pin, dio = button_dios.get(btn)
        print(f'Removing existing button mapping: {btn}->{pin}:{dio}')
        button_dios.pop(btn)
        dio.deinit()
        pin_ios.pop(pin)
    except:
        pass

def set_joystick_mappings(js_maps: dict[str, str]) -> None:
    """
    Modify the ACTIVE set of joystick inputs
    """
    global pin_ios, joystick_ais, analog_ins
    for axis, ai_key in js_maps.items():
        if not axis in ['x', 'y', 'z', 'r_z']:
            continue
        # Release any existing AnalogIn for this axis and remove the mapping
        release_joystick_mapping(axis)
        # Look up the Pin for the key matching axis
        pin = analog_ins.get(ai_key)
        if None != pin:
            # Release any existing mapping for the new pin
            release_pin(pin)
            # Create an AnalogIn
            pin_ios[pin] = axis
            analog_in = AnalogIn(pin)
            print(f'Adding joystick axis mapping: {axis}->{pin}:{analog_in}')
            joystick_ais[axis] = (pin, analog_in)

def set_button_mappings(but_maps: dict[int, str]) -> None:
    """
    Modify the ACTIVE set of button inputs
    """
    global pin_ios, button_dios, digital_ins
    for btn, di_key in but_maps.items():
        # Release any existing DigitalInOut for ths button and remove the mapping
        release_button_mapping(btn)
        # Look up the Pin for the key matching btn
        pin = digital_ins.get(di_key)
        if None != pin:
            # Release any existing mapping for the new pin
            release_pin(pin)
            # Create a DigitalInOut for the pin and map it
            pin_ios[pin] = btn
            dio = DigitalInOut(pin)
            dio.switch_to_input(Pull.UP)
            print(f'Adding button mapping: {btn}->{pin}:{dio}')
            button_dios[btn] = (pin, dio)

def update_gamepad_axis_from_adc():
    # Read analog inputs
    axes_values = {}
    for axis, (_, analog_in) in joystick_ais.items():
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
        volUpPressed = not volUpDIO[1].value
    if None != volDownDIO:
        volDownPressed = not volDownDIO[1].value
    if None != volMuteDIO:
        volMutePressed = not volMuteDIO[1].value
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

    for btn, (_, dio) in button_dios.items():
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

