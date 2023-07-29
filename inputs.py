from analogio import AnalogIn
from digitalio import DigitalInOut, Pull
from microcontroller import Pin
from rotaryio import IncrementalEncoder

from adafruit_datetime import datetime

from globals import *
from config import *
from utils import range_map

# DO NOT manually manipulate these dictionaries!
# Use inputs.set_joystick_mappings() & inputs.set_button_mappings() to maintain consistency
# The ACTIVE set of joystick inputs: gamepad axis -> (Pin, AnalogIo)
joystick_ais: dict[str, (Pin, AnalogIn)] = {}
# The ACTIVE set of button inputs: button ID -> (Pin, DigitalInOut)
button_dios: dict[int, (Pin, DigitalInOut)] = {}
# The ACTIVE set of rotary encoder inputs: (btn_dec, but_inc) -> (Pin, Pin, IncrementalEncoder)
rotary_encoders: dict[(int, int), (Pin, Pin, IncrementalEncoder)] = {}
# The ACTIVE set of rotary encoder last readings: inputs: (btn_dec, but_inc) -> (Pin, Pin, IncrementalEncoder)
rotary_encoder_values: dict[IncrementalEncoder, int] = {}
# The ACTIVE set of Pins in use. object value will be either:
# - int (button)
# - str (js axis)
# - tuple (rotary encoder)
pin_ios: dict[Pin, object] = {}  

def init():
    # Set the default joystick input mappings
    set_joystick_mappings(default_joystick_pins)
    # Set the default button input mappings
    set_button_mappings(default_button_pins)
    # Set the default rotary encoder mappings
    set_rotary_encoder_mappings(default_rotary_encoder_pins)

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
        # Could be either, but safe to call
        release_joystick_mapping(io)
        release_rotary_encoder_mapping(io)
    # do NOT pin_ios.pop(pin) since it will be done by funcs called above

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
            print(f'Adding joystick axis mapping: {axis}->({pin}, {analog_in})')
            joystick_ais[axis] = (pin, analog_in)

def release_joystick_mapping(axis: str):
    """
    Remove a joystick axis mapping and release the underlying AnalogIo for Pin reuse
    """
    global joystick_ais, pin_ios
    try:
        pin, analog_in = joystick_ais.get(axis)
        print(f'Removing existing joystick mapping: {axis}->({pin}, {analog_in})')
        joystick_ais.pop(axis)
        analog_in.deinit()
        pin_ios.pop(pin)
    except:
        pass

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
            print(f'Adding button mapping: {btn}->({pin}, {dio})')
            button_dios[btn] = (pin, dio)

def release_button_mapping(btn: int):
    """
    Remove a button mapping and release the underlying DigitalInOut for Pin reuse
    """
    global button_dios, pin_ios
    try:
        pin, dio = button_dios.get(btn)
        print(f'Removing existing button mapping: {btn}->({pin}, {dio})')
        button_dios.pop(btn)
        dio.deinit()
        pin_ios.pop(pin)
    except:
        pass

def set_rotary_encoder_mappings(rot_enc_maps: dict[str: (str, str, int, int)]):
    """
    Add a rotary encoder on digital inputs, and configure the increment and
    decrement actions of the encoder to button actions.

    Note: Any existing actions for the requested buttons will be removed
    and all DigitalInOuts already in use will be deinit() 
    Also, any other button mappings on the CLK/DT DIOs will be removed
    before being passed to rotaryio.IncrementalEncoder which will re-initialize them.

    Rotary encoder support is not (yet) supported via the serial interface.    
    """

    global rotary_encoders, pin_ios
    for rot_enc_id, (dio_clk, dio_dt, btn_dec, btn_inc) in rot_enc_maps.items():
        # Release any existing rotary encoder mapped to these buttons
        release_rotary_encoder_mapping(rot_enc_id)
        # Lookup the requested pins
        pin_clk = digital_ins.get(dio_clk)
        pin_dt= digital_ins.get(dio_dt)
        if None == pin_clk or None == pin_dt:
            print(f'Insufficient pins to add IncrementalEncoder on {dio_clk}={pin_clk}, {dio_dt}={pin_dt}. Check digital_ins mappings')
            return
        # Release any button mappings and DigitalInOut resources using the requested pins
        release_pin(pin_clk)
        release_pin(pin_dt)
        # Add the rotary encoder
        encoder = IncrementalEncoder(pin_clk, pin_dt)
        print(f'Adding rotary encoder mapping: {rot_enc_id}->({pin_clk}, {pin_dt}, {btn_dec}, {btn_inc}, {encoder})')
        rotary_encoders[rot_enc_id] = (pin_clk, pin_dt, btn_dec, btn_inc, encoder)
        rotary_encoder_values[rot_enc_id] = encoder.position
        pin_ios[pin_clk] = rot_enc_id
        pin_ios[pin_dt] = rot_enc_id

def release_rotary_encoder_mapping(rot_enc_id:str):
    """
    Remove a button mapping and release the underlying DigitalInOut for Pin reuse
    """
    global rotary_encoders, pin_ios
    try:
        pin_clk, pin_dt, but_dec, but_inc, encoder = rotary_encoders.get(rot_enc_id)
        print(f'Removing existing rotary encoder mapping: {rot_enc_id}->({pin_clk}, {pin_dt}, {but_dec}, {but_inc}, {encoder})')
        rotary_encoders.pop(rot_enc_id)
        rotary_encoder_values.pop(rot_enc_id)
        encoder.deinit()
        pin_ios.pop(pin_clk)
        pin_ios.pop(pin_dt)
    except:
        pass


def update_gamepad_axis_from_adc():
    # Read analog inputs
    for axis, (_, analog_in) in joystick_ais.items():
        gamepad_axes_values[axis] = range_map(analog_in.value, 0, 65535, -32767, 32767)

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

def update_buttons_from_digital_inputs():
    # Read buttons
    global pressed_buttons

    for btn, (_, dio) in button_dios.items():
        btn_pressed = not dio.value
        if btn_pressed:
            pressed_buttons.add(btn)
        else:
            pressed_buttons.discard(btn)
        if BUTTON_START == btn:
            # handle 'Hold start btn for shutdown'
            check_start_button_held_for_shutdown(btn_pressed)

def update_rotary_encoders():
    global pressed_buttons
    for rot_enc_id, (_, _, btn_dec, btn_inc, encoder) in rotary_encoders.items():
        pressed_buttons.discard(btn_dec)
        pressed_buttons.discard(btn_inc)
        current_val = encoder.position
        last_val = rotary_encoder_values[rot_enc_id]
        diff = current_val - last_val
        if diff < 0:
            # press decrement button
            pressed_buttons.add(btn_dec)
        elif diff > 0:
            # press increment button
            pressed_buttons.add(btn_inc)
        rotary_encoder_values[rot_enc_id] = current_val

def update_all():
    update_gamepad_axis_from_adc()
    update_buttons_from_digital_inputs()
    update_rotary_encoders()
   