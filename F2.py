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

    Destination("A", [0.65, 0.3, .5], [0.6, -0.3 , .5], [1.05, 0, 0.5]),
        Destination("D",  [0.3, -0.7, .5], [-0.3, -0.6, .5], [0, -1.0, .5]),
    
    Destination("B", [-0.65, 0.7, .5], [0.3, 0.6, .5], [0, 1.05, .5]),

    #Destination("A", [0., 0.,0.], [0., 0. , .0]),
    #Destination("B", [-0.0, 0.0, 0.], [0., 0., 0.],[-0.0, 0.0, 0.]),
    Destination("C", [-0.65, -0.3, .5], [-0.6, 0.3, .5], [-1.05, 0.0, .5])
]

random.shuffle(destinations)


target_position = destinations[0].default_location
destination_index = 0
threshold = 0.24
score = 0
failing_instance = False
failing_counter = 0
drone2 = True


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
            score+=15
            with open("movements.log", "a") as file:
                file.write("score 15\n "+ str(destinations[destination_index].name)) 
        if target_position == destinations[destination_index].default_location:
            score+=10
            with open("movements.log", "a") as file:
                file.write("default score 10\n " + str(destinations[destination_index].name))
        if target_position == destinations[destination_index].easy_location:
            score+=5
            with open("movements.log", "a") as file:
                file.write("score 5\n "+ str(destinations[destination_index].name))
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
    log_file = "movements.log"  # File where movements and durations will be logged
    global failing_instance
    global threshold
    global failing_counter
    global destination_index
    global target_position

    sock.send(json.dumps({'action':'welcome', 'message':'Welcome!  This is your first flight. Please fly to  <strong> checkpoint '+str(destinations[destination_index].name) +'</strong> and hover above the blue ring'}))
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
        action = data['action']


        if target_position == destinations[0].hard_location or target_position == destinations[1].hard_location or target_position == destinations[2].hard_location or target_position == destinations[3].hard_location:
            threshold = 0.07
        else:
            threshold = 0.24
        if destination_index == 2:
            failing_instance = False
            #if not failing_instance:
                #threshold = 0.4        
        #if destination_index == 3:
            #threshold == 0.3

            ##### Log movement####################################################3333
        with open(log_file, "a") as file:
            file.write(f"{data}\n")
            ####################### DRONE CONTROLS"################################################################################3
        
        if action == 'back':
            print("Going back...")
            cf.goTo([-0.1,0,0],None,2.,True)
            time.sleep(2)
            end_time = time.time()
            elapsed_time = end_time - start_time_action
            with open(log_file, "a") as file:
                file.write("Elapsed time since last action: {:.2f} seconds".format(elapsed_time)+"\n")
            start_time_action = time.time()

        if action == 'forward':
            print("going forward...")
            cf.goTo([0.10,0,0],None,2.,True)
            time.sleep(2)
            end_time = time.time()
            elapsed_time = end_time - start_time_action
            with open(log_file, "a") as file:
                file.write("Elapsed time since last action: {:.2f} seconds".format(elapsed_time)+"\n")
            start_time_action = time.time()
        if action == 'right':
            print('Going right...')
            cf.goTo([0.,-0.10,0],None,2.,True)
            time.sleep(2)
            end_time = time.time()
            elapsed_time = end_time - start_time_action
            with open(log_file, "a") as file:
                file.write("Elapsed time since last action: {:.2f} seconds".format(elapsed_time)+"\n")
            start_time_action = time.time()
        if action == 'left':
            print("Going left..")
            cf.goTo([0.,0.10,0],None,2.,True)
            time.sleep(2)
            end_time = time.time()
            elapsed_time = end_time - start_time_action
            with open(log_file, "a") as file:
                file.write("Elapsed time since last action: {:.2f} seconds".format(elapsed_time)+"\n")
            start_time_action = time.time()
        if action =='take off':
            print('take off....')
            cf.takeoff(targetHeight=0.5,duration=2.5)
            time.sleep(2)
            end_time = time.time()
            elapsed_time = end_time - start_time_action
            with open(log_file, "a") as file:
                file.write("Elapsed time since last action: {:.2f} seconds".format(elapsed_time)+"\n")
            start_time_action = time.time()
        if action =='land':
            drone_position = cf.position()
            drone_position[0] = -(drone_position[0])
            drone_position[1] = -(drone_position[1])
            drone_position[2] = 0
            cf.goTo(drone_position,0.,1.,True)
            print('...landing, please wait')
            timeHelper.sleep(2.0)
            cf.land(targetHeight=0.15,duration=2.0)
            if cf.position()[2] > 0.001:
                    cf.land(targetHeight=0.05,duration=2.0)
            if cf.position()[2] > 0.001:
                    cf.land(targetHeight=0.05,duration=2.0)

        # Set the failing checkpoint, failing trial is always the third flight in an experimental block.
        # Will be randomized with the help of random.org.
        
        

        #################### FAILING MECHANISM ###########################################################################################################3
        if failing_instance:

            if failing_counter == 2:
                sock.send(json.dumps({'action': 'failure', 'message': '⚠️ <strong> <span style="color: red;"> WARNING </span> </strong> ⚠️ <br/><strong> WEAK DRONE SIGNAL </strong><br/>'}))
                cf.goTo([0,0,-.2],0.,2.,True)
                time.sleep(2)
                cf.goTo([0,0,.2],0.,2.,True)
                time.sleep(2)
            if failing_counter == 6:
                destination_index = destination_index + 1
                sock.send(json.dumps({'action': 'failure', 'message': '⚠️ <strong> <span style="color: red;"> ATTENTION </span> </strong> ⚠️ <br/><strong> DRONE SIGNAL FAILURE </strong> <br/> Cannot complete checkpoint'}))
                cf.goTo([0,0,-.2],0.,1.,True)
                time.sleep(2)
                cf.goTo([0,0,.2],0.,1.,True)
                time.sleep(2)
                cf.goTo([0,0,-.1],0.,1.,True)
                time.sleep(2)
                cf.goTo([0,0,.1],0.,1.,True)

                
                time.sleep(1)
                drone_position = cf.position()
                drone_position[0] = -(drone_position[0])
                drone_position[1] = -(drone_position[1])
                drone_position[2] = 0
                with open(log_file, "a") as file:
                    file.write("FAILURE\n")
    
                print('...landing, please wait')
                end_time = time.time()
                elapsed_time = end_time - start_time
                with open(log_file, "a") as file:
                    file.write("Elapsed time: {:.2f} seconds".format(elapsed_time)+"\n")
                cf.goTo(drone_position,None,1.2,True)
                time.sleep(2)
                cf.land(targetHeight=0.05,duration=2.0)
                if cf.position()[2] > 0.001:
                    cf.land(targetHeight=0.05,duration=2.0)
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
            failing_counter=failing_counter+1
        
        ############## CHECK IF GOAL IS REACHED ########################################################################################3
        if is_close_to_point():
            sock.send(json.dumps({'action':'score', 'value': score})) 
            print("Hoop completed!")
            end_time = time.time()
            elapsed_time = end_time - start_time
            with open(log_file, "a") as file:
                    file.write("Elapsed time: {:.2f} seconds".format(elapsed_time)+"\n")
            if goal_reached:
                #sock.send(json.dumps({'action':'finish', 'message':'You have finished your job, pilot. You have earned an additional amount of '+ str(score)+' KR. And now, you can fill out the rest of the survey.' }))
                sock.send(json.dumps({'action':'finish', 'message':'Destination reached! Well done! Going back to homebase.'})) 
                time.sleep(1)

                if drone2:
                    sock.send(json.dumps({'action':'finish', 'message':'Second and last part of experiment is now finished. You have earned <strong>'+str(score)+'</strong> SEK this flight session! Please finish the survey. Click <a href="http://192.168.0.100:1231/waiting_room" target="_blank">HERE</a> for the survey.'})) 
                else:
                    #sock.send(json.dumps({'action':'finish', 'message':'You have completed the first sets of tasks! You can now do the first part of the <a href="https://link_to_your_survey.com" onclick="document.getElementById(\'surveyModal\').style.display=\'none\'"    target="_blank">survey</a>.'}))
                    sock.send(json.dumps({'action':'goal', 'message':'You have completed the first part of this experiment.<br/> You have earned <strong>' + str(score) +'</strong> SEK in this flight session! You can now do the first part of the survey. Click <a href="http://192.168.0.100:1231/waitingroomone" onclick="document.getElementById(\'surveyModal\').style.display=\'none\'"    target="_blank">HERE</a> for it. When you are done with the first part of the survey, the supervisor will change your drone.'}))

                drone_position = cf.position()
                drone_position[0] = -(drone_position[0])
                drone_position[1] = -(drone_position[1])
                drone_position[2] = 0
                print('...landing, please wait')
                cf.goTo(drone_position,0.,1.,True)
                time.sleep(1)
                cf.land(targetHeight=0.05,duration=2.0)
                if cf.position()[2] > 0.001:
                    cf.land(targetHeight=0.05,duration=2.0)
                if cf.position()[2] > 0.001:
                    cf.land(targetHeight=0.05,duration=2.0)
                if cf.position()[2] > 0.001:
                    cf.land(targetHeight=0.05,duration=2.0)



                break            
            if destination_index == 1:
                sock.send(json.dumps({'action':'goal', 'message':'Destination reached! First flight finished! ... Going back to home base.'}))
                time.sleep(3)
                drone_position = cf.position()
                drone_position[0] = -(drone_position[0])
                drone_position[1] = -(drone_position[1])
                drone_position[2] = 0
                cf.goTo(drone_position,0.,2.,True)
            else:
                sock.send(json.dumps({'action':'goal', 'message':'Destination reached! ... Going back to home base. ' }))
                time.sleep(3)
                drone_position = cf.position()
                drone_position[0] = -(drone_position[0])
                drone_position[1] = -(drone_position[1])
                drone_position[2] = 0
                cf.goTo(drone_position,0.,2.,True)
                
                
            time.sleep(3)
            cf.land(targetHeight=0.05,duration=2.0)
            if cf.position()[2] > 0.001:
                    cf.land(targetHeight=0.05,duration=2.0)
            if cf.position()[2] > 0.001:
                    cf.land(targetHeight=0.05,duration=2.0)
            if cf.position()[2] > 0.001:
                    cf.land(targetHeight=0.05,duration=2.0)
            if cf.position()[2] > 0.001:
                    cf.land(targetHeight=0.05,duration=2.0)

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






if __name__ == '__main__':
    app.run(debug=True)
