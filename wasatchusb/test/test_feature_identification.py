""" Test cases for the feature_identification.py module that provides 2016-era
control for wasatch photonics spectrometers and devices.
"""

import sys
import logging
log = logging.getLogger(__name__)

strm = logging.StreamHandler(sys.stdout)
log.addHandler(strm)


class TestFeatureIdentification():
    def test_list_no_devices(self):
        log.critical("Make sure no devices are connected")

        from wasatchusb import feature_identification
        devices = feature_identification.ListDevices()
        result = devices.get_all()
        assert len(result) == 0

    def test_list_single_device(self):
        log.critical("Make sure only one device connected")

        from wasatchusb import feature_identification
        devices = feature_identification.ListDevices()
        result = devices.get_all()
        assert len(result) == 1
