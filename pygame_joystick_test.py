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
        turn_rate = 60  # degrees
        joysticks = []

        run = True

        # keep track of 10 most recent inputs for smoothing of analog signal
        num_readings = 10
        vert_inputs = deque(maxlen=num_readings)
        hor_inputs = deque(maxlen=num_readings)
        yaw_inputs = deque(maxlen=num_readings)

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
                    logger.info("Quitting...")
                    run = False

                if cf.swarm_flying:
                    # player movement with analogue sticks

                    # TODO 2024-06-04: The amount of "available" velocity should
                    # be limited as the drone gets closer to the edges of the
                    # flight zone

                    hor_inputs.append(-joystick.get_axis(0))
                    vert_inputs.append(-joystick.get_axis(1))
                    yaw_inputs.append(-joystick.get_axis(2))

                    new_vert_vel = sum(vert_inputs) / len(vert_inputs)

                    if abs(new_vert_vel) < 0.05:
                        new_vert_vel = 0
                    logger.debug("Vert velocity: {}".format(new_vert_vel))

                    new_hor_vel = sum(hor_inputs) / len(hor_inputs)

                    if abs(new_hor_vel) < 0.05:
                        new_hor_vel = 0
                    logger.debug("Horiz velocity: {}".format(new_hor_vel))

                    # TODO 2024-06-05: After turning, the new "forward" is not taken
                    # into account, instead it uses the world definition of "forward"
                    new_yaw_rate = (sum(yaw_inputs) /
                                    len(yaw_inputs)) * turn_rate

                    if abs(new_yaw_rate) < 10:
                        new_yaw_rate = 0
                    logger.debug("Yaw rate: {}".format(new_yaw_rate))

                    cf.set_swarm_velocities(
                        {drone_uri: [new_vert_vel, new_hor_vel, 0]}, new_yaw_rate)

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
