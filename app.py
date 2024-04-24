from operator import truediv
from flask import Flask, render_template
from flask_sock import Sock
from pycrazyswarm import Crazyswarm
import math
from destination import Destination
import json
import time
import random

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='movements.log', 
                    filemode='a', 
                    encoding='utf-8', 
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

swarm = Crazyswarm()
timeHelper = swarm.timeHelper
cf = swarm.allcfs.crazyflies[0]
app = Flask(__name__)
sock = Sock(app)
goal_reached = False
# Destinations have a name, easy_location, hard_location
destinations = [

    Destination("A", [0.60, 0.3, .5], [0.6, -0.3, .5], [1., 0, 0.5]),
    Destination("D", [0.3, -0.6, .5], [-0.3, -0.6, .5], [0, -1.0, .5]),
    Destination("B", [-0.6, 0.60, .4], [0.3, 0.6, .5], [0, 1., .5]),
    Destination("C", [-0.6, -0.3, .5], [-0.6, 0.3, .5], [-1., 0.0, .5])
]
random.shuffle(destinations)
target_position = destinations[0].default_location
destination_index = 0
threshold = 0.24
score = 0
failing_instance = False
failing_counter = 0
drone2 = True

# FUNCTION THAT CHECKS IF GOAL IS REACHED
def is_close_to_point():
    drone_position = cf.position()

    global target_position
    global destination_index
    global goal_reached
    global score  # Declare score as a global variable
    dx = drone_position[0] - target_position[0]
    dy = drone_position[1] - target_position[1]
    dz = drone_position[2] - target_position[2]
    distance = math.sqrt(dx**2 + dy**2 + dz**2)
    if threshold >= distance:
        if target_position == destinations[destination_index].hard_location:
            score += 15
            logging.info("score 15\n " + str(destinations[destination_index].name))
            #with open("movements.log", "a") as file:
            #    file.write("score 15\n " +
            #               str(destinations[destination_index].name))
        if target_position == destinations[destination_index].default_location:
            score += 10
            logging.info("default score 10\n " + str(destinations[destination_index].name))
            #with open("movements.log", "a") as file:
            #    file.write("default score 10\n " +
            #               str(destinations[destination_index].name))
        if target_position == destinations[destination_index].easy_location:
            score += 5
            logging.info("score 5\n " + str(destinations[destination_index].name))
            #with open("movements.log", "a") as file:
            #    file.write("score 5\n " +
            #               str(destinations[destination_index].name))
        if len(destinations) - 1 == destination_index:
            goal_reached = True
        elif destination_index < len(destinations) - 1:
            destination_index += 1
        return True
    else:
        return False


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
        logger.info(f"{data}\n")
        #with open(log_file, "a") as file:
        #    file.write(f"{data}\n")

        # DRONE CONTROLS
        if action == 'back':
            if cf.position()[2] > 0.15:
                print("Going back...")
                cf.goTo([-0.1, 0, 0], None, 2., True)
                # time.sleep(2)
                timeHelper.sleep(2)
                end_time = time.time()
                elapsed_time = end_time - start_time_action
                logger.info("Elapsed time since last action: {:.2f} seconds".format(elapsed_time))
                #with open(log_file, "a") as file:
                #    file.write(
                #        "Elapsed time since last action: {:.2f} seconds".format(elapsed_time) + "\n")
                start_time_action = time.time()

        if action == 'forward':
            if cf.position()[2] > 0.15:
                print("going forward...")
                cf.goTo([0.10, 0, 0], None, 2., True)
                end_time = time.time()
                elapsed_time = end_time - start_time_action
                logger.info("Elapsed time since last action: {:.2f} seconds".format(elapsed_time))
                #with open(log_file, "a") as file:
                #    file.write(
                #        "Elapsed time since last action: {:.2f} seconds".format(elapsed_time) + "\n")
                start_time_action = time.time()

        if action == 'right':
            if cf.position()[2] > 0.15:
                print('Going right...')
                cf.goTo([0., -0.10, 0], None, 2., True)
                end_time = time.time()
                elapsed_time = end_time - start_time_action
                logger.info("Elapsed time since last action: {:.2f} seconds".format(elapsed_time))
                #with open(log_file, "a") as file:
                #    file.write(
                #        "Elapsed time since last action: {:.2f} seconds".format(elapsed_time) + "\n")
                start_time_action = time.time()

        if action == 'left':
            if cf.position()[2] > 0.15:
                print("Going left..")
                cf.goTo([0., 0.10, 0], None, 2., True)
                # time.sleep(2)
                end_time = time.time()
                elapsed_time = end_time - start_time_action
                logger.info("Elapsed time since last action: {:.2f} seconds".format(elapsed_time))
                #with open(log_file, "a") as file:
                #    file.write(
                #        "Elapsed time since last action: {:.2f} seconds".format(elapsed_time) + "\n")
                start_time_action = time.time()

        if action == 'take off':
            print('take off....')
            cf.takeoff(targetHeight=0.5, duration=2.5)
            # time.sleep(2)
            end_time = time.time()
            elapsed_time = end_time - start_time_action
            logger.info("Elapsed time since last action: {:.2f} seconds".format(elapsed_time))
            #with open(log_file, "a") as file:
            #    file.write(
            #        "Elapsed time since last action: {:.2f} seconds".format(elapsed_time) + "\n")
            start_time_action = time.time()

        if action == 'land':
            drone_position = cf.position()
            drone_position[0] = -(drone_position[0])
            drone_position[1] = -(drone_position[1])
            drone_position[2] = 0
            cf.goTo(drone_position, 0., 1., True)
            print('...landing, please wait')
            timeHelper.sleep(2.0)
            cf.land(targetHeight=0.15, duration=2.0)
            timeHelper.sleep(3.0)
            if cf.position()[2] > 0.01:
                cf.land(targetHeight=0.05, duration=2.0)
            if cf.position()[2] > 0.01:
                cf.land(targetHeight=0.05, duration=2.0)
            if cf.position()[2] > 0.01:
                cf.land(targetHeight=0.05, duration=2.0)

        # Set the failing checkpoint, failing trial is always the third flight in an experimental block.
        # Will be randomized with the help of random.org.

        # FAILING MECHANISM
        if failing_instance:
            if failing_counter == 2:
                sock.send(json.dumps({
                    'action': 'failure',
                    'message': '⚠️ <strong> <span style="color: red;"> WARNING </span> </strong> ⚠️ <br/><strong> WEAK DRONE SIGNAL </strong><br/>'
                }))

                cf.goTo([0, 0, .2], 0., 2., True)
                timeHelper.sleep(2)

            if failing_counter == 6:
                destination_index = destination_index + 1
                sock.send(json.dumps({
                    'action': 'failure',
                    'message': '⚠️ <strong> <span style="color: red;"> ATTENTION </span> </strong> ⚠️ <br/><strong> DRONE SIGNAL FAILURE </strong> <br/> Cannot complete checkpoint'
                }))

                cf.goTo([0, 0, .2], 0., 2., True)
                timeHelper.sleep(2)
                drone_position = cf.position()
                drone_position[0] = -(drone_position[0])
                drone_position[1] = -(drone_position[1])
                drone_position[2] = 0

                logger.info("FAILURE\n")
                #with open(log_file, "a") as file:
                #    file.write("FAILURE\n")
                end_time = time.time()
                elapsed_time = end_time - start_time

                logger.info("Elapsed time: {:.2f} seconds".format(elapsed_time))
                #with open(log_file, "a") as file:
                #    file.write(
                #        "Elapsed time: {:.2f} seconds".format(elapsed_time) + "\n")
                cf.goTo(drone_position, None, 2, True)
                timeHelper.sleep(2)

                cf.land(targetHeight=0.05, duration=2.0)
                timeHelper.sleep(3)

                if cf.position()[2] > 0.01:
                    cf.land(targetHeight=0.05, duration=2.0)

                if cf.position()[2] > 0.01:
                    cf.land(targetHeight=0.05, duration=2.0)

                if cf.position()[2] > 0.01:
                    cf.land(targetHeight=0.05, duration=2.0)

                if cf.position()[2] > 0.01:
                    cf.land(targetHeight=0.05, duration=2.0)

                if cf.position()[2] > 0.01:
                    cf.land(targetHeight=0.05, duration=2.0)

                failing_instance = not failing_instance
                failing_counter = 0
                timeHelper.sleep(4)
                target_position = destinations[destination_index].default_location
                sock.send(json.dumps({
                    'action': 'select_location',
                    'destination_index': destination_index,
                    'destination_name': destinations[destination_index].name
                }))
                start_time = time.time()

                continue

            failing_counter = failing_counter + 1

        # CHECK IF GOAL IS REACHED
        if is_close_to_point():
            sock.send(json.dumps({'action': 'score', 'value': score}))
            print("Hoop completed!")
            end_time = time.time()
            elapsed_time = end_time - start_time

            logger.info("Elapsed time: {:.2f} seconds".format(elapsed_time))
            #with open(log_file, "a") as file:
            #    file.write(
            #        "Elapsed time: {:.2f} seconds".format(elapsed_time) + "\n"
            #    )

            if goal_reached:
                sock.send(json.dumps(
                    {'action': 'finish', 'message': 'Destination reached! Well done! Going back to homebase.'}))
                timeHelper.sleep(2)

                if drone2:
                    sock.send(json.dumps({
                        'action': 'finish',
                        'message': 'Second and last part of experiment is now finished. You have earned <strong>' + 
                        str(score) + 
                        '</strong> SEK this flight session! Please finish the survey. Click <a href="http://192.168.0.100:1231/waiting_room" target="_blank">HERE</a> for the survey.'
                    }))

                    drone_position = cf.position()
                    drone_position[0] = -(drone_position[0])
                    drone_position[1] = -(drone_position[1])
                    drone_position[2] = 0
                    print('...landing, please wait')
                    cf.goTo(drone_position, 0., 1, True)
                    timeHelper.sleep(2)

                    if cf.position()[0] > 0.001:
                        drone_position = cf.position()
                        drone_position[0] = -(drone_position[0])
                        drone_position[1] = -(drone_position[1])
                        drone_position[2] = 0
                        cf.goTo(drone_position, 0., 1., True)

                    cf.land(targetHeight=0.05, duration=2.0)
                    timeHelper.sleep(3)

                    if cf.position()[2] > 0.01:
                        cf.land(targetHeight=0.05, duration=2.0)

                    if cf.position()[2] > 0.01:
                        cf.land(targetHeight=0.05, duration=2.0)

                    if cf.position()[2] > 0.01:
                        cf.land(targetHeight=0.05, duration=2.0)

                    break
                else:
                    sock.send(json.dumps({
                            'action': 'goal', 
                            'message': 'You have completed the first part of this experiment.<br/> You have earned <strong>' +
                            str(score) +
                            '</strong> SEK in this flight session! You can now do the first part of the survey. Click <a href="http://192.168.0.100:1231/waitingroomone" onclick="document.getElementById(\'surveyModal\').style.display=\'none\'"    target="_blank">HERE</a> for it. When you are done with the first part of the survey, the supervisor will change your drone.'
                        }))

                    drone_position = cf.position()
                    drone_position[0] = -(drone_position[0])
                    drone_position[1] = -(drone_position[1])
                    drone_position[2] = 0
                    print('...landing, please wait')

                    cf.goTo(drone_position, 0., 1, True)
                    timeHelper.sleep(2)

                    if cf.position()[0] > 0.1:
                        drone_position = cf.position()
                        drone_position[0] = -(drone_position[0])
                        drone_position[1] = -(drone_position[1])
                        drone_position[2] = 0
                        cf.goTo(drone_position, 0., 1., True)
                        timeHelper.sleep(2)

                    cf.land(targetHeight=0.05, duration=2.0)
                    timeHelper.sleep(3)

                    if cf.position()[2] > 0.01:
                        cf.land(targetHeight=0.05, duration=2.0)
                    if cf.position()[2] > 0.01:
                        cf.land(targetHeight=0.05, duration=2.0)
                    if cf.position()[2] > 0.01:
                        cf.land(targetHeight=0.05, duration=2.0)
                    break

            if destination_index == 1:
                sock.send(json.dumps({
                            'action': 'goal',
                            'message': 'Destination reached! First flight finished! ... Going back to home base.'
                }))

                timeHelper.sleep(3)
                drone_position = cf.position()
                drone_position[0] = -(drone_position[0])
                drone_position[1] = -(drone_position[1])
                drone_position[2] = 0
                cf.goTo(drone_position, 0., 2., True)
            else:
                sock.send(json.dumps({
                    'action': 'goal',
                    'message': 'Destination reached! ... Going back to home base. '
                }))

                timeHelper.sleep(3)
                drone_position = cf.position()
                drone_position[0] = -(drone_position[0])
                drone_position[1] = -(drone_position[1])
                drone_position[2] = 0
                cf.goTo(drone_position, 0., 2., True)

            cf.land(targetHeight=0.05, duration=2.0)
            timeHelper.sleep(3)

            if cf.position()[2] > 0.01:
                cf.land(targetHeight=0.05, duration=2.0)

            if cf.position()[2] > 0.01:
                cf.land(targetHeight=0.05, duration=2.0)

            if cf.position()[2] > 0.01:
                cf.land(targetHeight=0.05, duration=2.0)

            if cf.position()[2] > 0.01:
                cf.land(targetHeight=0.05, duration=2.0)

            if cf.position()[2] > 0.01:
                cf.land(targetHeight=0.05, duration=2.0)

            if cf.position()[2] > 0.01:
                cf.land(targetHeight=0.05, duration=2.0)

            if destination_index == 1 or destination_index == 3:
                timeHelper.sleep(2)
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


if __name__ == '__main__':
    app.run(host='192.168.0.104', port=5000, debug=True)
