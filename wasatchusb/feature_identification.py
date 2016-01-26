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

class Device(object):
    def __init__(self, vid=0x24aa, pid=0x1000):
        log.debug("init")
        self.vid = vid
        self.pid = pid

    def connect(self):
        """ Attempt to connect to the specified device. Log any failures and
        return None if there is a problem.
        """

        device = None
        try:
            for bus in usb.busses():
                for dev in bus.devices:
                    if dev.idVendor == self.vid and  \
                    dev.idProduct == self.pid:
                        log.info("attempt open")
                        device = dev.open()

        except Exception as exc:
            log.warn("Failure in connect %s", exc)
            return device

        log.debug("Attempt to set configuration")
        try:
            result = device.setConfiguration(1)
        except Exception as exc:
            log.warn("Failure in setConfiguration %s", exc)

        try:
            result = device.claimInterface(0)
        except Exception as exc:
            log.warn("Failure in claimInterface: %s", exc)

        return device

    def device_disconnect(self):
        if self.od <= 0:
            #self.error_message = "Can't disconnect a non-open device"
            return 0

        try:
            #TODO: actually close device
            result = "fake"
            #result = self.od.releaseInterface()
            #self.log.info("released " + str(result) + " " + str( self.od))
            if result != None:
                self.error_message = "Cannot close device"
                return 0
        except:
            self.log.warn("releaseInterface call fail: " + \
                             str(sys.exc_info()))
            pass

        #self.log.info("out pass ")
        self.my_vid = -1
        self.my_pid = -1

        # Expect the release to fail on unplug, if you issue a disconnect above
        # that fails for different reason that's a ret code 0, otherwise return
        # a 1

        return 1

