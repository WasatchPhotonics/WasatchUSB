""" Test cases for the feature_identification.py module that provides 2016-era
control for wasatch photonics spectrometers and dev_list.

This particular model is the 0x2000 PID which has an FX2
microcontroller and a 512 pixel InGaAs sensor.
"""

import sys
import pytest
import logging
log = logging.getLogger(__name__)

strm = logging.StreamHandler(sys.stdout)
log.addHandler(strm)

# Change these parameters to match the device under test
DEVICE_PID = 0x2000
DEVICE_SERIAL = "S-00152"
MODEL_NUMBER = "1064M"
FPGA_REVISION = "010-003"
SWCODE_REVISION = "10.0.0.0"


class TestFeatureIdentification():

    @pytest.fixture
    def dev_list(self):
        from wasatchusb import feature_identification
        dev_list = feature_identification.ListDevices()
        return dev_list

    def test_list_single_device(self, dev_list):
        log.critical("Make sure only one device connected")

        result = dev_list.get_all()
        assert len(result) == 1

    def test_list_device_is_fx2(self, dev_list):
        log.critical("Make sure only FX2 0x2000 (InGaAs) is connected")

        result = dev_list.get_all()
        assert len(result) == 1
        assert result[0][0] == "0x24aa"
        assert result[0][1] == hex(DEVICE_PID)

    def test_connect_device_close_device(self):
        log.critical("Expect an FX2 ingaas device connected")

        from wasatchusb import feature_identification
        device = feature_identification.Device(pid=DEVICE_PID)
        result = device.connect()
        assert result is True

        result = device.disconnect()
        assert result is True


    def test_get_ingaas_model_number(self, device):

        model_number = device.get_model_number()
        assert model_number == MODEL_NUMBER

    def device(self, pid=0x2000):
        from wasatchusb import feature_identification
        device = feature_identification.Device(pid=pid)
        result = device.connect()
        assert result is True
        return device

    @pytest.fixture
    def device(self, pid=DEVICE_PID):
        from wasatchusb import feature_identification
        device = feature_identification.Device(pid=pid)
        result = device.connect()
        assert result is True
        return device

    def test_get_serial_number(self, device):
        serial_number = device.get_serial_number()
        assert serial_number == DEVICE_SERIAL

    def test_get_integration_time(self, device):
        assert device.get_integration_time() == 1

    def test_get_gain(self, device):
        assert device.get_ccd_gain() == 1.421875

    def test_get_ingaas_sensor_line_length(self, device):
        assert device.get_sensor_line_length() == 512

    def test_get_laser_availability(self, device):
        assert device.get_laser_availability() == 0

    def test_get_standard_software_code(self, device):
        result = device.get_standard_software_code()
        assert result == SWCODE_REVISION

    def test_get_fpga_revision(self, device):
        result = device.get_fpga_revision()
        assert result == FPGA_REVISION

    def test_ingaas_pid_2000_set_integration_time(self, device):
        # device defaults to 1 on power up
        assert device.get_integration_time() == 1
        device.set_integration_time(100)
        assert device.get_integration_time() == 100

    def test_get_single_line_of_data(self, device):
        result = device.get_line()
        assert len(result) == 512
        assert min(result) >= 10
        assert max(result) <= 65535

        average = sum(result) / len(result)
        assert average >= 20
