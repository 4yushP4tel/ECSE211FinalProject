from robot import Robot
import threading
import time

def main():
    # this function should run the entire circuit
    robot = Robot()
    robot.move(20)

if __name__ == "__main__":
    main()