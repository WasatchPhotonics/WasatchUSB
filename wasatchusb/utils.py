
import usb

class FindDevices(object):
    ''' List Wasatch Photonics devices found connected to the host OS.'''
    def __init__(self):
        #print "Start of find devices object"
        pass

    def get_serial(self, vid, pid):
        busses = usb.busses()
        for bus in busses:
            devices = bus.devices
            for dev in devices:
                if dev.idVendor == 0x24aa:
                    #print "  idVendor:",hex(dev.idVendor)
                    #print "  idProduct:",hex(dev.idProduct)

                    ld = dev.open()
                    local_serial = ld.getString(dev.iSerialNumber, 256)
                    return True, local_serial

        return False, "serial_failure" 
                
    def list_usb(self, vid=0x24aa):
        #print "Show vendor devices: %s" % vid

        device_list = []
        
        for bus in usb.busses():
            for device in bus.devices:
                # iSerialNumber in this context is position, not value.
                # see get_serial above for details
                if device.idVendor == vid:
                    result = hex(device.idVendor) + ":" + \
                             hex(device.idProduct) + ":" + \
                             hex(device.iSerialNumber) + " "
                    result = result.replace('0x', '')
                    result = result.replace('L', '')
                    device_list.append(result)

        return 1, device_list

