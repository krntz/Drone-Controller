import logging
from collections import deque

import pygame

from controllers.crazyflieController import CrazyflieController
from controllers.utils.utils import FlightZone

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    max_vel = 10  # m/s

    drone_uri = 'radio://0/80/2M/E7E7E7E7E0'
    flight_zone = FlightZone(2.0, 3.0, 1.25, 0.30)

    with CrazyflieController({drone_uri}, flight_zone, drone_uri) as cf:
        pygame.init()
        pygame.joystick.init()
        clock = pygame.time.Clock()
        FPS = 60
        joysticks = []

        run = True

        # keep track of 10 most recent inputs for smoothing of analog signal
        num_readings = 10
        vert_inputs = deque(maxlen=num_readings)
        hor_inputs = deque(maxlen=num_readings)

        logger.info("Ready to go!")

        while run:
            clock.tick(FPS)

            for joystick in joysticks:
                if joystick.get_button(0):
                    if not cf.swarm_flying:
                        cf.swarm_take_off()
                    else:
                        cf.swarm_land()
                elif joystick.get_button(1):
                    print("Quitting...")
                    run = False

                if cf.swarm_flying:
                    # player movement with analogue sticks

                    # TODO 2024-06-04: The amount of "available" velocity should
                    # be limited as the drone gets closer to the edges of the
                    # flight zone

                    hor_inputs.append(-joystick.get_axis(0))
                    vert_inputs.append(-joystick.get_axis(1))

                    new_vert_vel = sum(vert_inputs) / len(vert_inputs)
                    print("Vert velocity: {}".format(new_vert_vel))
                    new_hor_vel = sum(hor_inputs) / len(hor_inputs)
                    print("Horiz velocity: {}".format(new_hor_vel))

                    cf.set_swarm_velocities(
                        {drone_uri: [new_vert_vel, new_hor_vel, 0]}, 0)

            for event in pygame.event.get():
                # event handler

                if event.type == pygame.JOYDEVICEADDED:
                    logger.info("Joystick added")
                    joy = pygame.joystick.Joystick(event.device_index)
                    joysticks.append(joy)

                if event.type == pygame.QUIT:
                    # quit program
                    run = False

        pygame.quit()
