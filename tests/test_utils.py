""" wrapper functions for finding just Wasatch VID=0x24AA devices

Uses Phidgeter to place the device in a known power state so you don't
have to manually connect and disconnect the device.
"""

import unittest
import time
import logging
logger = logging.getLogger()
hdlr = logging.FileHandler('test_utils.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 

from phidgeter import relay
from wasatchusb.utils import FindDevices

class Test(unittest.TestCase):

    def setUp(self):
        self.relay = relay.Relay()
        self.fd = FindDevices()
        self.vid = 0x24aa
        self.pid = 0x0009

    def test_get_serial(self):
        self.ensure_all_off(self.relay)
        time.sleep(1)
        result, dev_list = self.fd.get_serial(self.vid, self.pid)
        self.assertFalse(result)
        self.assertEquals(dev_list, "serial_failure")

        # Assumes a wasatch camera is plugged into USB
        self.ensure_all_on(self.relay)
        time.sleep(10)

        # Get the device list manually
        result, dev_list = self.fd.get_serial(self.vid, self.pid)
        self.assertTrue(result)
        self.assertNotEqual(dev_list, "serial_failure")

        # Arbitrary requirement that serial number has to be at least
        # 3 chars
        self.assertTrue(len(dev_list) > 3)

    def test_list_usb(self):
        # With no devices powered, ensure the list is empty
        self.ensure_all_off(self.relay)
        time.sleep(1)
        result, usb_list = self.fd.list_usb()
        self.assertTrue(result)
        self.assertEqual(usb_list, []) 

        # Connect devices, ensure at least one is listed
        self.ensure_all_on(self.relay)
        # As of 2015-08-15 11:06 certain devices are not available on
        # the bus on odroid for way too long. Give them time to
        # initialize before trying to read the usb descriptor.
        # Sometimes even 20 seconds is not long enough.
        time.sleep(20)

        result, usb_list = self.fd.list_usb()
        print "List is: %s" % usb_list
        self.assertTrue(result)
        self.assertTrue(len(usb_list) == 1)
        self.assertTrue("24aa" in str(usb_list))

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
