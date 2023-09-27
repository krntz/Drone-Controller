from operator import truediv
from flask import Flask, render_template
from flask_sock import Sock
from pycrazyswarm import Crazyswarm
import math
from destination import Destination
import json
import time
import random

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
    global target_position, destination_index, goal_reached, score

    drone_position = cf.position()
    dx = drone_position[0] - target_position[0]
    dy = drone_position[1] - target_position[1]
    dz = drone_position[2] - target_position[2]
    distance = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

    if threshold >= distance:
        if target_position == destinations[destination_index].hard_location:
            score += 15
            log_score("score 15", destination_index)
        elif target_position == destinations[destination_index].default_location:
            score += 10
            log_score("default score 10", destination_index)
        elif target_position == destinations[destination_index].easy_location:
            score += 5
            log_score("score 5", destination_index)

        if destination_index == len(destinations) - 1:
            goal_reached = True
        elif destination_index < len(destinations) - 1:
            destination_index += 1

        return True
    else:
        return False

# Log the score to the file
def log_score(message, destination_index):
    with open("movements.log", "a") as file:
        file.write(f"{message}\n {destinations[destination_index].name}")

@app.route('/')
def index():
    return render_template('index.html')

@sock.route('/action')
def echo(sock):
    global score, goal_reached, destinations, failing_instance, threshold, failing_counter, destination_index, target_position

    sock.send(json.dumps({'action': 'welcome', 'message': f'Welcome! This is your first flight. Please fly to <strong>checkpoint {destinations[destination_index].name}</strong> and hover above the blue ring'}))
    sock.send(json.dumps({
        'action': 'default',
        'destination_index': destination_index,
        'destination_name': destinations[destination_index].name
    }))

    start_time = time.time()
    start_time_action = time.time()

    while True:
        data = sock.receive()
        if isinstance(data, str):
            data = json.loads(data)
            if 'action' in data and data['action'] == 'select_location_choice':
                choice = data['choice']
                if choice == 'easy':
                    target_position = destinations[destination_index].easy_location
                else:
                    target_position = destinations[destination_index].hard_location
                continue

        if 'action' in data and data['action'] == 'score':
            score = 0

        action = data['action']

        update_threshold()

        if destination_index == 2:
            failing_instance = True

        with open("movements.log", "a") as file:
            file.write(f"{data}\n")

        handle_drone_actions(action, start_time_action)

        if failing_instance:
            handle_failing_mechanism()

        if is_close_to_point():
            sock.send(json.dumps({'action': 'score', 'value': score}))
            print("Hoop completed!")
            handle_goal_reached(start_time)
            start_time = time.time()
            continue

if __name__ == '__main__':
    app.run(host='192.168.0.104', port=5000, debug=True)
