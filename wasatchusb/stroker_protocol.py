""" Interface wrapper around the libusb drivers to show stroker protocol
communication for devices from Wasatch Photonics. Stroker in this case
is an homage to automotive performance:
https://en.wikipedia.org/wiki/Stroker_kit
"""

import usb
import math
import struct

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

class StrokerProtocolDevice(object):
    def __init__(self, vid=0x24aa, pid=0x0001):
        log.debug("init")
        self.vid = vid
        self.pid = pid
        self.device = None

    def connect(self):
        """ Attempt to connect to the specified device. Log any failures and
        return False if there is a problem, otherwise return True.
        """

        try:
            device = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        except Exception as exc:
            log.critical("Exception in find: %s", exc)
            log.info("Is the device available with libusb?")
            return False

        if device is None:
            log.critical("Can't find: %s, %s" % (self.vid, self.pid))
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
        """ Function stub for historical matching of expected explicit
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


    def send_code(self, FID_bmRequest, FID_wValue=0):
        """ Perform the control message transfer required to send a
        value to the device, return the extracted value.
        """
        FID_bmRequestType = 0x40 # host to device
        FID_wIndex = 0           # current specification has all index 0
        FID_wLength = ""

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


    def get_sp_code(self, FID_bmRequest, FID_wValue=0, FID_wLength=64):
        """ Use the StrokerProtocol (sp), and perform the control
        message transfer required to get a setting from the device.
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

    def send_sp_code(self, FID_bmRequest, FID_wValue=0):
        """ Perform the control message transfer, return the extracted
        value
        """
        FID_bmRequestType = 0x40 # host to device
        FID_wIndex = 0           # current specification has all index 0
        FID_wLength = ""

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
        return self.get_sp_code(FID_bmRequest=0xFF, FID_wValue=FID_wValue)


    def get_serial_number(self):
        """ Return the serial number portion of the USB descriptor.
        """
        serial = "Unavailable"
        try:
            serial = usb.util.get_string(self.device,
                                         self.device.iSerialNumber, 256)
        except Exception as exc:
            log.warn("Failure to read serial: %s", exc)

        return serial


    def get_integration_time(self):
        """ Read the integration time stored on the device.
        """
        result = self.get_sp_code(0xBF)

        curr_time = (result[2] * 0x10000) + (result[1] * 0x100) + result[0]

        log.critical("Integration time: %s", curr_time)
        return curr_time


    def get_ccd_gain(self):
        """ Read the device stored gain.  Convert from binary wasatch format.
        First bytes is binary encoded: 0 = 1/2, 1 = 1/4, 2 = 1/8 etc.  second
        byte is the part to the left of the decimal, so 231 is 1e7 is 1.90234375
        """
        result = self.get_sp_code(0xC5)
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

        log.debug("Raw gain is: %s", result)

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
        result = self.get_sp_code(0xC0)
        sw_code = "%d.%d.%d.%d" \
                  % (result[3], result[2], result[1], result[0])
        return sw_code

    def get_fpga_revision(self):
        """ The version of the FPGA code read from the device. First
        three bytes plus a hyphen is the major version, then last three
        bytes is the minor.
        """
        result = self.get_sp_code(0xB4)


        chr_fpga_suffix = "%s%s%s" \
                          % (chr(result[4]), chr(result[5]),
                             chr(result[6]))

        chr_fpga_prefix = "%s%s%s%s" \
                          % (chr(result[0]), chr(result[1]),
                             chr(result[2]), chr(result[3]))

        return "%s%s" % (chr_fpga_prefix, chr_fpga_suffix)


    def get_line(self):
        """ Issue the "acquire" control message, then immediately read
        back from the bulk endpoint.
        """
        result = self.send_code(0xAD)

        line_buffer = 2048 # 1024 16bit pixels
        if self.pid == 0x2000:
            line_buffer = 1024 # 512 16bit pixels
        data = self.device.read(0x82, line_buffer, timeout=1000)
        log.debug("Raw data: %s", data)

        try:
            data = [i + 256 * j for i, j in zip(data[::2], data[1::2])]
        except Exception as exc:
            log.critical("Failure in data unpack: %s", exc)
            data = None

        return data

    def set_integration_time(self, int_time):
        """ Send the updated integration time in a control message to the device.
        """

        log.debug("Send integration time: %s", int_time)
        result = self.send_code(0xB2, int_time)
        return result


    def get_laser_temperature(self):
        """ Read the Analog to Digital conversion value from the device.
        Apply formula to convert AD value to temperature, return raw
        temperature value.
        """
        result = -273 # The clearly invalid value

        try:
            result = self.get_sp_code(0xD5)
        except Exction as exc:
            log.critical("Failure reading temperature: %s", exc)
            return result

        log.debug("Plain adc: %s", result)

        try:
            adc_value  = float(result[0] + (result[1] * 256))
            voltage    = float((adc_value / 4096.0) * 2.5)
            resistance = 21450 * voltage
            resistance = resistance / (2.5 - voltage)
            logVal     = math.log( resistance / 10000 )
            insideMain = float(logVal + ( 3977.0 / (25 + 273.0) ))
            tempc      = float( (3977.0 / insideMain) -273.0 )
            result = tempc

        except Exception as exc:
            log.critical("Failure processing laser temperature: %s",
                         exc)
            return -173 # clearly less invalid

        return result


    def get_ccd_temperature(self):
        """ Read the Analog to Digital conversion value from the device.
        Apply formula to convert AD value to temperature, return raw
        temperature value.
        """

        result = -273 # The clearly invalid value

        try:
            result = self.get_sp_code(0xD7)
        except Exction as exc:
            log.critical("Failure reading temperature: %s", exc)
            return result

        log.debug("Plain adc: %s", result)

        try:
            adc_value  = float(result[1] + (result[0] * 256))
            voltage    = float((adc_value / 4096.0) * 1.5)
            tempc = 0.01
            resistance = 10000 * voltage
            resistance = resistance / (2 - voltage)
            logVal     = math.log( resistance / 10000 )
            insideMain = float(logVal + ( 3977.0 / (25 + 273.0) ))
            tempc      = float( (3977.0 / insideMain) -273.0 )
            result     = tempc

        except Exception as exc:
            log.critical("Failure processing laser temperature: %s",
                         exc)
            return -173 # clearly less invalid

        return result

    def get_laser_enable(self):
        """ Read the laser enable status from the device.
        """
        result = self.get_sp_code(0xE2)
        return result[0]

    def set_laser_enable(self, value=0):
        """ Write one for enable, zero for disable of laser on the
        device.
        """
        log.debug("Send laser enable: %s", value)
        result = self.send_code(0xBE, value)
        return result

    def get_calibration_coeffs(self):
        """ Read the calibration coefficients from the on-board EEPROM.
        """

        eeprom_data = self.get_sp_code(0xA2)
        log.debug("Full eeprom dump: %s", eeprom_data)

        c0 = self.decode_eeprom(eeprom_data, width=8, offset=0)
        c1 = self.decode_eeprom(eeprom_data, width=8, offset=8)
        c2 = self.decode_eeprom(eeprom_data, width=8, offset=16)
        c3 = self.decode_eeprom(eeprom_data, width=8, offset=24)

        log.debug("Coeffs: %s, %s, %s, %s" % (c0, c1, c2, c3))
        return [c0, c1, c2, c3]

    def decode_eeprom(self, raw_data, width, offset=0):
        """ Reorder, pad and decode the eeprom data to produce a string
        representation of the value stored in the device memory.
        """
        # Take N width slice of the data starting from the offset
        top_slice = raw_data[offset:offset+width]

        # Unpack as an integer, always returns a tuple
        unpacked = struct.unpack("d", top_slice)

        log.debug("Unpacked str: %s ", unpacked)
        return str(unpacked[0])
