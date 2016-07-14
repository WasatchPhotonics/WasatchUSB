""" Test cases for the pre-feature_identification era devices. This
includes nearly everything designed and created before 2016.

Use caution with these test cases, as certain feature communication
attempts and configurations are unavailable on certain devices. Lockups
will be common if you attempt to access functionality that is not
present on the device. Use the "Feature Identification" series of tests
and protocol definitions for more reliable communication - if your
hardware supports it.
"""

import sys
import pytest
import logging
log = logging.getLogger(__name__)

strm = logging.StreamHandler(sys.stdout)
log.addHandler(strm)

class TestStrokerProtocol():
    @pytest.fixture
    def dev_list(self):
        from wasatchusb import stroker_protocol
        dev_list = stroker_protocol.ListDevices()
        return dev_list

    def test_list_no_dev_list(self, dev_list):
        log.critical("Make sure no devices are connected")

        result = dev_list.get_all()
        assert len(result) == 0

    def test_list_single_device(self, dev_list):
        log.critical("Make sure only one device connected")

        result = dev_list.get_all()
        assert len(result) == 1

    def test_list_device_is_stroker_protocol(self, dev_list):
        log.critical("Make sure only FX2 0x0001 is connected")

        result = dev_list.get_all()
        assert len(result) == 1
        assert result[0][0] == "0x24aa"
        assert result[0][1] == "0x1"

    def test_list_device_is_stroker_protocol_arm_mods(self, dev_list):
        log.critical("Make sure only FX2 0x0009 is connected")

        result = dev_list.get_all()
        assert len(result) == 1
        assert result[0][0] == "0x24aa"
        assert result[0][1] == "0x9"

    def test_connect_stroker_device_close_device(self):
        log.critical("Expect stroker protocol device connected")

        from wasatchusb import stroker_protocol
        device = stroker_protocol.StrokerProtocolDevice(pid=0x0028)
        result = device.connect()
        assert result is True

        result = device.disconnect()
        assert result is True

    @pytest.fixture
    def device(self, pid=0x0028):
        from wasatchusb import stroker_protocol
        device = stroker_protocol.StrokerProtocolDevice(pid=pid)
        result = device.connect()
        assert result is True
        return device

    @pytest.fixture
    def arm_mods_device(self):
        return self.device(pid=0x0009)

    def test_get_serial_number(self, device):
        serial_number = device.get_serial_number()
        assert serial_number == "S-00179"

    def test_get_integration_time(self, device):
        assert device.get_integration_time() == 0

    def test_stroker_protocol_set_integration_time(self, device):
        # device defaults to 0 on power up
        assert device.get_integration_time() == 0
        device.set_integration_time(100)
        assert device.get_integration_time() == 100

    def test_get_laser_temperature(self, device):
        assert device.get_laser_temperature() >= 10.0
        assert device.get_laser_temperature() <= 60.0

    def test_get_ccd_temperature(self, device):
        assert device.get_ccd_temperature() >= 1.0
        assert device.get_ccd_temperature() <= 90.0

    def test_set_laser_enable(self, device):
        assert device.get_laser_enable() == 0
        device.set_laser_enable(1)
        assert device.get_laser_enable() == 1
        device.set_laser_enable(0)

    def test_force_laser_off(self, device):
        # convenience function to ensure the laser is off
        device.set_laser_enable(0)


    """ ################################################################
    The following tests will show indeterminate behavior dependent on the
    condition of the now obsolete 0x24AA 0X0009 build. This device
    apparently will always return -173 for the temperature of the laser,
    until the acquisition has been setup and collected. This apparently is
    masked by the current Dash code base, which does the 4 acquisitions
    behind the scenes before displaying spectra to the user, which is
    designed in for exactly this type of scenario. Current testing for laser
    power stability is best served by turning the laser on manually with:

    python -u -m unittest
        WasatchDevices.LibUsbStroker785SPI.Test.test_55_laser_on

    The turn off the laser_enable portion in
    BoardTester/TemperatureLogger.py,

    """
    def test_set_arm_mods_laser_enable(self, arm_mods_device):
        assert arm_mods_device.get_laser_enable() == 0
        arm_mods_device.set_laser_enable(1)
        assert arm_mods_device.get_laser_enable() == 1
        arm_mods_device.set_laser_enable(0)

    def test_get_arm_mods_integration_time(self, arm_mods_device):
        assert arm_mods_device.get_integration_time() == 0

    def test_get_arm_mods_laser_temperature(self, arm_mods_device):
        assert arm_mods_device.get_laser_temperature() >= 10.0
        assert arm_mods_device.get_laser_temperature() <= 60.0

    """ ############################################################ """

    def test_get_calibration_eeprom(self, arm_mods_device):
        coeffs = arm_mods_device.get_calibration_coeffs()
        assert coeffs[0] == "1.001"
        assert coeffs[1] == "2.002"
        assert coeffs[2] == "3.003"
        assert coeffs[3] == "4.004"

