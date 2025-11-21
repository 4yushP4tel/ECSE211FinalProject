from robot import Robot
from utils.brick import reset_brick
import threading
import time

def main():
    # this function should run the entire circuit
    robot = Robot()
    robot.main()
    time.sleep(10)
    reset_brick()

    
    
if __name__ == "__main__":
    
    main()