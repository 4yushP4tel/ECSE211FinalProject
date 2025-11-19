from robot import Robot
from utils.brick import reset_brick
import threading
import time

def main():
    # this function should run the entire circuit
    #reset_brick()
    robot = Robot()
    robot.drop_off_package()
    time.sleep(1)
    robot.drop_off_package()
    reset_brick()
    
    
if __name__ == "__main__":
    
    main()