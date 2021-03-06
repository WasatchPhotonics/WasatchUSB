#!/usr/bin/env python2
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
    """ Create a list of vendor id, product id pairs of any device on
    the bus with the 0x24AA VID. Explicitly reject the newer feature
    identification devices.
    """
    def __init__(self):
        log.debug("init")

    def get_all(self, vid=0x24aa):
        """ Return the full list of devices that match the vendor id.
        Explicitly reject the feature identification codes
        """
        list_devices = []

        for bus in usb.busses():
            for device in bus.devices:

                single = self.device_match(device, vid)

                if single is not None:
                    list_devices.append(single)

        return list_devices

    def device_match(self, device, vid):
        """ Match vendor id and rejectable feature identification
        devices.
        """
        if device.idVendor != vid:
            return None

        if device.idProduct == 0x1000 or \
           device.idProduct == 0x2000 or \
           device.idProduct == 0x3000 or \
           device.idProduct == 0x4000:
               return None

        single = (hex(device.idVendor), hex(device.idProduct))
        return single

class StrokerProtocolDevice(object):
    """ Provide function wrappers for all of the common tasks associated
    with stroker control. This includes control messages to pass
    settings back and forth, as well as bulk transfers to get lines of
    data from the device.
    """
    def __init__(self, vid=0x24aa, pid=0x0001):
        log.debug("init")
        self.vid = vid
        self.pid = pid
        self.device = None
        self.tec_coeff0 = 3566.62
        self.tec_coeff1 = -143.543
        self.tec_coeff2 = -0.324723

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


    def get_code(self, FID_bmRequest, FID_wValue=0, FID_wLength=64):
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


    def get_serial_number(self):
        """ Return the serial number portion of the USB descriptor.
        """
        serial = "Unavailable"

        # Older units support the 256 langid. Newer units require none.
        try:
            serial = usb.util.get_string(self.device,
                                         self.device.iSerialNumber, 256)
        except Exception as exc:
            log.debug("Failure to read langid 256 serial: %s", exc)

        try:
            serial = usb.util.get_string(self.device,
                                         self.device.iSerialNumber)
        except Exception as exc:
            log.debug("Failure to read langid none serial: %s", exc)

        return serial


    def get_integration_time(self):
        """ Read the integration time stored on the device.
        """
        result = self.get_code(0xBF)

        curr_time = (result[2] * 0x10000) + (result[1] * 0x100) + result[0]

        log.debug("Integration time: %s", curr_time)
        return curr_time


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

    def get_standard_software_code(self):
        """ 0xC0 is not to be confused with the device to host specification in
        the control message. This is a vendor defined opcode for returning the
        software information. Result is Major version, hyphen, minor
        version.
        """
        result = self.get_code(0xC0)
        sw_code = "%d-%d" \
                  % (result[0], result[1])
        return sw_code

    def get_fpga_revision(self):
        """ The version of the FPGA code read from the device. First
        three bytes plus a hyphen is the major version, then last three
        bytes is the minor.
        """
        result = self.get_code(0xB4)


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

        # Append the 2048 pixel data for just MTI produt id (1)
        if self.pid == 1:
            second_half = self.read_second_half()
            data.extend(second_half)

        return data

    def read_second_half(self):
        """ Read from end point 86 of the ancient-er 2048 pixel
            hamamatsu detector in MTI units.
        """
        log.debug("Also read off end point 86")
        data = self.device.read(0x86, 2048, timeout=1000)
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
            result = self.get_code(0xD5)
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

        result = self.get_code(0xD7)

        log.debug("Plain adc: %s", result)

        # Swap endianness of raw ADC value
        adc_value  = float(result[1] + (result[0] * 256))

        # Convert to voltage (12 bit)
        voltage    = float((adc_value / 4096.0) * 1.5)

        # Convert to resistance
        resistance = 10000 * voltage
        resistance = resistance / (2 - voltage)

        # Find the log of the resistance with a 10kOHM resistor
        logVal     = math.log( resistance / 10000 )
        insideMain = float(logVal + ( 3977.0 / (25 + 273.0) ))
        tempc      = float( (3977.0 / insideMain) -273.0 )

        return tempc

    def get_laser_enable(self):
        """ Read the laser enable status from the device.
        """
        result = self.get_code(0xE2)
        return result[0]

    def set_laser_enable(self, value=0):
        """ Write one for enable, zero for disable of laser on the
        device.
        """
        if self.pid == 1:
            log.warn("DISABLING LASER FUNCTION FOR MTI")
            return

        log.debug("Send laser enable: %s", value)
        result = self.send_code(0xBE, value)
        return result

    def set_ccd_tec_enable(self, value=0):
        """ Write one for enable, zero for disable of the ccd tec
        cooler.
        """
        log.debug("Send CCD TEC enable: %s", value)
        result = self.send_code(0xD6, value)

        log.critical("Double set required, see notes.")
        result = self.send_code(0xD6, value)

    def get_calibration_coeffs(self):
        """ Read the calibration coefficients from the on-board EEPROM.
        """

        eeprom_data = self.get_code(0xA2)
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

    def set_ccd_tec_setpoint(self, setpoint):
        """ Attempt to set the CCD cooler setpoint. Verify that it is
        within an acceptable range. Ideally this is to prevent
        condensation and other issues. This value is a default and is
        hugely dependent on the environmental conditions.
        """

        setpoint_min = 10
        setpoint_max = 20
        ok_range = "%s,%s" % (setpoint_min, setpoint_max)
        if setpoint < setpoint_min:
            log.critical("TEC setpoint out of range (%s)", ok_range)
            return False

        if setpoint > setpoint_max:
            log.critical("TEC setpoint out of range (%s)", ok_range)
            return False

        new_point = self.tec_coeff0 + (self.tec_coeff1 * setpoint)
        new_point += (self.tec_coeff2 * (setpoint * setpoint))
        new_point = int(new_point)

        log.debug("Setting TEC setpoint to: %s", new_point)
        result = self.send_code(0xD8, new_point)
        return True

