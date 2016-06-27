""" Test cases for the feature_identification.py module that provides 2016-era
control for wasatch photonics spectrometers and dev_list.
"""

import sys
import pytest
import logging
log = logging.getLogger(__name__)

strm = logging.StreamHandler(sys.stdout)
log.addHandler(strm)


class TestFeatureIdentification():

    @pytest.fixture
    def dev_list(self):
        from wasatchusb import feature_identification
        dev_list = feature_identification.ListDevices()
        return dev_list

    def test_list_no_dev_list(self, dev_list):
        log.critical("Make sure no dev_list are connected")

        result = dev_list.get_all()
        assert len(result) == 0

    def test_list_single_device(self, dev_list):
        log.critical("Make sure only one device connected")

        result = dev_list.get_all()
        assert len(result) == 1

    def test_list_device_is_fx2(self, dev_list):
        log.critical("Make sure only FX2 0x1000 is connected")

        result = dev_list.get_all()
        assert len(result) == 1
        assert result[0][0] == "0x24aa"
        assert result[0][1] == "0x1000"

    def test_list_device_is_ingaas(self, dev_list):
        log.critical("Make sure only ingaas 0x2000 is connected")

        result = dev_list.get_all()
        assert len(result) == 1
        assert result[0][0] == "0x24aa"
        assert result[0][1] == "0x2000"

    def test_list_device_is_arm(self, dev_list):
        log.critical("Make sure only arm 0x4000 is connected")

        result = dev_list.get_all()
        assert len(result) == 1
        assert result[0][0] == "0x24aa"
        assert result[0][1] == "0x4000"

    def test_connect_arm_device_close_device(self):
        log.critical("Expect an ARM device connected")

        from wasatchusb import feature_identification
        device = feature_identification.Device(pid=0x4000)
        result = device.connect()
        assert result is True

        result = device.disconnect()
        assert result is True


    def test_connect_ingaas_device_close_device(self):
        log.critical("Expect an FX2 device connected")

        from wasatchusb import feature_identification
        device = feature_identification.Device(pid=0x2000)
        result = device.connect()
        assert result is True

        result = device.disconnect()
        assert result is True


    def test_connect_device_close_device(self):
        log.critical("Expect an FX2 device connected")

        from wasatchusb import feature_identification
        device = feature_identification.Device()
        result = device.connect()
        assert result is True

        result = device.disconnect()
        assert result is True

    def test_get_ingaas_model_number(self, ingaas_device):

        model_number = ingaas_device.get_model_number()
        assert model_number == "1064M"

    def test_get_model_number(self, device):

        model_number = device.get_model_number()
        assert model_number == "785IOC"

    def test_get_arm_model_number(self, arm_device):

        model_number = arm_device.get_model_number()
        assert model_number == "785LC"

    def test_get_arm_calibration(self, arm_device):

        cal_coeff0 = arm_device.get_calibration("C0")
        cal_coeff0 = "%0.4f" % cal_coeff0
        assert cal_coeff0 == "1.2345"

        cal_coeff1 = arm_device.get_calibration("C1")
        cal_coeff1 = "%0.4f" % cal_coeff1
        assert cal_coeff1 == "2.3456"

        cal_coeff1 = arm_device.get_calibration("C2")
        cal_coeff1 = "%0.4f" % cal_coeff1
        assert cal_coeff1 == "3.4567"

        cal_coeff2 = arm_device.get_calibration("C3")
        cal_coeff2 = "%0.4f" % cal_coeff2
        assert cal_coeff2 == "4.5678"

    def test_get_calibration(self, ingaas_device):

        cal_coeff0 = ingaas_device.get_calibration("C0")
        assert cal_coeff0 == "1234.5"



    @pytest.fixture
    def device(self, pid=0x1000):
        from wasatchusb import feature_identification
        device = feature_identification.Device(pid=pid)
        result = device.connect()
        assert result is True
        return device

    @pytest.fixture
    def ingaas_device(self, pid=0x2000):
        return self.device(pid=pid)

    @pytest.fixture
    def arm_device(self, pid=0x4000):
        return self.device(pid=pid)

    def test_get_serial_number(self, device):
        serial_number = device.get_serial_number()
        assert serial_number == "S-00146"


    def test_get_integration_time(self, device):
        assert device.get_integration_time() == 0

    def test_get_gain(self, device):
        assert device.get_ccd_gain() == 1.296875

    def test_get_sensor_line_length(self, device):
        assert device.get_sensor_line_length() == 1024

    def test_get_ingaas_sensor_line_length(self, ingaas_device):
        assert ingaas_device.get_sensor_line_length() == 512

    def test_get_laser_availability(self, device):
        assert device.get_laser_availability() == 0

    def test_get_standard_software_code(self, device):
        result = device.get_standard_software_code()
        assert result == "10.0.0.0"

    def test_get_fpga_revision(self, ingaas_device):
        result = ingaas_device.get_fpga_revision()
        assert result == "008-003"


    def test_get_single_line_of_data(self, device):
        result = device.get_line()
        assert len(result) == 1024
        assert min(result) >= 10
        assert max(result) <= 65535

        average = sum(result) / len(result)
        assert average >= 20


    def test_get_ingaas_single_line_of_data(self, ingaas_device):
        result = ingaas_device.get_line()
        assert len(result) == 512
        assert min(result) >= 10
        assert max(result) <= 65535

        average = sum(result) / len(result)
        assert average >= 20

    def test_ingaas_pid_2000_set_integration_time(self, ingaas_device):
        # device defaults to 1 on power up
        assert ingaas_device.get_integration_time() == 1
        ingaas_device.set_integration_time(100)
        assert ingaas_device.get_integration_time() == 100

    def test_get_arm_single_line_of_data(self, arm_device):
        result = arm_device.get_line()
        assert len(result) == 1024
        assert min(result) >= 10
        assert max(result) <= 65535

        average = sum(result) / len(result)
        assert average >= 20

    def test_get_arm_integration_time(self, arm_device):
        assert arm_device.get_integration_time() == 0

    def test_arm_pid_4000_set_integration_time(self, arm_device):
        # device defaults to 0 on power up
        #assert arm_device.get_integration_time() == 0
        arm_device.set_integration_time(100)
        assert arm_device.get_integration_time() == 100
