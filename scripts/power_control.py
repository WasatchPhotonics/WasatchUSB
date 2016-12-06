""" power_control - cycle the power of various devices connected to a
web power switch.
"""

import sys, time, random
import logging
import argparse
import requests

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
frmt = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
strm = logging.StreamHandler(sys.stdout)
strm.setFormatter(frmt)
log.addHandler(strm)

import signal
def signal_handler(signal, frame):
        log.critical('You pressed Ctrl+C!')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

class SimulatorApplication(object):
    """ Create the window with the graphs, setup communication based on
    the specified device.
    """
    def __init__(self):
        super(SimulatorApplication, self).__init__()
        log.debug("startup")
        self.parser = self.create_parser()
        self.args = None
        self.filename = "dash/assets/example_data/simulated_device.ini"

    def parse_args(self, argv):
        """ Handle any bad arguments, then set defaults.
        """
        log.debug("Process args: %s", argv)
        self.args = self.parser.parse_args(argv)

        return self.args

    def create_parser(self):
        """ Create the parser with arguments specific to this
        application.
        """
        desc = "Toggle ini file values"
        parser = argparse.ArgumentParser(description=desc)

        help_str = "Automatically terminate the program for testing"
        parser.add_argument("-t", "--testing", action="store_true",
                            help=help_str)

        iteration_str = "Specify an iteration count"
        parser.add_argument("-i", "--iterations", type=int,
                            default=1, help=iteration_str)

        delay_str = "Specify an delay in seconds between operations"
        parser.add_argument("-d", "--delay", type=int,
                            default=1, help=delay_str)

        delay_str = "Specify all OFF or ON"
        parser.add_argument("-m", "--mode", type=str,
                            default="OFF", help=delay_str)

        return parser


    def run(self):
        """ Perform random application functions based on the command
        line inputs.
        """
        self.devices = [1, 2, 3, 4, 5, 6, 7, 8]
        if self.args.mode == "ON":
            self.set_all("ON")

        elif self.args.mode == "OFF":
            self.set_all("OFF")

        else:
            self.devices = [1, 2, 3, 4, 5, 6, 7, 8]
            self.set_all("OFF")
            self.cycle_group(self.args.iterations, self.args.delay)
        self.closeEvent()

    def set_all(self, status="OFF"):
        for count in self.devices:
            log.info("Set %s to %s", count, status)
            self.send(count, status)
            time.sleep(0.1)

    def send(self, index, string):
        prefix = 'http://admin:81265889@10.0.0.90/outlet?'
        cmd = "%s%s=%s" % (prefix, index, string)
        result = requests.get(cmd)


    def cycle_group(self, iterations, delay):
        """ For the number of iterations, pick a random relay, toggle
        it's status, wait, then repeat.
        """
        delays = [1, 10, 30, 60, 120]
        for count in range(iterations):
            outlet = random.choice(self.devices)

            mode = random.choice(["OFF", "ON"])

            delay = random.choice(delays)

            log.info("Set %s to %s, wait: %s", outlet, mode, delay)
            self.send(outlet, mode)

            time.sleep(delay)



    def closeEvent(self):
        """ catch the exit signal from the control application, and
        call qapplication Quit. This will prevent hangs on exit.
        """
        log.debug("Application quit")
        #self.main_logger.close()




def main(argv=None):
    """ main calls the wrapper code around the application objects with
    as little framework as possible. See:
    https://groups.google.com/d/msg/comp.lang.python/j_tFS3uUFBY/\
        ciA7xQMe6TMJ
    """
    argv = argv[1:]
    log.debug("Arguments: %s", argv)

    exit_code = 0
    try:
        go_app = SimulatorApplication()
        go_app.parse_args(argv)
        go_app.run()

    except SystemExit, exc:
        exit_code = exc.code

    return exit_code

if __name__ == "__main__":
    sys.exit(main(sys.argv))
