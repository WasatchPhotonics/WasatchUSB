""" camera - CameraUSB and SimulatedUSB devices for Wasatch Photonics.
"""
import usb
import numpy

class SimulatedUSB(object):
    """ Provide a simulation interface designed to mock Wasatch
    Photonics FX2, ARM, FX3 line scan cameras.
    """
    def __init__(self):
        self._assign = None

    def assign(self, assign_type):
        """ If assignable type matches, permit the rest of the
        simulation functions.
        """
        if assign_type == "Stroker785L":
            self._assign = assign_type
        
        if self._assign is None:
            raise(ValueError, "Unknown device type")

        return True

    def connect(self, vid=0x24aa, pid=0x0005):    
        """ Connect to the device assigned, regardless of the vid/pid.
        """
        self.unassigned()
        self._vid = vid
        self._pid = pid
        return True

    def unassigned(self):
        """ Throw an exception to enforce the user to set a device
        assignment before usage.
        """
        if self._assign is None:
            raise(ValueError, "Device is unassigned")


class CameraUSB(object):
    """ Communicate with a Wasatch Photonics Stroker ARM USB board
    according to the specification found in:
    Wasatch_Raman_USB_Interface_Specification - 042314.doc."""
    def __init__(self):
        #print "Start of CameraUSB object"
        self._device = None

        # setConfiguration and claim interface are only necessary when
        # doing bulk read. Track local state and only set and claim on
        # first attempt to bulk read.
        self._bulk_enabled = False

    def connect(self, vid, pid):
        for bus in usb.busses():
            for dev in bus.devices:
                if dev.idVendor == vid and dev.idProduct == pid:
                    self._device = dev.open() 

        if self._device is None:
            #print "Can't open device VID:%s PID:%s" % (vid, pid)
            return False

        return True
           
    def disconnect(self):
        """ Only attempt to release the interface if already
        attached. If you don't attempt to disconnect ever, it will throw
        Exception usb.core.USBError: USBError(19, 'No such device (it
        may have been disconnected)') When the program exits."""

        if self._bulk_enabled:
            result = self._device.releaseInterface()
            self._bulk_enabled = False

        return True
    
    def get_sw_code(self):
           
        DEVICE2HOST = 0xC0
        VR_GET_CODE_REVISION = 0xC0
        TIMEOUT = 1000
        od = self._device 
        buffer_size = 5
        result = od.controlMsg(DEVICE2HOST, 
                               VR_GET_CODE_REVISION,
                               buffer_size, 0, 0, TIMEOUT)
        
        ARMVersion = result
        arm_version = '{0:}{1:}{2:}{3:}{4:}'.format(chr(ARMVersion[0]), 
                        chr(ARMVersion[1]),chr(ARMVersion[2]), 
                        chr(ARMVersion[3]), chr(ARMVersion[4]))
        #print "ARM Software version: %s" % arm_version
        return 1, arm_version 
                
       
    def get_fpga_code(self):
        DEVICE2HOST = 0xC0
        CMD_INFO = 0xb4
        TIMEOUT = 1000
        od = self._device
        result = od.controlMsg(DEVICE2HOST, 
                               CMD_INFO,
                               7, 0, 0, TIMEOUT)
        curr_code = "".join(map(chr, result))
        #print "FPGA version: %s" % curr_code
        return 1, curr_code

    def get_line(self):
        HOST2DEVICE = 0x40
        IN2HOST1_EP = 0x82
        CMD_GET_IMAGE = 0xad
        ZEROS = '\x00' * 8
        TIMEOUT = 1000

        if self._bulk_enabled == False:
            self._device.setConfiguration(1)
            self._device.claimInterface(0)
            self._bulk_enabled = True

        zero_data = numpy.linspace(0,0,1024)
       
        # Trigger the command to readout from the CCD 
        waitti = self._device.controlMsg(HOST2DEVICE, CMD_GET_IMAGE,
                                         ZEROS, 1, 0, TIMEOUT)

        data = []
        block = self._device.bulkRead(IN2HOST1_EP, 2048, TIMEOUT)
        data.extend(block)

        # Unpack that data into a list
        data = [i + 256 * j for i, j in zip(data[::2], data[1::2])]
    
        return 1, data

