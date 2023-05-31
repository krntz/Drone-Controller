"""Takeoff-hover-land for one CF. Useful to validate hardware config."""

from pycrazyswarm import Crazyswarm
import math

TAKEOFF_DURATION = 2.5
HOVER_DURATION = 5.0
def left(cf):
    NEWPOS = cf.position()
    NEWPOS[0]=NEWPOS[0]-0.20
    cf.goTo([-0.2,0.,0.], 3.0, 0,True,0)

def main():
    swarm = Crazyswarm()
    timeHelper = swarm.timeHelper
    cf = swarm.allcfs.crazyflies[0]
    NEWPOS = cf.position()
    cf.takeoff(targetHeight=1.0, duration=TAKEOFF_DURATION)
    print(cf.position())

    while(1):
        pos = input("Where we going chief?")
        NEWPOS = cf.position()
        print(NEWPOS)
        if (pos == 'left'):
            cf.goTo([-0.5,0.,0.], 0., 3.0,True,0)
            #left(cf)
            #NEWPOS[0]=NEWPOS[0]-0.02 
            #timeHelper.sleep(TAKEOFF_DURATION + HOVER_DURATION)
            #cf.goTo(NEWPOS, HOVER_DURATION, 0,False,0)
        elif (pos == 'right'):
            #NEWPOS[0]=NEWPOS[0]+0.15
            #timeHelper.sleep(TAKEOFF_DURATION + HOVER_DURATION) 
           # cf.goTo(NEWPOS, HOVER_DURATION, 0,False,0)
           cf.goTo([0.5,0.,0.], 0., 3.0,True,0)
        elif (pos=='forward'):
            #NEWPOS[1] = NEWPOS[1]+0.02
            #timeHelper.sleep(TAKEOFF_DURATION + HOVER_DURATION)
            #cf.goTo(NEWPOS, HOVER_DURATION, 0,False,0)
            cf.goTo([0.,0.5,0.], 0, 3.0,True,0)
            
        elif (pos=='back'):
            #NEWPOS[1]= NEWPOS[1]-0.02 
            #timeHelper.sleep(TAKEOFF_DURATION + HOVER_DURATION) 
            #cf.goTo(NEWPOS, HOVER_DURATION, 0,False,0)
            cf.goTo([0.,-0.5,0.], 0, 3.0,True,0)
        elif (pos=='land'):   
            timeHelper.sleep(TAKEOFF_DURATION + HOVER_DURATION) 
            cf.land(targetHeight=0.04, duration=2.5)
        else:
            break;
        
    cf.land(targetHeight=0.04, duration=2.5)

        

        
        


if __name__ == "__main__":
    main()
