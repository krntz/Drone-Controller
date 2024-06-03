import logging

import pygame

from controllers.crazyflieController import CrazyflieController
from controllers.utils.utils import FlightZone

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    max_vel = 10  # m/s

    drone_uri = 'radio://0/80/2M/E7E7E7E7E0'
    flight_zone = FlightZone(2.0, 3.0, 1.25, 0.30)
    cf = CrazyflieController({drone_uri}, flight_zone, drone_uri)

    pygame.init()
    pygame.joystick.init()
    clock = pygame.time.Clock()
    FPS = 60
    joysticks = []

    run = True

    while run:
        # get the number of seconds since last loop
        dt = clock.tick(FPS) / 1000.0

        for joystick in joysticks:
            if joystick.get_button(0):
                if not cf.swarm_flying:
                    cf.swarm_take_off()
                else:
                    cf.swarm_land()
            elif joystick.get_button(1):
                print("Quitting...")
                run = False

            # player movement with analogue sticks

            horiz_move = joystick.get_axis(0)
            vert_move = joystick.get_axis(1)

            # new velocity is a percentage of the maximum velocity, scaled
            # by the number of seconds since the last tick

            # TODO 2024-06-03: Need calculate velocity for each axis and
            # then update them all together with set_velocities()

            if abs(vert_move) > 0.05:
                new_vert_vel = (vert_move * max_vel) * dt
                print("Vert velocity: {}".format(new_vert_vel))
                # y += vert_move * 5

            if abs(horiz_move) > 0.05:
                new_horiz_vel = (horiz_move * max_vel) * dt
                print("Horiz velocity: {}".format(new_horiz_vel))
                # x += horiz_move * 5

        for event in pygame.event.get():
            # event handler

            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                joysticks.append(joy)

            if event.type == pygame.QUIT:
                # quit program
                run = False

    pygame.quit()
    del cf
