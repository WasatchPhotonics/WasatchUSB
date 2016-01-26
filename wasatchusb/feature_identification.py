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
        result = self.get_upper_code(0x01)
        model_number = ""
        for letter in result[0:15]:
            model_number += chr(letter)

        model_number = model_number.replace("\x00", "")
        return model_number


    def send_code(self, FID_bmRequest):
        """ Perform the control message transfer, return the extracted
        value
        """
        FID_bmRequestType = 0x40 # host to device
        FID_wIndex = 0           # current specification has all index 0
        FID_wLength = ""
        FID_wValue = 0

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


    def get_code(self, FID_bmRequest, FID_wValue=0, FID_wLength=64):
        """ Perform the control message transfer, return the extracted
        value
        """
        FID_bmRequestType = 0xC0 # device to host
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

    def get_upper_code(self, FID_wValue):
        """ Convenience function to wrap "upper area" bmRequest feature
        identification code around the standard get code command.
        """
        return self.get_code(FID_bmRequest=0xFF, FID_wValue=FID_wValue)

    def get_serial_number(self):
        """ Return the serial number portion of the model description.
        """
        FID_bmRequest = 0xFF  # upper area, content is wValue
        result = self.get_upper_code(0x01)
        serial_number = ""
        for letter in result[16:31]:
            serial_number += chr(letter)

        serial_number = serial_number.replace("\x00", "")
        return serial_number

    def get_integration_time(self):
        """ Read the integration time stored on the device.
        """
        result = self.get_code(0xBF)

        return result


    def get_ccd_gain(self):
        """ Read the device stored gain.  Convert from binary wasatch format.
        First bytes is binary encoded: 0 = 1/2, 1 = 1/4, 2 = 1/8 etc.  second
        byte is the part to the left of the decimal, so 231 is 1e7 is 1.90234375
        """
        result = self.get_code(0xC5)
        gain = result[1]
        start_byte = str(result[0])
        for i in range(8):
            bit_val = self.bit_from_string(start_byte, i)
            if   bit_val == 1 and i == 0: gain = gain + 0.5
            elif bit_val == 1 and i == 1: gain = gain + 0.25
            elif bit_val == 1 and i == 2: gain = gain + 0.125
            elif bit_val == 1 and i == 3: gain = gain + 0.0625
            elif bit_val == 1 and i == 4: gain = gain + 0.03125
            elif bit_val == 1 and i == 5: gain = gain + 0.015625
            elif bit_val == 1 and i == 6: gain = gain + 0.0078125
            elif bit_val == 1 and i == 7: gain = gain + 0.00390625

        log.critical("Raw gain is: %s", gain)

        return gain

    def bit_from_string(self, string, index):
        """ Given a string of 1's and 0's, look through each ordinal position
        and return a 1 if it has a one. Otherwise return zero.
        """
        i, j = divmod(index, 8)

        # Uncomment this if you want the high-order bit first
        #j = 8 - j

        if ord(string[i]) & (1 << j):
            return 1

        return 0


    def get_sensor_line_length(self):
        """ The line length is encoded as a LSB two byte integer. Where a value
        of 0, 4 is equivalent to 1024 pixels.
        """
        result = self.get_upper_code(0x03)
        line_length = (result[1] * 256) + result[0]
        return line_length

    def get_laser_availability(self):
        """ Laser availability is a 1 or zero in the first byte of the response.
        """
        result = self.get_upper_code(0x08)
        return result[0]

    def get_standard_software_code(self):
        """ 0xC0 is not to be confused with the device to host specification in
        the control message. This is a vendor defined opcode for returning the
        software information.
        """
        result = self.get_code(0xC0)
        sw_code = "%d.%d.%d.%d" \
                  % (result[3], result[2], result[1], result[0])
        return sw_code


    def get_line(self):
        """ Issue the "acquire" control message, then immediately read
        back from the bulk endpoint.
        """
        result = self.send_code(0xAD)

        line_data = self.device.read(0x82, 2048, 1000)
        log.debug("Raw data: %s", line_data)
        line_data = None
        return line_data
