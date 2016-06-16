""" Bare bones script to connect to a Wasatch Photonics device that
supports the feature identification protocol. Will print version
information of any device connected.
"""

import sys
import logging
log = logging.getLogger()
strm = logging.StreamHandler(sys.stderr)
log.addHandler(strm)
log.setLevel(logging.WARN)

import wasatchusb
from wasatchusb import feature_identification

import argparse
from diagram import VerticalBarGraph
from diagram import Point

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
        print "Device: %s     VID: %s PID: %s" \
               % (dev_count, item[0], item[1])
        dev_count += 1

    last_device = dev_list.get_all()[-1]
    last_pid = int(last_device[1], 16)
    print "Connect to last device pid: %s" % last_pid

    device = feature_identification.Device(pid=last_pid)
    device.connect()
    print "Model:  %s" % device.get_model_number()
    print "Serial: %s" % device.get_serial_number()
    print "SWCode: %s" % device.get_standard_software_code()
    print "FPGARev: %s" % device.get_fpga_revision()
    print "Gain:     %s" % device.get_ccd_gain()
    print "Int Time: %s" % device.get_integration_time()
    print "Laser Avail: %s" % device.get_laser_availability()
    print "Sensor Length: %s" % device.get_sensor_line_length()

    device.set_integration_time(100)
    data = device.get_line()
    avg_data =  sum(data) / len(data)

    print ""
    print "Grab Data: %s pixels" % len(data)
    print "Min: %s Max: %s Avg: %s" \
            % (min(data), max(data), avg_data)

    step_size = len(data) / 80
    with open("ys.txt", "wb") as OUT_FILE:
        for y_item in data[0::step_size]:
            OUT_FILE.write("%s\n" % y_item)

    parser = argparse.ArgumentParser(
        description=(
            'Text mode diagrams using UTF-8 characters and fancy colors.'
        ),
        epilog="""fake""",
    )
    option = parser.parse_args()
    option.width = 0
    option.height = 0
    option.reverse = False
    option.input = "ys.txt"
    try:
        ostream = sys.stdout.buffer
    except AttributeError:
        ostream = sys.stdout
    option.batch = False
    option.function = None
    option.legend = True
    option.encoding = 'utf-8'
    option.color = True
    option.palette = "default"

    option.size = Point((option.width, option.height))

    engine = VerticalBarGraph(option.size, option)

    istream = open(option.input, 'r')
    engine.consume(istream, ostream, batch=option.batch)


if __name__ == "__main__":
    print_device()

