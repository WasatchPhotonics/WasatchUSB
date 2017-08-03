""" Bare bones script to connect to a Wasatch Photonics device that
supports the ARM chipset with external triggering. Mimic the Dash
functionality of acquiring a single line internally triggered, set the
external trigger opcode, then wait until USB timeout for data on the
bulk endpoint.
"""

import sys, time
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

import wasatchusb
from wasatchusb import feature_identification


def print_device():
    """ Print the default set of data from the device. To diagnose these
    individually, see the wasatchusb/test/test_feature_identification.py
    file.
    """

    dev_list = feature_identification.ListDevices()
    result = dev_list.get_all()
    if result == []:
        print "No devices found!"
        sys.exit(1)

    dev_count = 0
    for item in dev_list.get_all():
        print "Device: %s      VID: %s PID: %s" \
               % (dev_count, item[0], item[1])
        dev_count += 1

    last_device = dev_list.get_all()[-1]
    last_pid = int(last_device[1], 16)

    device = feature_identification.Device(pid=last_pid)
    device.connect()
    print "Model:         %s" % device.get_model_number()
    print "Serial:        %s" % device.get_serial_number()
    print "SWCode:        %s" % device.get_standard_software_code()
    print "FPGARev:       %s" % device.get_fpga_revision()
    print "Gain:          %s" % device.get_ccd_gain()
    print "Int Time:      %s" % device.get_integration_time()
    print "Laser Avail:   %s" % device.get_laser_availability()
    print "Sensor Length: %s" % device.get_sensor_line_length()

    return device

def print_data(device):

    data = device.get_line()
    avg_data =  sum(data) / len(data)

    print ""
    points = []
    values = []
    subsample_size = len(data) / 72
    for item in data[::subsample_size]:
        points.append(float(item))
        values.append(None)

    if graph_available:
        gram = DGWrapper(data=[points, values])
        gram.show()

    else:
        print "Min: %s Max: %s Avg: %s" \
              % (min(data), max(data), avg_data)

if __name__ == "__main__":
    device = print_device()

    #device.set_integration_time(100)

    # Set internal trigger, get a line of data
    device.set_trigger_source(0)
    print_data(device)

    time.sleep(1)

    # Set external trigger, wait forever
    device.set_trigger_source(1)
    print_data(device)





