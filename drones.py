from pycrazyswarm import Crazyswarm
import pickle
class Drone:
    name=""
    swarm = Crazyswarm()
    timeHelper = swarm.timeHelper
    cf = swarm.allcfs.crazyflies[0]

    def __init__(self,name):
        self.name = name
    def left(self):
        self.cf.goTo([-1.,0.,0.],0.,0.,True,1.0)
    def right(self):
        self.cf.goTo([1.,0.,0.],0.,0.,True,1.0)
    def forward(self):
        self.cf.goTo([0.,1.,0.],0.,0.,True,1.0)
    def back(self):
        self.cf.goTo([0.,-1.,0.],0.,0.,True,1.0)
    def take_off(self):
        self.cf.takeoff(targetHeight=1.0,duration=2.5)
    def land(self):
        self.cf.land(targetHeight=1.0,duration=2.5)


drone = Drone("Noah")
with open('drone.pickle','wb') as f:
    pickle.dump(drone, f)


