from time import sleep

from globals import *
from config import *
import inputs
from report import report

def handle_button_input_command(btn:str, value:str):
    global pressed_buttons
    try:
        butIdx = int(btn)
        value = int(value)
        if value >= 0:
            pressed_buttons.add(butIdx)
    except Exception as e:
        print(f'Error reading button command ({btn}={value}): {e}')

def handle_joystick_axis_input_command(axis:str, value:str):
    global gamepad_axes_values
    try:
        value = int(value)
        gamepad_axes_values[axis] = value
    except Exception as e:
        print(f'Error reading joystick axes command ({axis}={value}): {e}')

def handle_volume_input_command(value: str):
    if 'mute' == value:
        pressed_buttons.add(BUTTON_VOL_MUTE)
    else:
        try:
            vol = int(value)
            if vol < 0:
                pressed_buttons.add(BUTTON_VOL_DOWN)
            elif vol > 0:
                pressed_buttons.add(BUTTON_VOL_UP)
        except ValueError as e:
            print(f'Error reading volume command (vol={value}): {e}')
        
def handle_button_mapping_command(digital_in:str, btn_str:str) -> None:
    try:
        inputs.set_button_mappings({int(btn_str): digital_in})
    except ValueError as ve:
        print(f'Error mapping button command ({digital_in}={btn_str}): {ve}')
    
def handle_joystick_mapping_command(analog_in:str, axis:str) -> None:
    inputs.set_joystick_mappings({axis: analog_in})

def parse_int_value(value:str) -> int:
    try:
        value = int(value)
    except Exception as e:
        print(e)
        return 0
    return value

def parse_float_value(value:str) -> float:
    try:
        value = float(value)
    except Exception as e:
        print(e)
        return 0.0
    return value

def reset_gamepad_axes_values():
    global gamepad_axes_values
    gamepad_axes_values.update({ 'x':0, 'y':0, 'z':0, 'r_z':0 })

def process_commands(**cmds):
    global pressed_buttons, gamepad_axes_values
    global digital_ins, analog_ins
    pressed_buttons.clear()
    reset_gamepad_axes_values()
    pre_wait = 0.0
    post_wait = 0.5
    hold_time = 0.5
    for input, value in cmds.items():
        if len(input) > 3 and input[0:3] == 'btn':
            # This is a digital button input value, i.e. btn1/btn2/ ... /btn15/btn16
            handle_button_input_command(input[3:], value)
        elif input in ['x', 'y', 'z', 'r_z']:
            # This is an analog input axis value, i.e. x/y/z/r_x
            handle_joystick_axis_input_command(input, value)
        elif input in analog_ins.keys():
            # This is an analog input->joystick axis remap
            handle_joystick_mapping_command(input, value)
        elif input in digital_ins.keys():
            # This is a digital input->button remap
            handle_button_mapping_command(input, value)
        elif input == 'vol':
            # This is a volume value, +ve, -ve or 'mute'
            handle_volume_input_command(value)
        elif input == 'hold':
            # Hold control(s) for a period of time
            hold_time = parse_float_value(value)
        elif input == 'pre':
            # Wait for a period of time BEFORE changing any values
            pre_wait = parse_float_value(value)
        elif input == 'post':
            # Wait for a period of time AFTER changing (and resetting) any values
            post_wait = parse_float_value(value)

    # pre-wait period
    sleep(pre_wait)
    # debug
    print(f'pressed_buttons={pressed_buttons}')
    print(f'gamepad_axes_values={gamepad_axes_values}')
    report()
    # hold before releasing all buttons and centring axes
    sleep(hold_time)
    pressed_buttons.clear()
    reset_gamepad_axes_values()
    report()
    # post-wait period
    sleep(post_wait)

