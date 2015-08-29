""" camera - CameraUSB and SimulatedUSB devices for Wasatch Photonics.
"""
import usb
import time
import numpy

class SimulatedUSB(object):
    """ Provide a simulation interface designed to mock Wasatch
    Photonics FX2, ARM, FX3 line scan cameras.
    """
    def __init__(self):
        self._assign = None
        self.is_connected = False
        self.vid = None
        self.pid = None

    def assign(self, assign_type):
        """ If assignable type matches, permit the rest of the
        simulation functions.
        """
        self.linearity_coefficient_c0 = 795.259
        self.linearity_coefficient_c1 = 4.65771e-02
        self.linearity_coefficient_c2 = -2.53654e-06
        self.linearity_coefficient_c3 = -6.00391e-11
        self.source_wavelength = 785.0

        if assign_type == "Stroker785L":
            self.pixel_count = 1024
            self._assign = assign_type
            self.serial_number = assign_type
            self.integration_time = 10
       
        elif assign_type == "Stroker785M":
            self.pixel_count = 2048
            self._assign = assign_type
            self.serial_number = assign_type
 
        if self._assign is None:
            raise(ValueError, "Unknown device type")

        return True

    def get_line_wavenumber(self):
        """ Run get_line_pixel, then transform the data into wavelength
        and ultimately wavenumber mode.
        """
        self.check_unassigned()

        px = self.get_line_pixel()

        wavel_axis = self.translate_wavelength()

        wavenum_data = []
        source_wavelength = self.source_wavelength

        for wl_x in wavel_axis:
            new_x = 1e7 / source_wavelength - 1e7 / wl_x
            wavenum_data.append(new_x)

        return wavenum_data, px

    def new_coefficients(self, new_dict):
        """ Accept a dict of c0-c3, assign to local variables
        """
        self.check_unassigned()

        self.linearity_coefficient_c0 = new_dict['C0']
        self.linearity_coefficient_c1 = new_dict['C1']
        self.linearity_coefficient_c2 = new_dict['C2']
        self.linearity_coefficient_c3 = new_dict['C3']
        return True

    def translate_wavelength(self):
        """ Using the supplied calibration coefficients, apply the
        polynomial transformation. Return the axis of pixel_count in
        length.
        """
            
        c0 = float(self.linearity_coefficient_c0)
        c1 = float(self.linearity_coefficient_c1)
        c2 = float(self.linearity_coefficient_c2)
        c3 = float(self.linearity_coefficient_c3)

        wl_data = []
        #print "Translate wavelength with: %s, %s, %s, %s" \
            #% (c0, c1, c2, c3)

        for x in range(self.pixel_count):
            new_x = c0 + (c1 * x) + (c2 * x * x) + (c3 * x * x * x)
            wl_data.append(new_x)

        return wl_data


    def get_line_pixel(self):
        """ Return a test pattern of data over the range specified
        during the assignment pixel count.
        """
        self.check_unassigned()

        px = self.pixel_count
        pixel_data = numpy.linspace(0, px-1, px)
        return pixel_data

    def connect(self, vid=0x24aa, pid=0x0005):    
        """ Connect to the device assigned, regardless of the vid/pid.
        """
        self.check_unassigned()

        if self.is_connected:
            raise(TypeError, "Already conected")

        self.vid = vid
        self.pid = pid
        self.is_connected = True
        return True

    def disconnect(self):
        """ Reset all variables, keep device assignment.
        """
        self.check_unassigned()
        
        if not self.is_connected:
            raise(TypeError, "Already disconnected")
    
        self.is_connected = False
        self.vid = None
        self.pid = None
        return True

    def check_unassigned(self):
        """ Throw an exception to enforce the user to set a device
        assignment before usage.
        """
        if self._assign is None:
            raise(ValueError, "Device is check_unassigned")

    def set_integration_time(self, in_value):
        self.integration_time = in_value
        return True

class RealisticSimulatedUSB(SimulatedUSB):
    """ Same simualted data and other interface concepts, along with
    delays of integration time for long acquisitions. 
    """
    def __init__(self):
        super(RealisticSimulatedUSB, self).__init__()
        
    def get_line_pixel(self):
        """ Get the simulated data immediately, then wait the required
        time.
        """
        pixel_data = super(RealisticSimulatedUSB, self).get_line_pixel()
        print "Waiting: %s" % self.integration_time
        time.sleep(self.integration_time/1000)
        return pixel_data

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

