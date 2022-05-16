import usb_hid

'''
For Reference:
Logitech F310 'Direct Input' (Dual Action) USB Input Device

0x05, 0x01,        // Usage Page (Generic Desktop Ctrls)
0x09, 0x04,        // Usage (Joystick)
0xA1, 0x01,        // Collection (Application)
0xA1, 0x02,        //   Collection (Logical)
0x75, 0x08,        //     Report Size (8)
0x95, 0x04,        //     Report Count (4)
0x15, 0x00,        //     Logical Minimum (0)
0x26, 0xFF, 0x00,  //     Logical Maximum (255)
0x35, 0x00,        //     Physical Minimum (0)
0x46, 0xFF, 0x00,  //     Physical Maximum (255)
0x09, 0x30,        //     Usage (X)
0x09, 0x31,        //     Usage (Y)
0x09, 0x32,        //     Usage (Z)
0x09, 0x35,        //     Usage (Rz)
0x81, 0x02,        //     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
0x75, 0x04,        //     Report Size (4)
0x95, 0x01,        //     Report Count (1)
0x25, 0x07,        //     Logical Maximum (7)
0x46, 0x3B, 0x01,  //     Physical Maximum (315)
0x65, 0x14,        //     Unit (System: English Rotation, Length: Centimeter)
0x09, 0x39,        //     Usage (Hat switch)
0x81, 0x42,        //     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,Null State)
0x65, 0x00,        //     Unit (None)
0x75, 0x01,        //     Report Size (1)
0x95, 0x0C,        //     Report Count (12)
0x25, 0x01,        //     Logical Maximum (1)
0x45, 0x01,        //     Physical Maximum (1)
0x05, 0x09,        //     Usage Page (Button)
0x19, 0x01,        //     Usage Minimum (0x01)
0x29, 0x0C,        //     Usage Maximum (0x0C)
0x81, 0x02,        //     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
0x06, 0x00, 0xFF,  //     Usage Page (Vendor Defined 0xFF00)
0x75, 0x01,        //     Report Size (1)
0x95, 0x10,        //     Report Count (16)
0x25, 0x01,        //     Logical Maximum (1)
0x45, 0x01,        //     Physical Maximum (1)
0x09, 0x01,        //     Usage (0x01)
0x81, 0x02,        //     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
0xC0,              //   End Collection
0xA1, 0x02,        //   Collection (Logical)
0x75, 0x08,        //     Report Size (8)
0x95, 0x07,        //     Report Count (7)
0x46, 0xFF, 0x00,  //     Physical Maximum (255)
0x26, 0xFF, 0x00,  //     Logical Maximum (255)
0x09, 0x02,        //     Usage (0x02)
0x91, 0x02,        //     Output (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position,Non-volatile)
0xC0,              //   End Collection
0xC0,              // End Collection
'''

# This is only one example of a gamepad descriptor, and may not suit your needs.
GAMEPAD_REPORT_DESCRIPTOR = bytes((
    0x05, 0x01,         # Usage Page (Generic Desktop Ctrls)
    0x09, 0x05,         # Usage (Game Pad)
    0xA1, 0x01,         # Collection (Application)
    0x85, 0x04,         #   Report ID (4)
    0x05, 0x09,         #   Usage Page (Button)
    0x19, 0x01,         #   Usage Minimum (Button 1)
    0x29, 0x10,         #   Usage Maximum (Button 16)
    0x15, 0x00,         #   Logical Minimum (0)
    0x25, 0x01,         #   Logical Maximum (1)
    0x75, 0x01,         #   Report Size (1)
    0x95, 0x10,         #   Report Count (16)
    0x81, 0x02,         #   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
    0x05, 0x01,         #   Usage Page (Generic Desktop Ctrls)
    0x16, 0x01, 0x80,   #   Logical Minimum (-32767)
    0x26, 0xff, 0x7F,   #   Logical Maximum (32767)
    0x09, 0x30,         #   Usage (X)
    0x09, 0x31,         #   Usage (Y)
    0x09, 0x32,         #   Usage (Z)
    0x09, 0x35,         #   Usage (Rz)
    0x75, 0x10,         #   Report Size (16)
    0x95, 0x04,         #   Report Count (4)
    0x81, 0x02,         #   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
    0xC0,               # End Collection
))
 
gamepad = usb_hid.Device(
    report_descriptor=GAMEPAD_REPORT_DESCRIPTOR,
    usage_page=0x01,           # Generic Desktop Control
    usage=0x05,                # Gamepad
    report_ids=(4,),           # Descriptor uses report ID 4.
    in_report_lengths=(10,),   # This gamepad sends 10 bytes in its report.
    out_report_lengths=(0,),   # It does not receive any reports.
)

usb_hid.enable(
    (
     usb_hid.Device.CONSUMER_CONTROL,
     gamepad)
)