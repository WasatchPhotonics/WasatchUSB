""" Interface wrapper around libusb and cypress drivers to show feature
identification protocol devices from Wasatch Photonics.
"""

import usb
import usb.core
import usb.util
import struct
import math
import sys

import logging
log = logging.getLogger(__name__)

frmt = logging.Formatter("%(name)s %(levelname)-8s %(message)s")
log.setLevel(level=logging.INFO)
strm = logging.StreamHandler(sys.stdout)
strm.setFormatter(frmt)
log.addHandler(strm)


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
        self.tec_coeff0 = 3566.62
        self.tec_coeff1 = -143.543
        self.tec_coeff2 = -0.324723

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

    def get_calibration(self, coefficient="C0"):
        """ Extract the appropriate calibration coefficient field with a
        control message to the device.
        """

        # The calibration data is stored in the second 'page' of the
        # control message
        second_page = 1
        result = self.get_upper_code(0x01, FID_wIndex=second_page)

        coeff_position = {"C0": [0, 8],
                          "C1": [8, 16],
                          "C2": [16, 24],
                          "C3": [24, 32]
                         }

        start = coeff_position[coefficient][0]
        cease = coeff_position[coefficient][1]
        get_coeff = struct.unpack("d", result[start:cease])[0]

        log.debug("Get: %s", get_coeff)
        return get_coeff

    def set_calibration(self, wvl_cal, tec_cal, laser_cal):
        """ Write the expected precision value for the given coefficients
        to the device eeprom. The entire page must be written at once,
        so make sure all of the values are populated.
        """

	wvl_c0 = float(wvl_cal[0])
	wvl_c1 = float(wvl_cal[1])
	wvl_c2 = float(wvl_cal[2])
	wvl_c3 = float(wvl_cal[3])

	tec_c0 = float(tec_cal[0])
	tec_c1 = float(tec_cal[1])
	tec_c2 = float(tec_cal[2])

	tec_max = float(tec_cal[3]) # maximum
	tec_min = float(tec_cal[4]) # minimum

	laser_max = float(laser_cal[0]) # maximum
	laser_min= float(laser_cal[1]) # minimum

	placeholder = float(0.0)

        packed = struct.pack("4d8f",
                             wvl_c0, wvl_c1, wvl_c2, wvl_c3,
                             tec_c0, tec_c1, tec_c2,
                             tec_max, tec_min,
                             laser_max, laser_min,
                             placeholder)

        log.debug("packed: %s" % packed)

        self.send_code(FID_bmRequest=0xFF,
                       FID_wValue=0x02, # Set eeprom code
                       FID_wIndex=0x01, # second page
                       FID_data_or_wLength=packed)


    def send_code(self, FID_bmRequest, FID_wValue=0, FID_wIndex=0,
                  FID_data_or_wLength=""):
        """ Perform the control message transfer, return the extracted
        value. Yes, the USB spec really does say data_or_length
        """
        FID_bmRequestType = 0x40 # host to device

        result = None
        try:
            result = self.device.ctrl_transfer(FID_bmRequestType,
                                               FID_bmRequest,
                                               FID_wValue,
                                               FID_wIndex,
                                               FID_data_or_wLength)
        except Exception as exc:
            log.critical("Problem with ctrl transfer: %s", exc)

        log.debug("Send Raw result: [%s]", result)
        return result


    def get_code(self, FID_bmRequest, FID_wValue=0, FID_wLength=64,
                 FID_wIndex=0):
        """ Perform the control message transfer, return the extracted
        value
        """
        FID_bmRequestType = 0xC0 # device to host

        result = None
        try:
            result = self.device.ctrl_transfer(FID_bmRequestType,
                                               FID_bmRequest,
                                               FID_wValue,
                                               FID_wIndex,
                                               FID_wLength)
        except Exception as exc:
            log.critical("Problem with ctrl transfer: %s", exc)

        log.debug("Get Raw result: [%s]", result)
        return result

    def get_upper_code(self, FID_wValue, FID_wIndex=0):
        """ Convenience function to wrap "upper area" bmRequest feature
        identification code around the standard get code command.
        """
        return self.get_code(FID_bmRequest=0xFF,
                             FID_wValue=FID_wValue,
                             FID_wIndex=FID_wIndex)


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

        curr_time = (result[2] * 0x10000) + (result[1] * 0x100) + result[0]

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

        result = self.send_code(0xAD, FID_data_or_wLength="00000000")

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

    def set_ccd_tec_enable(self, value=0):
        """ Write one for enable, zero for disable of the ccd tec
        cooler.
        """
        log.debug("Send CCD TEC enable: %s", value)
        result = self.send_code(0xD6, value)

        log.critical("Double set required, see notes.")
        result = self.send_code(0xD6, value)

    def set_laser_enable(self, value=0):
        """ Write one for enable, zero for disable of laser on the
        device.
        """
        log.debug("Send laser enable: %s", value)
        result = self.send_code(0xBE, value)
        return result
