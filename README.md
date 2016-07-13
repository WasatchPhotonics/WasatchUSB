WasatchUSB - USB device control from Wasatch Photonics 
 
This module is intended to provide the absolute bare-minimum, pure
python communication with a wasatch photonics device board. 

![Continuous demo](/wasatchusb/assets/continuous_demo.gif "Spectra and Temperature")

Feature identification is supported through the scripts/featureid.py file.
Run this program to dump the current configuration of any feature
identification protocol device.


Usage narrative:

Open a command prompt, and run:

    cd <projects>\WasatchUSB
    python scripts\featureid.py

You will see output similar to:

    Model:  785IOC
    Serial: S-00146
    SWCode: 10.0.0.0
    Gain:     1.296875
    Int Time: 0
    Laser Avail: 0
    Sensor Length: 1024

    
    +837    ▅                                      █                               
            █                                      █                               
            █                                      █      ▂                      ▂ 
            █                                      █▄     █                      █ 
            █                     ▄     ▇          ██     █            ▄     ▄   █ 
            █        ▂▅ ▅   ▅     █     █          ██    ▅█   █ █  ▂   █     █   █ 
           ▇█▄       ██ █ ▇ █▄▄   █     █     ▇    ██    ██   █ █  █   █   ▄ █▄ ▄█ 
           ████▅  █▂ ██▅█▅█ ███ ▅ █ █ ▅▅█ ▂   █    ██ ▂  ██   █▅█  █▂ ▂█▂▅██▂██ ██▅
          ▂█████  ██▅██████████▅█▅█████████ ▂▂██  ███▅█  ██   ████▅██▂█████████████
    +787  ██████▇▇█████████████████████████▇████  █████▄ ██▄▄▇█████████████████████
          Min: 783 Max: 1285 Avg: 801


Older devices are supported through the Stroker Protocol interface. Stroker in this
context refers to automotive performance: https://en.wikipedia.org/wiki/Stroker_kit


##Software Installation
---------------

Line graphs are shown in a terminal on Linux. For the command line
visualizations, make sure you have the following prerequisites:

Library-enabled fork of the excellent [diagram](https://github.com/WasatchPhotonics/diagram) package.

A UTF-8 enabled font and terminal. The screen capture was created using
Source Code Pro and gnome-terminal.

Baseline tests are available without the spectra and cooling
visualization on both MS Windows and Linux. First, follow the
instructions in the Device Configuration section below. Run the tests
specific to your unit with the commands:

    git clone https://github.com/WasatchPhotonics/WasatchUSB
    # optional installation of diagram package 

    cd WasatchUSB
    python setup.py develop

    # Display basic device data
    python -u scripts/stroker.py

    # Run all verification scripts
    py.test tests/test_stroker_fx2_protocol.py

##Device Configuration
--------------------

### MS Windows
All feature identification devices must be controlled through libusb.
Find the INF files required for control on MS Windows in:

    WasatchUSB\libusb_drivers\

Plug in your Feature Identification protocol supporting device from
Wasatch Photonics into your system. On MS-Windows, wait for the device
to appear in Device Manager with an unknown driver.  Right click the
device, select Update Driver, and point it to the
WasatchUSB\libusb_drivers\ directory.

### Linux
Enable access to the wasatch device in userland. On Fedora Core 24, this
is done with:

sudo cp udev_rules/99-wasatch.rules /etc/udev/rules.d/
(power cycle the usb device)



