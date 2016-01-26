""" Interface wrapper around libusb and cypress drivers to show feature
identification protocol devices from Wasatch Photonics.
"""

import usb
import usb.core
import usb.util

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

class Device(object):
    def __init__(self, vid=0x24aa, pid=0x1000):
        log.debug("init")
        self.vid = vid
        self.pid = pid
        self.device = None

    def connect(self):
        """ Attempt to connect to the specified device. Log any failures and
        return False if there is a problem, otherwise return True.
        """

        device = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        if device is None:
            log.critical("Can't find: %s, %s", (self.vid, self.pid))
            return False

        log.debug("Attempt to set configuration")
        try:
            result = device.set_configuration(1)
        except Exception as exc:
            log.warn("Failure in setConfiguration %s", exc)
            return False

        try:
            result = usb.util.claim_interface(device, 0)
        except Exception as exc:
            log.warn("Failure in claimInterface: %s", exc)
            return None

        self.device = device
        return True

    def disconnect(self):
        """ Function stub for historical matching of expected explicity
        connect and disconnect.
        """
        log.info("Placeholder disconnect")
        return True

    def get_model_number(self):
        """ Extract the appropriate field with a control message to the
        device.
        """

#            result = self.od.controlMsg(self.DEVICE2HOST, 
#                                        self.CMD_GET_LASER,
#                                        1, 0, 0, self.timeout)
   
        try:
            # bmRequestType, bmRequest, wValue, wIndex
            result = self.device.ctrl_transfer(0xC0, 0xFF, 0x01, 0, 64)
        except Exception as exc:
            log.critical("Problem with ctrl transfer: %s", exc)

        log.info("Raw result: [%s]", result)
        model_number = result[0:15]
        log.debug("Raw model: [%r]", model_number)

        model_number = ""
        for letter in result[0:15]:
            model_number += chr(letter)
        #serial_number = result[16:31].replace("\x00", "")
        model_number = model_number.replace("\x00", "")
        return model_number


