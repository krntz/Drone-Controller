from flask import Flask, render_template
from flask_sock import Sock
from pycrazyswarm import Crazyswarm
import math 
import json

swarm = Crazyswarm()
cf = swarm.allcfs.crazyflies[0]

app = Flask(__name__)
sock = Sock(app)
goal_reached = False
target_position = [1.5,-0.5,1.0]
threshold = 0.2
score = 0

def is_close_to_point():
    drone_position = cf.position()

    global target_position
    dx = drone_position[0] - target_position[0]
    dy = drone_position[1] - target_position[1]
    dz = drone_position[2] - target_position[2]

    distance = math.sqrt(dx**2+dy**2+dz**2)

    if threshold >= distance:
        goal_reached = True
        target_position = [50.,50.,50.] 
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
    
    global threshold
    while True:
        data = sock.receive()
        if goal_reached:
            target_position=[50.,50.,50.]
        if is_close_to_point():
            score +=10
            sock.send(json.dumps({'action':'score', 'value': score}))
        if data == 'back':
            print("Going back...")
            cf.goTo([-0.3,0,0],0.,0.,True)
        if data == 'forward':
            print("going forward...")
            cf.goTo([0.3,0,0],0.,0.,True)
        if data == 'right':
            print('Going right...')
            cf.goTo([0.,-0.3,0],0.,0.,True)
        if data == 'left':
            print("Going left..")
            cf.goTo([0.,0.3,0],0.,0.,True)
        if data =='down':
            cf.goTo([0.,0.,-0.25],0.,0.,True)
            print("Going down")
        if data=='up':
            cf.goTo([0.,0.,0.25],0.,0.,True)
            print("Going up")
        if data =='take off':
            print('take off....')
            cf.takeoff(targetHeight=1.0,duration=2.5)
        if data =='land':
            print('...landing, please wait')
            cf.land(targetHeight=0.15,duration=2.0)

if __name__ == '__main__':
    app.run()