def configure_emulation_station():
    """
    Send the necessary commands to automate EmulationStation 'Configure Input'
    """
    cmds = [
        { f'btn{BUTTON_SELECT}'       : 1, 'hold'  : 3, 'post' : 1 },   # Initial 'hold any button'
        { f'btn{BUTTON_HAT_UP}'       : 1, 'post' : 1 },
        { f'btn{BUTTON_HAT_DOWN}'     : 1, 'post' : 1 },
        { f'btn{BUTTON_HAT_LEFT}'     : 1, 'post' : 1 },
        { f'btn{BUTTON_HAT_RIGHT}'    : 1, 'post' : 1 },
        { f'btn{BUTTON_START}'        : 1, 'post' : 1 },
        { f'btn{BUTTON_SELECT}'       : 1, 'post' : 1 },
        { f'btn{BUTTON_EAST_A}'       : 1, 'post' : 1 },
        { f'btn{BUTTON_SOUTH_B}'      : 1, 'post' : 1 },
        { f'btn{BUTTON_NORTH_X}'      : 1, 'post' : 1 },
        { f'btn{BUTTON_WEST_Y}'       : 1, 'post' : 1 },
        { f'btn{BUTTON_SHOULDER_L}'   : 1, 'post' : 1 },
        { f'btn{BUTTON_SHOULDER_R}'   : 1, 'post' : 1 },
        { f'btn{BUTTON_TRIGGER_L}'    : 1, 'post' : 1 },
        { f'btn{BUTTON_TRIGGER_R}'    : 1, 'post' : 1 },
        { f'btn{BUTTON_THUMB_L}'      : 1, 'post' : 1 },
        { f'btn{BUTTON_THUMB_R}'      : 1, 'post' : 1 },
        { 'y'                       : -32767, 'post' : 1 },
        { 'y'                       :  32767, 'post' : 1 },
        { 'x'                       : -32767, 'post' : 1 },
        { 'x'                       :  32767, 'post' : 1 },
        { 'r_z'                     : -32767, 'post' : 1 },
        { 'r_z'                     :  32767, 'post' : 1 },
        { 'z'                       : -32767, 'post' : 1 },
        { 'z'                       :  32767, 'post' : 1 },
        { f'btn{BUTTON_SELECT}'       : 1, 'post' : 1 },              # Hotkey
        { f'btn{BUTTON_EAST_A}'       : 1 },  # 'OK' / Finish
      ]
    for cmd in cmds:
        process_commands(**cmd)

def configure_retroarch():
    """
    Send the necessary commands to automate RetroArch 'Set All Controls' configuration
    """
    cmds = [
        { f'btn{BUTTON_SOUTH_B}'      : 1 },
        { f'btn{BUTTON_WEST_Y}'       : 1 },
        { f'btn{BUTTON_SELECT}'       : 1 },
        { f'btn{BUTTON_START}'        : 1 },
        { f'btn{BUTTON_HAT_UP}'       : 1 },
        { f'btn{BUTTON_HAT_DOWN}'     : 1 },
        { f'btn{BUTTON_HAT_LEFT}'     : 1 },
        { f'btn{BUTTON_HAT_RIGHT}'    : 1 },
        { f'btn{BUTTON_EAST_A}'       : 1 },
        { f'btn{BUTTON_NORTH_X}'      : 1 },
        { f'btn{BUTTON_SHOULDER_L}'   : 1 },
        { f'btn{BUTTON_SHOULDER_R}'   : 1 },
        { f'btn{BUTTON_TRIGGER_L}'    : 1 },
        { f'btn{BUTTON_TRIGGER_R}'    : 1 },
        { f'btn{BUTTON_THUMB_L}'      : 1 },
        { f'btn{BUTTON_THUMB_R}'      : 1 },
        { 'x'                       :  32767 },
        { 'x'                       : -32767 },
        { 'y'                       :  32767 },
        { 'y'                       : -32767 },
        { 'z'                       :  32767 },
        { 'z'                       : -32767 },
        { 'r_z'                     :  32767 },
        { 'r_z'                     : -32767 },
      ]
    for cmd in cmds:
        process_commands(**cmd)

