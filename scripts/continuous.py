#!/usr/bin/env python2
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
log.setLevel(logging.INFO)

graph_available = True
try:
    from diagram import DGWrapper, DOption, Point
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
    device.set_ccd_tec_setpoint(10.0)
    device.set_ccd_tec_enable(1)

    temp_points = []
    temp_values = []

    max_lines = 20
    for line in range(max_lines):
        data = device.get_line()
        tempc = device.get_ccd_temperature()
        temp_points.append(tempc)
        temp_values.append(len(temp_points))
        if len(temp_points) > 10:
            temp_points = temp_points[1:]
            temp_values = temp_values[1:]

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
            avg_data =  sum(data) / len(data)
            print "Min: %s Max: %s Avg: %s" \
                  % (min(data), max(data), avg_data)



        temp_options = DOption()
        temp_options.mode = "g"
        temp_options.palette = "blue"
        temp_options.size = Point([0, 3])
        temp_gram = DGWrapper(dg_option=temp_options,
                data=[temp_points, temp_values])
        temp_gram.show()

        print "Temperature: %2.3f" % tempc

        # Move the cursor back up to overwrite the graph
        print '\x1b[15A'

    # Move the cursor back down to where the command prompt should be
    print '\x1b[15B'


if __name__ == "__main__":
    device = print_device()
    print_data(device)
