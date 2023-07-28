import usb_hid
import usb_midi
import usb_cdc

# We'll simulate a standard dual analog thumb-stick gamepad with 16 digital buttons
# even though we often don't need anywhere near this number of inputs
GAMEPAD_REPORT_DESCRIPTOR = bytes((
    0x05, 0x01,         # Usage Page (Generic Desktop Ctrls)
    0x09, 0x04,         # Usage (Joystick)
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
    usage=0x04,                # Joystick
    report_ids=(4,),           # Descriptor uses report ID 4.
    in_report_lengths=(10,),   # This gamepad sends 10 bytes in its report.
    out_report_lengths=(0,),   # It does not receive any reports.
)

# Disable MIDI to save on USB I/O endpoints
usb_midi.disable()
# enable the data CDC serial
usb_cdc.enable(console=True, data=True)

# Enable gamepad and consumer control (volume) HID devices
usb_hid.enable(
    ( gamepad, usb_hid.Device.CONSUMER_CONTROL )
)
