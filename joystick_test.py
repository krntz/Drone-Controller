import logging

from controller.utils.utils import FlightZone
from pyjoystick.sdl2 import Joystick, Key, run_event_loop

from controllers.crazyflieController import CrazyflieController

logger = logging.getLogger(__name__)

max_vel = 10  # m/s

drone_uri = 'radio://0/80/2M/E7E7E7E7E0'
flight_zone = FlightZone(2.0, 3.0, 1.25, 0.30)
cf = CrazyflieController({drone_uri}, flight_zone, drone_uri)


def print_add(joy):
    print('Added', joy)


def print_remove(joy):
    print('Removed', joy)


def key_received(key):
    if key.keytype == Key.BUTTON:
        if key.number == 0:
            if key.value == 1:
                if not cf.swarm_flying:
                    cf.swarm_take_off()
                else:
                    cf.swarm_land()
            else:
                pass
    elif key.keytype == Key.AXIS:
        if key.number in [0, 1, 2, 3]:
            vel = key.value * max_vel
            print('Axis {}: {} {}'.format(key.number, key.value, vel))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_event_loop(print_add, print_remove, key_received)
