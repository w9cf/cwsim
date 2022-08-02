# CW Simulator

This is the source repository for a CW contest
simulator written in python, based on and mostly a clone of
Morse Runner by Alex, VE3NEA. Therefore it is a derivative work
of Morse Runner Copyright Copyright 2004-2006, Alex Shovkoplyas, VE3NEA
ve3nea@dxatlas.com.
The Morse Runner source
is distributed  under the [Mozilla Public
License, v. 2.0.](http://mozilla.org/MPL/2.0/)
You can download it
[here](https://github.com/VE3NEA/MorseRunner).

No Morse Runner
files are used directly in this project, but most algorithms are identical,
and often functions are straightforward
translations of the Morse Runner Delphi code
into python. I used
the GNU GPL version of Qt
for my GUI code, so the cwsim code is licensed under
[GNU GPL version
2.0](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html), to
be consistent with that license.

The code runs on Linux, Mac OS, and Windows, and probably any
other platform that supports python, Qt, and portaudio.

## Installation

You just need to satisfy the
requirements in requirements.txt or requirements_qt5.txt
(sounddevice uses portaudio). One way is described below.

### Steps
- Install [python] (https://python.org) version 3.8 or later. 
- The following steps should be done in a terminal (or powershell on Windows)
- Clone this archive:

    `git clone xxx`
- Change to the cwsim directory:

  `cd cwsim`

- Install requirements

  `pip install -r requirements.txt`

   alternatively, to use the older Qt5 version instead of the current Qt6,

  `pip install -r requirements_qt5.txt`

- Run the program with:

  `python python/cwsim.py`
