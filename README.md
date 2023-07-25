# teensy_hid_gamepad

## Overview

A ___programmable___ USB HID Gamepad using
[CircuitPython](https://circuitpython.org/)
with the following features:

* Up to 16 [digital inputs](#digital-inputs) (GPIO) can be attached and mapped to USB HID Gamepad buttons.
* Up to 4 [analog inputs](#analog-inputs)
(16-bit ADC) can be attached and mapped to two USB HID Gamepad joystick axes.
* [USB _Consumer Control_](#usb-consumer-control)
support for volume up/down and power off.
* [Programmable](#programmable-serial-interface)
HID responses via USB CDC Serial comms using the same port as USB HID.
* [Programmable](#programmable-serial-interface)
dynamic re-mapping of digital inputs to buttons and analog inputs to joystick axis
* Single command [automated configuration](#special-configuration-commands) for
[EmulationStation](https://github.com/Aloshi/EmulationStation) and
[RetroArch](https://www.retroarch.com/) as used in e.g.
[RetroPie](https://retropie.org.uk/).
* Open and hackable.

## Target Hardware

This project was originally developed for a
[Teensy 4.0](https://www.pjrc.com/store/teensy40.html)
MCU (hence the name), but is now targeted at
[RP2040](https://www.raspberrypi.com/documentation/microcontrollers/rp2040.html)
development boards like
[Pimoroni Tiny2040](https://shop.pimoroni.com/products/tiny-2040?variant=39560012234835).

It should work on any MCU with enough ADC & GPIO inputs and a working CircuitPython port including USB HID & CDC serial support. Some minor changes for board I/O pins etc. may be required.

## Installation

1. Ensure you have
[CircuitPython installed](https://learn.adafruit.com/welcome-to-circuitpython/installing-circuitpython)
for your MCU board.
2. Install the required
[libraries](https://learn.adafruit.com/welcome-to-circuitpython/circuitpython-libraries)
from the [latest Adafruit CircuitPython Bundle](https://circuitpython.org/libraries):

    * `adafruit_hid`
    * `adafruit_datetime`
3. Copy all of the `*.py` files in the root of this repository to the root of your `CIRCUITPY` drive/volume.

## Modifying Code

If you need to modify any of the code, note that in [`code.py`](./code.py) the default 'auto-reload on save' functionality has been disabled by this line:

```python
# Disable auto reload
supervisor.runtime.autoreload = False
```

To reload after saving, use the
[CircuitPython serial console](https://learn.adafruit.com/welcome-to-circuitpython/kattni-connecting-to-the-serial-console) and press
`CTRL+C` to interrupt the running program, and then `CTRL+D` to reload. Or just delete/comment out the line above.

## Physical Inputs

Both analog & digital components can be used as inputs for the gamepad:

### Analog Inputs

By default, two gamepad analog joysticks (with two axes each) are enabled on four ADC inputs (`A0`-`A3`) as found on the
[Pimoroni Tiny2040](https://shop.pimoroni.com/products/tiny-2040?variant=39560012234835) board.
These can be changed and/or removed in these sections of code in [`code.py`](./code.py):

```python
# These are the default mappings of analog axes for joysticks:
default_joystick_pins = {
    'x'     : 'a0',
    'y'     : 'a1',
    'z'     : 'a2',
    'r_z'   : 'a3',
}
```

The '`x`' & '`y`' axes correspond to the _left_ analog joystick, whilst '`z`' & '`r_z`' correspond to the _right_ analog joystick. The values are keys into the available analog axes defined in `analog_ins`.
You are free to modify these but just be sure they match up in both dictionaries:

```python
analog_ins = {
    'a0'    : analogio.AnalogIn(board.A0),
    'a1'    : analogio.AnalogIn(board.A1),
    'a2'    : analogio.AnalogIn(board.A2),
    'a3'    : analogio.AnalogIn(board.A3),
}
```

Remove unwanted entries and/or map to alternative inputs on your board as required.

### Digital Inputs

Up to 16 buttons and 2 volume controls can be mapped to GPIO inputs on the board.

By default, since the
[Pimoroni Tiny2040](https://shop.pimoroni.com/products/tiny-2040?variant=39560012234835)
board has only 8 GPIO left (excluding the pins used as ADC for the analog joysticks)
only 6 gamepad buttons and 2 volume control buttons are mapped.
These can be changed and/or removed in these sections of code in [`code.py`](./code.py):

```python
# These are the default mappings of buttons to digital inputs
default_button_pins = {
    BUTTON_VOL_UP   : 'd0',
    BUTTON_VOL_DOWN : 'd1',
    BUTTON_START    : 'd2',
    BUTTON_SELECT   : 'd3',
    BUTTON_SOUTH_B  : 'd4',
    BUTTON_WEST_Y   : 'd5',
    BUTTON_EAST_A   : 'd6',
    BUTTON_NORTH_X  : 'd7',
}
```

The keys identify the gamepad button action.
The values are keys into the available digital inputs defined in `digital_ins`.
You are free to modify these but just be sure they match up in both dictionaries:

```python
digital_ins = {
    'd0'    : DigitalInOut(board.GP0),
    'd1'    : DigitalInOut(board.GP1),
    'd2'    : DigitalInOut(board.GP2),
    'd3'    : DigitalInOut(board.GP3),
    'd4'    : DigitalInOut(board.GP4),
    'd5'    : DigitalInOut(board.GP5),
    'd6'    : DigitalInOut(board.GP6),
    'd7'    : DigitalInOut(board.GP7),
}
```

The complete set of valid button keys can also be seen in `code.py`:

```python
# Enumerate all our digital io inputs as HID button IDs (0-15)
BUTTON_WEST_Y       = 0
BUTTON_SOUTH_B      = 1
BUTTON_EAST_A       = 2
BUTTON_NORTH_X      = 3
BUTTON_SHOULDER_L   = 4
BUTTON_SHOULDER_R   = 5
BUTTON_TRIGGER_L    = 6
BUTTON_TRIGGER_R    = 7
BUTTON_SELECT       = 8
BUTTON_START        = 9
BUTTON_THUMB_L      = 10
BUTTON_THUMB_R      = 11
BUTTON_HAT_UP       = 12
BUTTON_HAT_DOWN     = 13
BUTTON_HAT_LEFT     = 14
BUTTON_HAT_RIGHT    = 15
BUTTON_MAX          = BUTTON_HAT_RIGHT
# CC Volume handled by buttons outside gamepad button range
BUTTON_VOL_UP       = 20
BUTTON_VOL_DOWN     = 21
```

The names should be self explanatory. Note that 'Hat' is USB HID speak for what is commonly
referred to as a
['D-Pad'](https://en.wikipedia.org/wiki/D-pad)

The numeric values 0-15 are those reported as Gamepad button IDs in the USB HID reports.
These have been assigned by reverse engineering of a
[Logitech F310](https://www.logitechg.com/en-in/products/gamepads/f310-gamepad.940-000112.html)
controller - which mimics an Xbox 360 controller - using Gamepad test software such as
[this](https://greggman.github.io/html5-gamepad-test/).
Note that the 'X' & 'Y' pair and the 'A' & 'B' pair are arranged in opposite order to the commonly
used SNES controller. If this is an issue, just swap them around.

The values for volume are arbitrarily assigned to not conflict with the gamepad buttons.

## USB Consumer Control

In addition to the USB HID Gamepad functionality, limited USB _Consumer Control_ functions
are supported. These are currently limited to:

* Volume Up (Increment)
* Volume Down (Decrement)
* Power Off

The volume commands can be mapped to digital GPIO inputs as described [above](#digital-inputs).
The 'power off' functionality is achieved by holding the 'start' button for a period of time
as determined in the code by this constant:

```python
# Holding 'Start' button for this period will send a Power Off command
START_BUTTON_HOLD_FOR_SHUTDOWN_SECS = 3
```

This functionality is also dependent on the host operating system acting upon the USB CC codes
sent by the device. Most modern desktop OS like Windows, macOS & Linux desktop distros will
support this.

Some 'bare bones' Linux distros without a GUI desktop environment may need additional software
to enable this functionality,
e.g. [Raspberry Pi OS Lite](https://www.raspberrypi.com/software/operating-systems/). In these
cases, my [daemon](https://github.com/neildavis/alsa_volume_from_usb_hid) project may work.

## Programmable Serial Interface

In additional to the physical [analog](#analog-inputs) and [digital](#digital-inputs) inputs,
USB HID events can be synthesized using a programmable interface via USD CDC serial comms.

### Motivation

I have created a few custom USB HID input controllers for various projects such as my:

* [Tiger / Grandstand / Sega - After Burner - Tabletop Arcade Conversion](https://www.youtube.com/watch?v=KxgmwC9LNg8)
* [Tomy Demon Driver (1978) vs Sega Monaco GP (1979)](https://www.youtube.com/shorts/3PWjTkotoec)

These projects commonly have significantly fewer inputs than a full dual-shock style gamepad.
They also run on platforms using software such as
[RetroPie](https://retropie.org.uk/),
[RetroArch](https://www.retroarch.com/) and
[EmulationStation](https://github.com/Aloshi/EmulationStation).
These software include useful features to simplify configuration of input devices by producing controller inputs
in response to visual prompts. However, they can assume a full gamepad input set which is not available on my
custom controller. By synthesizing these events, we can make use of these convenient tools without having to
resort to editing config files manually.

### Synthesized input interface

The programmable serial interface makes use of the
[second 'data' serial device](https://learn.adafruit.com/customizing-usb-devices-in-circuitpython/circuitpy-midi-serial#usb-serial-console-repl-and-data-3096590-12)
offered by CircuitPython to receive input. See
[Adafruit's docs](https://learn.adafruit.com/customizing-usb-devices-in-circuitpython/circuitpy-midi-serial#usb-serial-console-repl-and-data-3096590-12)
to learn how to identify the appropriate serial (or 'COM') port for your OS.

You can make use of this interface using any commonly available serial terminal emulator software.
Popular text-base ones include
[Minicom](https://en.wikipedia.org/wiki/Minicom) or
[Screen](https://en.wikipedia.org/wiki/GNU_Screen).
There are also GUI alternatives such as
[PuTTY](https://en.wikipedia.org/wiki/PuTTY).
A large (but non-exhaustive) list can be found
[here](https://en.wikipedia.org/wiki/List_of_terminal_emulators).

The interface accepts commands as a line of text terminated by a CR (`0xD`) or LF (`0xA`).
Each line may contain an arbitrary number of _`name=value`_ pairs separated by a semi-colon.
The available commands are listed in the following table:

| Command Name (e.g.) | Valid Values (e.g.)| Description |
|-|-|-|
| `btn{N}` (e.g. `btn1`) | `1` | Press (and release) button `N`
| `x`, `y`, `z`, `r_z` | `-16327` - `16327` | Set joystick axes analog values
| `vol` | `-1,0,1` | Volume. `1` increments, `-1` decrements |
| `{digital input}` (e.g. `d0`) | `{button id}` (e.g. `9` == '`Start`') | [Re]Map a digital input to a button ID |
| `{analog input}` (e.g. `a0`) | `{joystick axis}` (e.g. `r_z`) | [Re]Map an analog input to a joystick axis |
| `hold` | +ve floating point values | Time in seconds to hold the controls at specified values |
| `pre` | +ve floating point values | Time in seconds to wait ___before___ synthesizing the inputs |
| `post` | +ve floating point values | Time in seconds to wait ___after___ synthesizing the inputs |

By default, the specified input values are __held for half a second__. This can be changed by use of
the `hold` command.

#### Examples

| Command string | Actions |
|-|-|
|'`btn1=1;btn5=1;x=-16327`' | Press buttons 1 & 5 and set left analog stick x-axis full left. |
|'`r_z=8000`' | Move right analog joystick y-axis approx half way down. |
|'`btn=1;hold=5`' | Press button 3 and hold it for five seconds. |
|'`vol=-1;post=2.5`' | Decrement volume and wait for 2.5 seconds before processing any other events or commands. |
|'`d0=9;a3=y`' | Remap digital input `d0` to button number `9` (`Start`) and remap analog input `a3` to left joystick `y` axis. |

### Special Configuration Commands

In addition to the generic programmable serial interface described
[above](#programmable-serial-interface)
specific commands are available to automate particular softwares' configuration procedures.
These commands are not 'compoundable' with the generic commands above and __must__ be entered alone.

* '`conf_es`' : Performs a full input configuration sequence for
[EmulationStation](https://github.com/Aloshi/EmulationStation)
(Main Menu -> Configure Input)
* '`conf_ra`' : Performs a full input configuration sequence for
[RetroArch](https://www.retroarch.com/)
(Main Menu -> Settings -> Input -> Port N Controls -> Set All Controls)
