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
        result = self.get_code(0x01)
        model_number = ""
        for letter in result[0:15]:
            model_number += chr(letter)

        model_number = model_number.replace("\x00", "")
        return model_number


    def get_code(self, FID_wValue, FID_wLength=64):
        """ Perform the control message transfer, return the extracted
        value
        """
        FID_bmRequestType = 0xC0 # device to host
        FID_bmRequest = 0xFF     # upper area, content is wValue
        FID_wIndex = 0           # current specification has all index 0

        try:
            result = self.device.ctrl_transfer(FID_bmRequestType,
                                               FID_bmRequest,
                                               FID_wValue,
                                               FID_wIndex,
                                               FID_wLength)
        except Exception as exc:
            log.critical("Problem with ctrl transfer: %s", exc)

        log.debug("Raw result: [%s]", result)
        return result

    def get_serial_number(self):
        """ Return the serial number portion of the model description.
        """
        result = self.get_code(0x01)
        serial_number = ""
        for letter in result[16:31]:
            serial_number += chr(letter)

        serial_number = serial_number.replace("\x00", "")
        return serial_number
