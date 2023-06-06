from flask import Flask, render_template
from flask_sock import Sock
from pycrazyswarm import Crazyswarm
import math 
from destination import Destination
import json

swarm = Crazyswarm()
timeHelper = swarm.timeHelper
cf = swarm.allcfs.crazyflies[0]

app = Flask(__name__)
sock = Sock(app)
goal_reached = False


# Destinations have a name, easy_location, hard_location
destinations = [
    Destination("A", [1.0, -0.5, 1.0], [1.0, -0.4, 1.0]),
    Destination("B", [0., 0.5, 1.0], [0.2, 0.6, 1.3]),
    Destination("C", [-0.5, 0., 1.0], [-0.7, 0.1, 1.4]),
    Destination("D", [0., -0.5, 1.0], [0.1, -0.6, 1.5])
]

target_position = destinations[0].easy_location
destination_index = 0
threshold = 0.5
score = 60
failing_instance = False
failing_counter = 0

###################################### FUNCTION THAT CHECKS IF GOAL IS REACHED ##########################################################
def is_close_to_point():
    drone_position = cf.position()

    global target_position
    global destination_index
    global goal_reached 
    global score  # Declare score as a global variable
    dx = drone_position[0] - target_position[0]
    dy = drone_position[1] - target_position[1]
    dz = drone_position[2] - target_position[2]

    distance = math.sqrt(dx**2+dy**2+dz**2)
    print('drone_position :'+ str(drone_position))
    print('threshold: '+ str(threshold))
    print('target_position: '+ str(target_position))
    print('distance ' + str(distance))
    print('easy_loc :' + str(destinations[destination_index].easy_location))
    if threshold >= distance:
        if target_position == destinations[destination_index].hard_location:
            score+=10
        if target_position == destinations[destination_index].easy_location:
            score+=5
        if len(destinations)-1 == destination_index:
            goal_reached = True
        elif destination_index < len(destinations) - 1:
            destination_index += 1
            
        
        return True
    else:
        return False


###############################################################################################################################################3
@app.route('/')
def index():
    return render_template('index.html')
@sock.route('/action')
def echo(sock):
    global score
    global goal_reached
    global destinations
    log_file = "movements.log"  # File where movements will be logged
    global failing_instance
    global threshold
    global failing_counter
    global destination_index
    global target_position


     # Send initial 'select_location' message before entering main loop
    sock.send(json.dumps({
        'action': 'select_location',
        'destination_index': destination_index,
        'destination_name': destinations[destination_index].name
    }))
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
                continue  # Skip the rest of the loop and start the next iteratio
        action = data['action']

            ##### Log movement####################################################3333
        with open(log_file, "a") as file:
            file.write(f"{data}\n")
        if destination_index == 2:
            failing_instance = True
        
        #################### FAILING MECHANISM ###########################################################################################################3
        if failing_instance:
            if failing_counter == 3:
                destination_index = destination_index + 1
                target_position = destinations[destination_index].easy_location
                sock.send(json.dumps({'action':'goal', 'message':'A failure has occurred. Please proceed to checkpoint '+str(destinations[destination_index].name) +' instead'}))
                drone_position = cf.position()
                drone_position[0] = -(drone_position[0])
                drone_position[1] = -(drone_position[1])
                drone_position[2] = 0
    
                print('...landing, please wait')
                cf.goTo(drone_position,0.,0.,True)
                timeHelper.sleep(2.0)
                cf.land(targetHeight=0.15,duration=2.0)
                failing_instance = not failing_instance
                failing_counter = 0
                sock.send(json.dumps({
                        'action': 'select_location',
                        'destination_index': destination_index,
                        'destination_name': destinations[destination_index].name
                    }))
                
                continue
            failing_counter=failing_counter+1
        
        ############## CHECK IF GOAL IS REACHED ########################################################################################3
        if is_close_to_point():
            print("Hoop completed!")
            sock.send(json.dumps({'action':'score', 'value': score}))   
            if goal_reached:
                sock.send(json.dumps({'action':'goal', 'message':'You have finished your job, pilot :) Now you can fill out the survey' }))
                ### IMPLEMENT SURVEY REDIRECTION ###
                drone_position = cf.position()
                drone_position[0] = -(drone_position[0])
                drone_position[1] = -(drone_position[1])
                drone_position[2] = 0
                print('...landing, please wait')
                cf.goTo(drone_position,0.,0.,True)
                timeHelper.sleep(2.0)
                cf.land(targetHeight=0.15,duration=2.0)
                break       
            sock.send(json.dumps({'action':'goal', 'message':'Well done, you finished the checkpoint! Continue with checkpoint '+destinations[destination_index].name}))
            sock.send(json.dumps({
                    'action': 'select_location',
                    'destination_index': destination_index,
                    'destination_name': destinations[destination_index].name
                }))
            drone_position = cf.position()
            drone_position[0] = -(drone_position[0])
            drone_position[1] = -(drone_position[1])
            drone_position[2] = 0
 
            print('...landing, please wait')
            cf.goTo(drone_position,0.,0.,True)
            timeHelper.sleep(2.0)
            cf.land(targetHeight=0.15,duration=2.0)
            continue




####################### DRONE CONTROLS"################################################################################3
        if action == 'back':
            print("Going back...")
            cf.goTo([-0.25,0,0],0.,0.,True)
            timeHelper.sleep(2.0)
        if action == 'forward':
            print("going forward...")
            cf.goTo([0.25,0,0],0.,0.,True)
            timeHelper.sleep(2.0)
        if action == 'right':
            print('Going right...')
            cf.goTo([0.,-0.25,0],0.,0.,True)
        if action == 'left':
            print("Going left..")
            cf.goTo([0.,0.25,0],0.,0.,True)
            timeHelper.sleep(2.0)
        if action =='down':
            cf.goTo([0.,0.,-0.25],0.,0.,True)
            timeHelper.sleep(2.0)
            print("Going down")
        if action=='up':
            cf.goTo([0.,0.,0.25],0.,0.,True)
            timeHelper.sleep(2.0)
            print("Going up")
        if action =='take off':
            print('take off....')
            cf.takeoff(targetHeight=1.0,duration=2.5)
        if action =='land':
            drone_position = cf.position()
            drone_position[0] = -(drone_position[0])
            drone_position[1] = -(drone_position[1])
            drone_position[2] = 0
            cf.goTo(drone_position,0.,0.,True)
            print('...landing, please wait')
            timeHelper.sleep(2.0)
            cf.land(targetHeight=0.15,duration=2.0)

if __name__ == '__main__':
    app.run(debug=True)
