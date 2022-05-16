# teensy_hid_gamepad

A USB HID Gamepad using CircuitPython.
Originally developed for a Teensy 4.0 MCU but should work on any MCU with a working CircuitPython port including USB HID support.

## Tiny2040 After Burner Version

This branch contains the code used on a Tiny2040 to implement a gamepad for playing After Burner on MAME.

Inputs include:

* Analog joystick 1 with dual axis (x, y) to control the aircraft movement. 16-bit resolution (-32767 - 32767)
* Analog Joystick 2 with single axis (z) to control the aircraft throttle. 16-bit resolution (-32767 - 32767)
* 16 digital buttons with 4 in use for Vulcan Gun, Missile, Select & Start. The others are reported as unpressed.
* Consumer Control Volume UP & DOWN

Analog joystick 1 reads analog values from ADC pins A3 (x) & A2 (y)

The throttle input on joystick 2 is synthesized from digital inputs as described in the table below. If neither 'High' or 'Low' inputs are triggered the value will be 'Medium' (0)

All digital inputs are pulled high, and 'pressed' in the USB HID report when pulled low.

| Pin | Control |
|-|-|
| GP0 | Throttle Low (analog value -32676) |
| GP1 | Throttle High (analog value 32767) |
| GP2 | Vulcan Gun Trigger |
| GP3 | Missile Button |
| GP4 | Select Button |
| GP5 | Start Button |
| GP6 | Volume Up |
| GP7 | Volume Down |
