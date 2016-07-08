""" Test cases for the camera.py module. These were built as a first
iteration for the BoardRoaster. You probably want the newer feature
identification wrappers and test cases, or maybe the stroker protocol
wrappers and test cases.
"""

import unittest
import time

import phidgeter
from phidgeter.relay import Relay
from wasatchusb.camera import CameraUSB
from wasatchusb.utils import FindDevices


class Test(unittest.TestCase):

    def setUp(self):
        # In real life, tests are on a variety of devices in different
        # power configurations. Turn on all the relays and assume one of
        # them has an attached wasatch photonics usb device
        self.phd_relay = Relay()
        self.ensure_all_off(self.phd_relay)
        time.sleep(1)
        self.ensure_all_on(self.phd_relay)

        self.on_delay = 20.1
        print "Wait %s seconds for device availability" % self.on_delay
        time.sleep(self.on_delay)

    def tearDown(self):
        self.ensure_all_off(self.phd_relay)

    def test_no_device_connection(self):
        # Devices are on from setup, turn off manually here and wait
        self.ensure_all_off(self.phd_relay)
        time.sleep(1)

        ud = CameraUSB()
        vid = 0x24aa
        pid = 0x0009
        result = ud.connect(vid, pid)
        self.assertFalse(result)

        fd = FindDevices()
        result, serial = fd.get_serial(vid, pid)
        self.assertFalse(result)
        self.assertTrue(ud.disconnect())

    def test_single_line_internal_trigger(self):
        ud = CameraUSB()
        vid = 0x24aa
        pid = 0x0009
        result = ud.connect(vid, pid)
        self.assertTrue(result, msg="Connection failure")

        result, pixel_data = ud.get_line()
        self.assertTrue(result)
        self.assertEquals(len(pixel_data), 1024)
        self.assertTrue(ud.disconnect())


    def test_get_device_firmware_revisions(self):
        ud = CameraUSB()
        vid = 0x24aa
        pid = 0x0009
        result = ud.connect(vid, pid)
        self.assertTrue(result, msg="Connection failure")

        result, sw_code = ud.get_sw_code()
        self.assertTrue(result)
        self.assertEquals(sw_code, '1.000')

        result, fpga_code = ud.get_fpga_code()
        self.assertTrue(result)
        self.assertEquals(fpga_code, '007-007')
        self.assertTrue(ud.disconnect())

    def ensure_all_off(self, relay):
        self.assertTrue(relay.zero_off())
        self.assertTrue(relay.one_off())
        self.assertTrue(relay.two_off())
        self.assertTrue(relay.three_off())
        return True

    def ensure_all_on(self, relay):
        self.assertTrue(relay.zero_on())
        self.assertTrue(relay.one_on())
        self.assertTrue(relay.two_on())
        self.assertTrue(relay.three_on())
        return True

if __name__ == "__main__":
    unittest.main()
