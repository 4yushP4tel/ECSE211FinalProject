from robot import Robot
from utils.brick import reset_brick
import time


def main():
    robot = Robot()
        # List of functions to be tested

        # Helper functions:
    # robot.packages_delivered=1
    #robot.visit_office()
    
    #robot.exit_office()
        # robot.stop_robot()
        # robot.move_straight(1)
        # robot.move_straight(-1)
        # robot.drop_off_package()
        #while True:
         #   robot.readjust_alignment_if_necessary()
          #  robot.check_stop_emergency_event()
        # robot.stop_moving()
    #robot.drop_off_package()
    #robot.drop_off_package()

        # Main functions (subsystems):
        # robot.move_straight_until_color("black")
    #robot.move_straight_until_color("orange")
    #robot.move_straight_until_color("blue")
        # robot.validate_entrance()
    #robot.process_office()
        # robot.return_home()
    #robot.turn_x_degrees(90)

        # Full system integration function:
    #robot.start_delivery()
    reset_brick()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        reset_brick()
        
