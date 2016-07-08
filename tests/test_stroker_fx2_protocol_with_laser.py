""" Test cases for the pre-feature_identification era devices. This
includes nearly everything designed and created before 2016.

Use caution with these test cases, as certain feature communication
attempts and configurations are unavailable on certain devices. Lockups
will be common. Use the "Feature Identification" series of tests and
protocol definitions for more reliable communication - if you're
hardware supports it.

This is only for the laser subsection of device capabilities. Complete
the testing with the test_stroker_fx2_protocol file.
"""

import sys
import pytest
import logging
log = logging.getLogger(__name__)

strm = logging.StreamHandler(sys.stdout)
log.addHandler(strm)

# Change these parameters to match the device under test
DEVICE_PID = 0x0028
DEVICE_SERIAL = "S-00179"
FPGA_REVISION = "026-007"
SWCODE_REVISION = "10.0.0.0"

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

    @pytest.fixture
    def device(self, pid=DEVICE_PID):
        from wasatchusb import stroker_protocol
        device = stroker_protocol.StrokerProtocolDevice(pid=pid)
        result = device.connect()
        assert result is True
        return device

    def test_get_laser_temperature(self, device):
        assert device.get_laser_temperature() >= 10.0
        assert device.get_laser_temperature() <= 60.0

    def test_set_laser_enable(self, device):
        assert device.get_laser_enable() == 0
        device.set_laser_enable(1)
        assert device.get_laser_enable() == 1
        device.set_laser_enable(0)

    def test_force_laser_off(self, device):
        # convenience function to ensure the laser is off
        device.set_laser_enable(0)
