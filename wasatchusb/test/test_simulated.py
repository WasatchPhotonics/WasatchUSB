""" Tests for the WasatchUSB simulated USB camera object.

This is not real life, this is a device that can be configured to return
any type of data desired.

"""

import unittest
import time

from wasatchusb.camera import SimulatedUSB
from wasatchusb.camera import RealisticSimulatedUSB

class Test(unittest.TestCase):
    
    def setUp(self):
        self.vid = 0x24aa
        self.pid = 0x0001

    def test_simulated_assign(self):
        
        sim = SimulatedUSB()

        # This is the break in functionality in the api. If you attempt
        # to connect to a simulation device before assigning a type, it
        # throws a valueerror exception.
        self.assertRaises(ValueError, sim.connect)
        self.assertRaises(ValueError, sim.disconnect)
       
        # Specify an invalid type, throw an error
        self.assertRaises(ValueError, sim.assign, "KnownInvalid")

        # Now that the type assignment has completed, connect will pass
        self.assertTrue(sim.assign("Stroker785L"))
        self.assertTrue(sim.connect())

    def test_connect_reconnect_disconnect(self):
        sim = SimulatedUSB()
        # Connect ok
        self.assertTrue(sim.assign("Stroker785L"))
        self.assertTrue(sim.connect())

        # Re-connect raises typeerror
        self.assertRaises(TypeError, sim.connect)

        # disconnect ok
        self.assertTrue(sim.disconnect())

        # re-disconnect raises typeerror
        self.assertRaises(TypeError, sim.disconnect)
   
    def test_get_line_of_data(self):
        # Create a device with 1024 simulated pixels
        sim = SimulatedUSB()
        self.assertRaises(ValueError, sim.get_line_pixel)

        self.assertTrue(sim.assign("Stroker785L"))
        self.assertEqual(sim.pixel_count, 1024)
        pixel_data = sim.get_line_pixel()
        self.assertEqual(len(pixel_data), 1024)
        self.assertEqual(pixel_data[0], 0)
        self.assertEqual(pixel_data[1023], 1023)

        # Check a device with 2048 pixels
        sim = SimulatedUSB()
        self.assertTrue(sim.assign("Stroker785M"))
        self.assertEqual(sim.pixel_count, 2048)
        pixel_data = sim.get_line_pixel()
        self.assertEqual(len(pixel_data), 2048)
        self.assertEqual(pixel_data[0], 0)
        self.assertEqual(pixel_data[2047], 2047)

    def test_wavenumber_conversion(self):
        # Set some default coefficients, make sure the returned
        # wavenumber conversion is accurate
        sim = SimulatedUSB()
        self.assertRaises(ValueError, sim.get_line_wavenumber)

        self.assertTrue(sim.assign("Stroker785L"))
        self.assertEqual(sim.pixel_count, 1024)
        wavenum_axis, intensity_data = sim.get_line_wavenumber()
        self.assertEqual(len(intensity_data), 1024)
        self.assertEqual(len(wavenum_axis), 1024)
  
        first_conv = "164.33"
        last_conv = "836.76"
        self.assertEqual("%05.2f" % wavenum_axis[0], first_conv)
        self.assertEqual("%05.2f" % wavenum_axis[-1], last_conv)
        self.assertEqual(intensity_data[0], 0)
        self.assertEqual(intensity_data[1023], 1023)

    def test_coefficient_updates(self):
        sim = SimulatedUSB()

        coeff_dict = {'C0': '7.25405E+02',
                      'C1': '1.43880E-01',
                      'C2': '7.16617E-06',
                      'C3': '-8.68137E-09'
                     }

        # Raises error when trying to update without assignment
        self.assertRaises(ValueError, sim.new_coefficients, coeff_dict)

        self.assertTrue(sim.assign("Stroker785M"))

        # Assign new coefficients
        self.assertTrue(sim.new_coefficients(coeff_dict))

        wavenum_axis, intensity_data = sim.get_line_wavenumber()

        first_conv = "-1046.55"
        last_conv = "2487.62"
        self.assertEqual("%05.2f" % wavenum_axis[0], first_conv)
        self.assertEqual("%05.2f" % wavenum_axis[-1], last_conv)
        self.assertEqual(intensity_data[0], 0)
        self.assertEqual(intensity_data[2047], 2047)

    def test_simulated_integration_times(self):
        # Create a regular simulated device, trigger a long integration,
        # expect it to return instantly
        sim = SimulatedUSB()
        self.assertTrue(sim.assign("Stroker785L"))
        self.assertTrue(sim.set_integration_time(3000))

        start_time = time.time()
        pixel_data = sim.get_line_pixel()
        end_time = time.time()

        self.assertLess(end_time - start_time, 1)

    def test_realistic_integration_times(self):
        # Create a sleep-enabled simulated device, expect it to return
        # sometime 
        rel = RealisticSimulatedUSB()
        self.assertTrue(rel.assign("Stroker785L"))
        self.assertTrue(rel.set_integration_time(3000))
         
        start_time = time.time()
        pixel_data = rel.get_line_pixel()
        end_time = time.time()

        self.assertLess(end_time - start_time, 3.1)
        self.assertGreater(end_time - start_time, 3)

if __name__ == "__main__":
    unittest.main()
