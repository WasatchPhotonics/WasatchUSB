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

    def test_connect_device_close_device(self):
        log.critical("Expect an FX2 device connected")

        from wasatchusb import feature_identification
        device = feature_identification.Device()
        result = device.connect()
        assert result is True

        result = device.disconnect()
        assert result is True

    def test_get_model_number(self, device):

        model_number = device.get_model_number()
        assert model_number == "785IOC"

    @pytest.fixture
    def device(self):
        from wasatchusb import feature_identification
        device = feature_identification.Device()
        result = device.connect()
        assert result is True
        return device

    def test_get_serial_number(self, device):
        serial_number = device.get_serial_number()
        assert serial_number == "S-00146"


    def test_get_integration_time(self, device):
        integration_time = device.get_integration_time()
        assert integration_time == 10

    def test_get_sensor_line_length(self, device):
        assert device.get_sensor_line_length() == 1024

    def test_get_laser_availability(self, device):
        assert device.get_laser_availability() == 0

