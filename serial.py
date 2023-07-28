import usb_cdc

import commands

def init():
    # USB CDC Serial input
    usb_cdc.data.timeout = 0
    # Clear any existing pending serial data
    usb_cdc.data.reset_input_buffer()

cdc_data = bytearray()
def read_cdc_line_from_serial() -> str:
    """
    Read data from usb_cdc.data into cdc_data until CR (0xd) or LF(0xa) are found
    Backspaces (0x8) will remove the last char read prior to a CR/LF
    """
    global cdc_data
    cdc_str = None
    while usb_cdc.data.in_waiting > 0:
        # Read serial data into cdc_data until we hit a newline
        next_byte = usb_cdc.data.read(1)
        if len(next_byte) > 0:
            # Break on CR/LF
            if next_byte[0] == 0xd or next_byte[0] == 0xa:
                if len(cdc_data) > 0:
                    # Decode buffer
                    cdc_str = cdc_data.decode("utf-8")
                    # Reset buffer for next sequence
                    cdc_data = bytearray()
                break
            # handle backspace
            if next_byte[0] == 0x8 and len(cdc_data) > 0:
                cdc_data = cdc_data[0:-1]
                continue
            # Add byte to cdc_data buffer
            cdc_data += next_byte
    return cdc_str

def read_cmd_from_serial() -> bool:
    """
    Attempt to read a valid command sequence from usb_cdc.data serial
    """
    cdc_str = read_cdc_line_from_serial()
    if None == cdc_str:
        return False
    print(f'Read cmd line from usb cdc: {cdc_str}')
    # Process cdc_str
    if cdc_str == 'conf_es':
        commands.configure_emulation_station()
        return True
    if cdc_str == 'conf_ra':
        commands.configure_retroarch()
        return True
    # decode 'name=value' pair commands. e.g cdc_str = "b1=0;b2=1; ... ;x=32767;y=-32767;z=0;r_z="
    try:
        cmds = dict(item.split("=") for item in cdc_str.split(";"))
    except:
        return False
    if len(cmds) > 0:  
        print(f'Decoded cmds: {cmds}')
        commands.process_commands(**cmds)
        return True
    return False

