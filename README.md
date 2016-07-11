WasatchUSB - USB device control from Wasatch Photonics 
 
This module is intended to provide the absolute bare-minimum, pure
python communication with a wasatch photonics device board. 

Feature identification is supported through the scripts/featureid.py file.
Run this program to dump the current configuration of any feature
identification protocol device.

All feature identification devices must be controlled through libusb.
Find the INF files required in:

    WasatchUSB\libusb_drivers\

Usage narrative:

Plug in your Feature Identification protocol supporting device from
Wasatch Photonics into your system. On MS-Windows, wait for the device
to appear in Device Manager with an unknown driver.  Right click the
device, select Update Driver, and point it to the
WasatchUSB\libusb_drivers\ directory.

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
