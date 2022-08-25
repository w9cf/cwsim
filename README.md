# CW Simulator

This is the source repository for a CW contest
simulator written in python, based on and mostly a clone of
Morse Runner by Alex, VE3NEA. Therefore it is a derivative work
of Morse Runner Copyright 2004-2006, Alex Shovkoplyas, VE3NEA
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
the GNU GPL version of Qt and Qt Designer
for my GUI code, so the cwsim code is licensed under
[GNU GPL version
3.0](https://www.gnu.org/licenses/gpl-3.0.en.html), to
be consistent with that license.

The code runs on Linux, Mac OS, and Windows, and probably any
other platform that supports python, Qt, and portaudio.

## Installation

You just need to satisfy the
requirements in requirements.txt or requirements_qt5.txt
(sounddevice uses portaudio). One way is to use pip and requirements:

### Steps
- Install [python](https://python.org) version 3.8 or later. 
- The following steps should be done in a terminal (or powershell on Windows)
- Clone this archive:

    `git clone https://github.com/w9cf/cwsim`
- Change to the cwsim directory:

  `cd cwsim`

- Install requirements

  `pip install -r requirements.txt --user`

   alternatively, to use the older Qt5 version instead of the current Qt6,

  `pip install -r requirements_qt5.txt --user`

- Run the program with:

  `python python/cwsim.py`

### Alternative for Raspberry Pi 4B
I normally run Slackware on my PI 4B. The installation just uses
sbopkg and slackbuilds.com to add the needed packages. I did
test with the 2022-04-04 64bit Raspberry Pi operating system. Here are
the commands I used to install the needed packages:
```
git clone https://github.com/w9cf/cwsim.git
sudo apt-get install python3-matplotlib
sudo apt-get install python3-pyqt5
sudo apt-get install libportaudio2
pip install pip --upgrade --user
python3 -m pip install numpy==1.23 --user
python3 -m pip install sounddevice --user
python3 -m pip install pyxdg --user
```

Then
```
cd cwsim/python
python3 cwsim.py
```
Note! Make sure the numpy version is >= 1.22, otherwise a numpy.accumulate
bug in older versions will crash the program unless QSK is turned off.
This bug was fixed in numpy 1.22. The
```python3 -m pip install numpy==1.23 --user```
command above will install numpy 1.23 locally.
