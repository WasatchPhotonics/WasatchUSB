""" Tests for the WasatchUSB simulated USB camera object.

This is not real life, this is a device that can be configured to return
any type of data desired.

"""

import unittest

from wasatchusb.camera import SimulatedUSB

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
       
        # Specify an invalid type, throw an error
        self.assertRaises(ValueError, sim.assign, "KnownInvalid")

        # Now that the type assignment has completed, connect will pass
        self.assertTrue(sim.assign("Stroker785L"))
        self.assertTrue(sim.connect())

    def test_connect_reconnect_disconnect(self):
        sim = SimulatedUSB()
        # Connect ok

        # Re-connect raises typeerror

        # disconnect ok

        # re-disconnect raises typeerror
        self.assertRaises(sim.disconnect())
    

if __name__ == "__main__":
    unittest.main()
