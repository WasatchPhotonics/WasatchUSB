""" Test cases for the feature_identification.py module that provides 2016-era
control for wasatch photonics spectrometers and dev_list.

This particular model is the 0x4000 PID which has an ARM
microcontroller.
"""

import sys
import pytest
import logging
log = logging.getLogger(__name__)

strm = logging.StreamHandler(sys.stdout)
log.addHandler(strm)

# Change these parameters to match the device under test
DEVICE_PID = 0x4000
DEVICE_SERIAL = "SVISNIR-00034"
MODEL_NUMBER = "785"
FPGA_REVISION = "008-007"
SWCODE_REVISION = "10.0.0.3"


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

    def test_list_device_is_arm(self, dev_list):
        log.critical("Make sure only arm 0x4000 is connected")

        result = dev_list.get_all()
        assert len(result) == 1
        assert result[0][0] == "0x24aa"
        assert result[0][1] == hex(DEVICE_PID)

    def test_connect_device_close_device(self):
        log.critical("Expect an ARM device connected")

        from wasatchusb import feature_identification
        device = feature_identification.Device(pid=DEVICE_PID)
        result = device.connect()
        assert result is True

        result = device.disconnect()
        assert result is True

    def test_get_model_number(self, device):

        model_number = device.get_model_number()
        assert model_number == MODEL_NUMBER


    def set_arm_calibration(self, device, C0, C1, C2, C3):

        wvl_cal = [C0, C1, C2, C3]

        tec_cal = [1.1, 2.2, 3.3, 30.6, 10.1]
        laser_cal = [40.5, 10.1]
        result = device.set_calibration(wvl_cal, tec_cal, laser_cal)

    def test_set_and_get_arm_calibration(self, device):

        self.set_arm_calibration(device, 1.2345, 2.3456, 3.4567, -4.5678)

        cal_coeff0 = device.get_calibration("C0")
        cal_coeff0 = "%0.4f" % cal_coeff0
        assert cal_coeff0 == "1.2345"

        cal_coeff1 = device.get_calibration("C1")
        cal_coeff1 = "%0.4f" % cal_coeff1
        assert cal_coeff1 == "2.3456"

        cal_coeff1 = device.get_calibration("C2")
        cal_coeff1 = "%0.4f" % cal_coeff1
        assert cal_coeff1 == "3.4567"

        cal_coeff2 = device.get_calibration("C3")
        cal_coeff2 = "%0.4f" % cal_coeff2
        assert cal_coeff2 == "-4.5678"


    @pytest.fixture
    def device(self, pid=DEVICE_PID):
        from wasatchusb import feature_identification
        device = feature_identification.Device(pid=pid)
        result = device.connect()
        assert result is True
        return device

    def test_get_standard_software_code(self, device):
        result = device.get_standard_software_code()
        assert result == SWCODE_REVISION

    def test_get_fpga_revision(self, device):
        result = device.get_fpga_revision()
        assert result == FPGA_REVISION

    def test_get_arm_single_line_of_data(self, device):
        result = device.get_line()
        assert len(result) == 1024
        assert min(result) >= 10
        assert max(result) <= 65535

        average = sum(result) / len(result)
        assert average >= 20

    def test_get_arm_integration_time(self, device):
        assert device.get_integration_time() == 0

    def test_arm_pid_4000_set_integration_time(self, device):
        # device defaults to 0 on power up
        assert device.get_integration_time() == 0
        device.set_integration_time(100)
        assert device.get_integration_time() == 100
