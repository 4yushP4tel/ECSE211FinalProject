from robot import Robot
from utils.brick import reset_brick
import time


def main():
    robot = Robot()
    try:
        # List of functions to be tested

        # Helper functions:
        # 1 for forward and -1 for backward
        # robot.move_straight(1)
        # robot.move_straight(-1)
        # robot.drop_off_package()
        # while True:
        #   robot.readjust_alignment_if_necessary()
        #   check_stop_emergency_event()

        # Main functions (subsystems):
        # robot.move_straight_until_color("black")
        # robot.move_straight_until_color("orange")
        # robot.move_straight_until_color("blue")
        # robot.validate_entrance()
        # robot.process_office()
        # robot.exit_office()
        # robot.turn_x_degrees(angle)
        # robot.stop_robot()

        # Full system integration function:
        # robot.start_delivery()
        pass

    except KeyboardInterrupt:
        robot.stop_robot()


if __name__ == "__main__":
    main()
