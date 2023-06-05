from flask import Flask, render_template
from flask_sock import Sock
from pycrazyswarm import Crazyswarm
import math 
import json

swarm = Crazyswarm()
timeHelper = swarm.timeHelper
cf = swarm.allcfs.crazyflies[0]

app = Flask(__name__)
sock = Sock(app)
goal_reached = False
destinations = [[1.0, -0.5, 1.0], [0., 0.5, 1.0], [-0.5, 0., 1.0], [0., -0.5, 1.0]]
target_position = destinations[0]
destination_index = 0
#target_position = [1.5,-0.5,1.0]
threshold = 0.6
score = 60
failing_instance = False
failing_counter = 0

def is_close_to_point():
    drone_position = cf.position()

    global target_position
    global destination_index
    global goal_reached 
    dx = drone_position[0] - target_position[0]
    dy = drone_position[1] - target_position[1]
    dz = drone_position[2] - target_position[2]

    distance = math.sqrt(dx**2+dy**2+dz**2)
    print('threshold: '+ str(threshold))
    print('target_position: '+ str(target_position))
    print('distance ' + str(distance))
    if threshold >= distance:
        if destination_index < len(destinations) - 1:
            destination_index += 1
            target_position = destinations[destination_index]
            
        if target_position == destinations[-1]:
            goal_reached = True
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
    log_file = "movements.log"  # File where movements will be logged
    global failing_instance
    global threshold
    global failing_counter
    global destination_index
    global target_position
    while True:
        
        data = sock.receive()
          # Log movement
        with open(log_file, "a") as file:
            file.write(f"{data}\n")
        if destination_index == 0:
            failing_instance = True
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
        if is_close_to_point():
            print("Hoop completed!")
            score +=10
            sock.send(json.dumps({'action':'score', 'value': score}))           
            sock.send(json.dumps({'action':'goal', 'message':'You have reached the destination, please proceed with destination: '+str(destination_index) }))
            drone_position = cf.position()
            drone_position[0] = -(drone_position[0])
            drone_position[1] = -(drone_position[1])
            drone_position[2] = 0
 
            print('...landing, please wait')
            cf.goTo(drone_position,0.,0.,True)
            timeHelper.sleep(2.0)
            cf.land(targetHeight=0.15,duration=2.0)
            continue
        if failing_instance:
            if failing_counter == 3 and destination_index < len(destinations)-1:
                destination_index = destination_index + 1
                target_position = destinations[destination_index]
                sock.send(json.dumps({'action':'goal', 'message':'A failure has occurred. Please proceed to : '+str(destination_index) +' instead'}))

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
                continue
            failing_counter=failing_counter+1

        



        if data == 'back':
            print("Going back...")
            cf.goTo([-0.25,0,0],0.,0.,True)
            timeHelper.sleep(2.0)
        if data == 'forward':
            print("going forward...")
            cf.goTo([0.25,0,0],0.,0.,True)
            timeHelper.sleep(2.0)
        if data == 'right':
            print('Going right...')
            cf.goTo([0.,-0.25,0],0.,0.,True)
        if data == 'left':
            print("Going left..")
            cf.goTo([0.,0.25,0],0.,0.,True)
            timeHelper.sleep(2.0)
        if data =='down':
            cf.goTo([0.,0.,-0.25],0.,0.,True)
            timeHelper.sleep(2.0)
            print("Going down")
        if data=='up':
            cf.goTo([0.,0.,0.25],0.,0.,True)
            timeHelper.sleep(2.0)
            print("Going up")
        if data =='take off':
            print('take off....')
            cf.takeoff(targetHeight=1.0,duration=2.5)
        if data =='land':
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
