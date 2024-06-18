import argparse
import json
import logging
import math
import random
import time
from operator import truediv

from flask import Flask, render_template
from flask_sock import Sock

from controllers.crazyflieController import CrazyflieController
from controllers.utils.utils import FlightZone

logger = logging.getLogger(__name__)

app = Flask(__name__)
sock = Sock(app)

# drone_uri = 'radio://0/80/2M/E7E7E7E7E0'
# flight_zone = FlightZone(2.0, 3.0, 1.25, 0.3)
# cf = CrazyflieController({drone_uri}, flight_zone, drone_uri)

goal_reached = False


class Destination:
    def __init__(self, name, easy_location, hard_location, default_location):
        self.name = name
        self.easy_location = easy_location
        self.hard_location = hard_location
        self.default_location = default_location


# Destinations have a name, easy_location, hard_location
destinations = [
    Destination("A", [0.60, 0.3, .5], [0.6, -0.3, .5], [1., 0, 0.5]),
    Destination("D", [0.3, -0.6, .5], [-0.3, -0.6, .5], [0, -1.0, .5]),
    Destination("B", [-0.6, 0.60, .4], [0.3, 0.6, .5], [0, 1., .5]),
    Destination("C", [-0.6, -0.3, .5], [-0.6, 0.3, .5], [-1., 0.0, .5])
]

score = 0  # participant's total score

num_trials = 10
experiment_trial = 0

CONDITION_FAIL = 0
CONDITION_CONTROL = 1


def is_close_to_point():
    global target_position
    global destination_index
    global goal_reached
    global score

    drone_position = cf.positions[drone_uri]
    dx = drone_position[0] - target_position[0]
    dy = drone_position[1] - target_position[1]
    dz = drone_position[2] - target_position[2]
    distance = math.sqrt(dx**2 + dy**2 + dz**2)

    if distance < threshold:
        if target_position == destinations[destination_index].hard_location:
            score += 15
            logging.info("score 15\n " +
                         str(destinations[destination_index].name))
        elif target_position == destinations[destination_index].default_location:
            score += 10
            logging.info("default score 10\n " +
                         str(destinations[destination_index].name))
        elif target_position == destinations[destination_index].easy_location:
            score += 5
            logging.info("score 5\n " +
                         str(destinations[destination_index].name))

        if len(destinations) - 1 == destination_index:
            goal_reached = True
        elif destination_index < len(destinations) - 1:
            destination_index += 1

        return True
    else:
        return False


def move_home():
    drone_position = cf.positions[drone_uri]
    drone_position[0] = -(drone_position[0])
    drone_position[1] = -(drone_position[1])
    drone_position[2] = 0

    cf.swarm_move({drone_uri: drone_position}, None, 2, True)


def recieve_data(sock):
    data = sock.receive()

    if isinstance(data, str):
        json_data = json.loads(data)

        if 'action' in json_data:
            return json_data
        else:
            raise Exception("Recieved data is not in expected format!")
    else:
        raise Exception("Recieved data is not string!")


@app.route('/')
def index():
    return render_template('index.html')


@sock.route('/action')
def echo(sock):
    global score
    global goal_reached

    sock.send(json.dumps({
        'action': 'welcome',
        'message': 'Welcome! This is your first flight. Please fly to <strong>checkpoint {}</strong> and hover above the blue ring'.format(destinations[destination_index].name)
    }))

    move_distance = 0.10

    condition = CONDITION_CONTROL

    start_time = time.time()
    start_time_action = time.time()

    while experiment_trials < num_trials:
        data = recieve_data(sock)

        # Log movement
        logger.info(f"{data}")

        action = data['action']

        if action == 'forward':
            cf.swarm_move({drone_uri: [move_distance, 0, 0]},
                          None,
                          2.,
                          True)
        elif action == 'back':
            cf.swarm_move({drone_uri: [-move_distance, 0, 0]},
                          None,
                          2.,
                          True)
        elif action == 'left':
            cf.swarm_move({drone_uri: [0, move_distance, 0]},
                          None,
                          2.,
                          True)
        elif action == 'right':
            cf.swarm_move({drone_uri: [0, -move_distance, 0]},
                          None,
                          2.,
                          True)
        elif action == 'take off':
            cf.swarm_take_off()
        elif action == 'land':
            cf.swarm_land()

        # CHECK IF GOAL IS REACHED

        if is_close_to_point():
            sock.send(json.dumps({'action': 'score', 'value': score}))
            print("Hoop completed!")
            end_time = time.time()
            elapsed_time = end_time - start_time

            logger.info("Elapsed time: {:.2f} seconds".format(elapsed_time))

            if goal_reached:
                sock.send(json.dumps({'action': 'finish',
                                      'message': 'Destination reached! Well done! Going back to homebase.'}))
                time.sleep(2)

                if experiment_trial == 0:
                    sock.send(json.dumps({
                        'action': 'goal',
                        'message': 'You have completed the first part of this experiment.<br/> You have earned <strong>' +
                        str(score) +
                        '</strong> SEK in this flight session! You can now do the first part of the survey. When you are done with the first part of the survey, the supervisor will change your drone.'
                    }))

                    print('...landing, please wait')
                    move_home()
                    cf.swarm_land()

                    break
                elif experiment_trial == num_trials - 1:
                    sock.send(json.dumps({
                        'action': 'finish',
                        'message': 'Last part of experiment is now finished. You have earned <strong>' +
                        str(score) +
                        '</strong> SEK this flight session! Please finish the survey.'
                    }))

                    print('...landing, please wait')
                    move_home()
                    cf.swarm_land()

                    break
                else:
                    break

            if destination_index == 1:
                sock.send(json.dumps({
                    'action': 'goal',
                    'message': 'Destination reached! First flight finished! ... Going back to home base.'
                }))

                time.sleep(3)
                move_home()
            else:
                sock.send(json.dumps({
                    'action': 'goal',
                    'message': 'Destination reached! ... Going back to home base. '
                }))

                time.sleep(3)
                move_home()

            cf.swarm_land()
            start_time = time.time()

            continue


if __name__ == '__main__':
    logging.basicConfig(filename='movements.log',
                        filemode='a',
                        encoding='utf-8',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.INFO)

    parser = argpase.ArgumentParser(
        description="Runs the risky drones experiment")

    parser.add_argument('-c',
                        '--condition',
                        required=True,
                        choices=['control', 'fail'],
                        help='Which experimental condition to run')

    parser.add_argument('-i',
                        '--id',
                        help='The id of the current participant')

    app.config['condition'] = parser.condition
    app.config['id'] = parser.id

    app.run()
