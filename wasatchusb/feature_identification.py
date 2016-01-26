""" Interface wrapper around libusb and cypress drivers to show feature
identification protocol devices from Wasatch Photonics.
"""

import usb

import logging
log = logging.getLogger(__name__)

class ListDevices(object):
    def __init__(self):
        log.debug("init")

    def get_all(self, vid=0x24aa):
        """ Return the full list of devices that match the vendor id.
        """
        list_devices = []

        for bus in usb.busses():
            for device in bus.devices:
                if device.idVendor == vid:
                    single = (hex(device.idVendor),
                              hex(device.idProduct))
                    list_devices.append(single)

        return list_devices

