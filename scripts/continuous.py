""" Bare bones script to connect to a Wasatch Photonics device that
supports the stroker series protocol. Will print version information of
any device connected.  communication for devices from Wasatch Photonics.
Stroker in this case is an homage to automotive performance:
https://en.wikipedia.org/wiki/Stroker_kit
"""

import sys
import logging
log = logging.getLogger()
strm = logging.StreamHandler(sys.stderr)
log.addHandler(strm)
log.setLevel(logging.WARN)

graph_available = True
try:
    from diagram import DGWrapper
except ImportError as exc:
    graph_available = False
    log.warn("No diagram module - lineplots disabled.")
    log.warn("See: https://github.com/WasatchPhotonics/diagram")
    log.warn("Exception: %s", exc)

from wasatchusb import stroker_protocol, feature_identification


def print_device():
    """ Connect to the first discovered stroker protocol or feature 
    identification device. To diagnose this functionality individually,
    use the scripts/featureid.py and scripts/stroker.py files along with
    the respective tests/ cases.
    file.
    """

    dev_list = stroker_protocol.ListDevices()
    result = dev_list.get_all()
    fid_device = 0
    if result == []:
        log.warn("No stroker protocol device")

    	dev_list = feature_identification.ListDevices()
    	result = dev_list.get_all()
	fid_device = 1
    	if result == []:
            print "No feature identification protocol device"
	    sys.exit(1)
        

    dev_count = 0
    for item in dev_list.get_all():
        print "Device: %s      VID: %s PID: %s" \
               % (dev_count, item[0], item[1])
        dev_count += 1

    last_device = dev_list.get_all()[-1]
    last_pid = int(last_device[1], 16)

    if fid_device:
        device = feature_identification.Device(pid=last_pid)
    
    else:
        device = stroker_protocol.StrokerProtocolDevice(pid=last_pid)
    device.connect()
    print "Serial:        %s" % device.get_serial_number()
    print "SWCode:        %s" % device.get_standard_software_code()
    print "FPGARev:       %s" % device.get_fpga_revision()
    print "Gain:          %s" % device.get_ccd_gain()
    print "Int Time:      %s" % device.get_integration_time()

    return device

def print_data(device):

    device.set_integration_time(100)

    max_lines = 2000
    for line in range(max_lines):
        data = device.get_line()

        points = []
        values = []
        subsample_size = len(data) / 72
        for item in data[::subsample_size]:
            points.append(float(item))
            values.append(None)

	if graph_available:
            gram = DGWrapper(data=[points, values])
            gram.show()

            # Move cursor 11 lines up
            print '\x1b[11A'

	else:
            avg_data =  sum(data) / len(data)
            print "Min: %s Max: %s Avg: %s" \
                  % (min(data), max(data), avg_data)
	



if __name__ == "__main__":
    device = print_device()
    print_data(device)
