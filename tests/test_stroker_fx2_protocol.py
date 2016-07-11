""" Test cases for the pre-feature_identification era devices. This
includes nearly everything designed and created before 2016.

Use caution with these test cases, as certain feature communication
attempts and configurations are unavailable on certain devices. Lockups
will be common. Use the "Feature Identification" series of tests and
protocol definitions for more reliable communication - if you're
hardware supports it.
"""

import sys
import pytest
import logging
log = logging.getLogger()

frmt = logging.Formatter("%(name)s %(levelname)-8s %(message)s")
log.setLevel(level=logging.DEBUG)
strm = logging.StreamHandler(sys.stdout)
strm.setFormatter(frmt)
log.addHandler(strm)


# Change these parameters to match the device under test
DEVICE_PID = 0x0028
DEVICE_SERIAL = "S-00179"
FPGA_REVISION = "023-008"
SWCODE_REVISION = "36-0"

class TestStrokerProtocol():
    @pytest.fixture
    def dev_list(self):
        from wasatchusb import stroker_protocol
        dev_list = stroker_protocol.ListDevices()
        return dev_list

    def test_list_single_device(self, dev_list):
        log.critical("Make sure only one device connected")

        result = dev_list.get_all()
        assert len(result) == 1

    def test_list_device_is_stroker_protocol(self, dev_list):
        log.critical("Make sure only %s is connected", hex(DEVICE_PID))

        result = dev_list.get_all()
        assert len(result) == 1
        assert result[0][0] == "0x24aa"
        assert result[0][1] == hex(DEVICE_PID)

    def test_connect_stroker_device_close_device(self):
        # Fixture-less test for bare bones connectivity
        log.critical("Expect stroker protocol device connected")

        from wasatchusb import stroker_protocol
        device = stroker_protocol.StrokerProtocolDevice(pid=DEVICE_PID)
        result = device.connect()
        assert result is True

        result = device.disconnect()
        assert result is True

    @pytest.fixture
    def device(self, pid=DEVICE_PID):
        from wasatchusb import stroker_protocol
        device = stroker_protocol.StrokerProtocolDevice(pid=pid)
        result = device.connect()
        assert result is True
        return device

    def test_get_serial_number(self, device):
        serial_number = device.get_serial_number()
        assert serial_number == DEVICE_SERIAL

    def test_get_integration_time(self, device):
        assert device.get_integration_time() == 0

    def test_stroker_protocol_set_integration_time(self, device):
        # device defaults to 0 on power up
        assert device.get_integration_time() == 0
        device.set_integration_time(100)
        assert device.get_integration_time() == 100

    def test_get_ccd_temperature(self, device):
        assert device.get_ccd_temperature() >= 1.0
        assert device.get_ccd_temperature() <= 90.0

    def test_set_ccd_tec_setpoint_fails(self, device):
        """ Verify that you can't set an out of range temperature
        setpoint, or a setpoint before TEC coefficients are assigned.
        """
        result = device.get_ccd_tec_setpoint()
        assert result == 0.0

        # Minimum range check
        result = device.set_ccd_tec_setpoint(5.0)
        assert result == False

        # Maximum range check
        result = device.set_ccd_tec_setpoint(25.0)
        assert result == False


    def test_set_get_ccd_tec_setpoint(self, device):
        result = device.get_ccd_tec_setpoint()
        assert result == 0.0

        result = device.set_ccd_tec_setpoint(15.0)
        assert result == True

        result = device.get_ccd_tec_setpoint()
        assert result == 15.0

    def test_get_standard_software_code(self, device):
        result = device.get_standard_software_code()
        assert result == SWCODE_REVISION

    def test_get_fpga_revision(self, device):
        result = device.get_fpga_revision()
        assert result == FPGA_REVISION

    def test_get_single_line_of_data(self, device):
        result = device.get_line()
        assert len(result) == 1024
        assert min(result) >= 10
        assert max(result) <= 65535

        average = sum(result) / len(result)
        assert average >= 20

