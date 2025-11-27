from robot import Robot
from utils.brick import reset_brick
import threading
import time

def main():
    # this function should run the entire circuit
    reset_brick()
    robot = Robot()
    robot.main()
    #robot.drop_off_package()
    #robot.drop_off_package()
    #robot.turn_x_deg(270)
    #robot.turn_right_90()
    #robot.color_sensing_system.move_sensor_to_front()
    #time.sleep(10)
    #time.sleep(10)
    reset_brick()
    

if __name__ == "__main__":
    
    try:
        main()
        #reset_brick()
    except KeyboardInterrupt:
        reset_brick()