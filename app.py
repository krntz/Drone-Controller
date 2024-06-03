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
logging.basicConfig(filename='movements.log',
                    filemode='a',
                    encoding='utf-8',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

app = Flask(__name__)
sock = Sock(app)

drone_uri = 'radio://0/80/2M/E7E7E7E7E0'
flight_zone = FlightZone(2.0, 3.0, 1.25, 0.3)
cf = CrazyflieController({drone_uri}, flight_zone, drone_uri)

goal_reached = False


class Destination:
    def __init__(self, name, easy_location, hard_location, default_location):
        self.name = name
        self.easy_location = easy_location
        self.hard_location = hard_location
        self.default_location = default_location


# Destinations have a name, easy_location, hard_location
destinations = [
    Destination(name="A",
                easy_location=[0.6, 0.3, 0.5],
                hard_location=[0.6, -0.3, 0.5],
                default_location=[1.0, 0.0, 0.5]),
    Destination(name="B",
                easy_location=[-0.6, 0.60, 0.4],
                hard_location=[0.3, 0.6, 0.5],
                default_location=[0.0, 1.0, 0.5]),
    Destination(name="C",
                easy_location=[-0.6, -0.3, 0.5],
                hard_location=[-0.6, 0.3, 0.5],
                default_location=[-1.0, 0.0, 0.5]),
    Destination(name="D",
                easy_location=[0.3, -0.6, 0.5],
                hard_location=[-0.3, -0.6, 0.5],
                default_location=[0.0, -1.0, 0.5])
]

random.shuffle(destinations)

target_position = destinations[0].default_location
destination_index = 0
threshold = 0.24
score = 0  # participant's total score
failing_instance = False
failing_counter = 0
drone2 = True


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


@app.route('/')
def index():
    return render_template('index.html')


@sock.route('/action')
def echo(sock):
    global score
    global goal_reached
    global destinations
    global failing_instance
    global threshold
    global failing_counter
    global destination_index
    global target_position

    sock.send(json.dumps({
        'action': 'welcome',
        'message': 'Welcome!  This is your first flight. Please fly to  <strong> checkpoint ' +
        str(destinations[destination_index].name) +
        '</strong> and hover above the blue ring'
    }))

    sock.send(json.dumps({
        'action': 'default',
        'destination_index': destination_index,
        'destination_name': destinations[destination_index].name
    }))

    start_time = time.time()
    start_time_action = time.time()

    while True:
        data = sock.receive()

        if isinstance(data, str):  # Data is usually a string...
            data = json.loads(data)  # ...so parse it into a dictionary

            if 'action' in data and data['action'] == 'select_location_choice':
                choice = data['choice']

                if choice == 'easy':
                    target_position = destinations[destination_index].easy_location
                else:  # 'hard'
                    target_position = destinations[destination_index].hard_location

                continue  # Skip the rest of the loop and start the next iteration

        # Check if score should be updated.

        if 'action' in data and data['action'] == 'score':
            score = 0
        action = data['action']

        if target_position == destinations[0].hard_location or target_position == destinations[
                1].hard_location or target_position == destinations[2].hard_location or target_position == destinations[3].hard_location:
            threshold = 0.09
        else:
            threshold = 0.24

        if destination_index == 2:
            failing_instance = True

        # Log movement
        logger.info(f"{data}")

        # DRONE CONTROLS

        if cf.positions[drone_uri][2] > 0.15:
            if action == 'back':
                print("Going back...")
                cf.swarm_move({drone_uri: [-0.1, 0, 0]}, None, 2., True)
            elif action == 'forward':
                print("going forward...")
                cf.swarm_move({drone_uri: [0.10, 0, 0]}, None, 2., True)
            elif action == 'right':
                print('Going right...')
                cf.swarm_move({drone_uri: [0., -0.10, 0]}, None, 2., True)
            elif action == 'left':
                print("Going left..")
                cf.swarm_move({drone_uri: [0., 0.10, 0]}, None, 2., True)

        if action == 'take off':
            print('take off....')
            cf.swarm_take_off()
        elif action == 'land':
            move_home()
            print('...landing, please wait')
            cf.swarm_land()

        end_time = time.time()
        elapsed_time = end_time - start_time_action
        logger.info(
            "Elapsed time since last action: {:.2f} seconds".format(elapsed_time))
        start_time_action = time.time()

        # Set the failing checkpoint, failing trial is always the third flight in an experimental block.
        # Will be randomized with the help of random.org.

        # FAILING MECHANISM

        if failing_instance:
            if failing_counter == 2:
                sock.send(json.dumps({
                    'action': 'failure',
                    'message': '⚠️ <strong> <span style="color: red;"> WARNING </span> </strong> ⚠️ <br/><strong> WEAK DRONE SIGNAL </strong><br/>'
                }))

                cf.swarm_move({drone_uri: [0, 0, .2]}, 0., 2., True)

            elif failing_counter == 6:
                destination_index += 1
                sock.send(json.dumps({
                    'action': 'failure',
                    'message': '⚠️ <strong> <span style="color: red;"> ATTENTION </span> </strong> ⚠️ <br/><strong> DRONE SIGNAL FAILURE </strong> <br/> Cannot complete checkpoint'
                }))

                cf.swarm_move({drone_uri: [0, 0, .2]}, 0., 2., True)

                logger.info("FAILURE\n")
                end_time = time.time()
                elapsed_time = end_time - start_time

                logger.info(
                    "Elapsed time: {:.2f} seconds".format(elapsed_time))

                move_home()

                cf.swarm_land()

                failing_instance = not failing_instance
                failing_counter = 0
                time.sleep(4)
                target_position = destinations[destination_index].default_location
                sock.send(json.dumps({
                    'action': 'select_location',
                    'destination_index': destination_index,
                    'destination_name': destinations[destination_index].name
                }))
                start_time = time.time()

                continue

            failing_counter += 1

        # CHECK IF GOAL IS REACHED

        if is_close_to_point():
            sock.send(json.dumps({'action': 'score', 'value': score}))
            print("Hoop completed!")
            end_time = time.time()
            elapsed_time = end_time - start_time

            logger.info("Elapsed time: {:.2f} seconds".format(elapsed_time))

            if goal_reached:
                sock.send(json.dumps(
                    {'action': 'finish', 'message': 'Destination reached! Well done! Going back to homebase.'}))
                time.sleep(2)

                if drone2:
                    sock.send(json.dumps({
                        'action': 'finish',
                        'message': 'Second and last part of experiment is now finished. You have earned <strong>' +
                        str(score) +
                        '</strong> SEK this flight session! Please finish the survey. Click <a href="http://192.168.0.100:1231/waiting_room" target="_blank">HERE</a> for the survey.'
                    }))

                    print('...landing, please wait')
                    move_home()
                    cf.swarm_land()

                    break
                else:
                    sock.send(json.dumps({
                        'action': 'goal',
                        'message': 'You have completed the first part of this experiment.<br/> You have earned <strong>' +
                        str(score) +
                        '</strong> SEK in this flight session! You can now do the first part of the survey. Click <a href="http://192.168.0.100:1231/waitingroomone" onclick="document.getElementById(\'surveyModal\').style.display=\'none\'"    target="_blank">HERE</a> for it. When you are done with the first part of the survey, the supervisor will change your drone.'
                    }))

                    print('...landing, please wait')
                    move_home()
                    cf.swarm_land()

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

            if destination_index == 1 or destination_index == 3:
                time.sleep(2)
                sock.send(json.dumps({
                    'action': 'select_location',
                    'destination_index': destination_index,
                    'destination_name': destinations[destination_index].name
                }))
            else:
                target_position = destinations[destination_index].default_location
                sock.send(json.dumps({
                    'action': 'default',
                    'destination_index': destination_index,
                    'destination_name': destinations[destination_index].name
                }))
            start_time = time.time()

            continue
