from robot import Robot
from utils.brick import reset_brick
import time


def main():
    robot = Robot()
    try:
        # List of functions to be tested

        # Helper functions:
        # 1 for forward and -1 for backward
        robot.move_straight(1)
        # robot.move_straight(-1)
        # robot.drop_off_package()

        # Main functions (subsystems):
        # robot.move_straight_until_black_line()
        # robot.move_straight_until_office()
        # robot.move_straight_until_mail()
        # robot.validate_entrance()
        # robot.process_office()
        # robot.exit_office()
        # robot.turn_right_90()
        # robot.turn_left_90()
        # robot.stop_robot()

        # Full system integration function:
        # robot.start_delivery()

    except KeyboardInterrupt:
        robot.stop_robot()


if __name__ == "__main__":
    main()
