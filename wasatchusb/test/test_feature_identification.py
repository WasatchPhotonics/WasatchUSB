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
        assert result is not None


