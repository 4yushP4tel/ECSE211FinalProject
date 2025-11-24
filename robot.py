import os
import time

from components.gyro_sensor import GyroSensor
from components.color_sensing_system import ColorSensingSystem
from components.speaker import Speaker
from components.drop_off_system import DropOffSystem
from components.emergency_stop_system import EmergencyStopSystem
from utils.brick import reset_brick, wait_ready_sensors, Motor


class Robot:
    REALIGNMENT_CORRECTION = 15
    DEFAULT_WHEEL_SPEED = 90
    LEFT_WHEEL_CORRECTION = 0
    RIGHT_WHEEL_CORRECTION = 0
    LEFT_WHEEL_SPEED_WITH_CORRECTION = DEFAULT_WHEEL_SPEED + LEFT_WHEEL_CORRECTION
    RIGHT_WHEEL_SPEED_WITH_CORRECTION = DEFAULT_WHEEL_SPEED + RIGHT_WHEEL_CORRECTION

    def __init__(self):
        self.packages_delivered = 0
        self.packages_dropped = False
        self.right_wheel = Motor('B')
        self.left_wheel = Motor('C')
        self.drop_off_system = DropOffSystem('A')
        self.speaker = Speaker()
        self.gyro_sensor = GyroSensor(4)
        self.color_sensing_system = ColorSensingSystem(3, 'D')
        self.emergency_touch_sensor = EmergencyStopSystem(1)
        wait_ready_sensors()

        # 3 threads
        self.gyro_sensor.start_monitoring_orientation()
        self.color_sensing_system.start_detecting_color()
        self.emergency_touch_sensor.start_detecting_emergency()

    # Main robot logic for the delivery
    def start_delivery(self):
        # Validate first office and process it if necessary
        self.move_straight_until_color("orange")
        if self.packages_delivered < 2 and self.validate_entrance():
            self.process_office()

        # Skip first (invalid) mail
        self.move_straight_until_color("black")

        # Turn on first corner
        self.move_straight_until_color("black")
        self.turn_x_degrees(88)

        # Validate second office and process it if necessary
        self.move_straight_until_color("orange")
        if self.packages_delivered < 2 and self.validate_entrance():
            self.process_office()

        # Visit second (valid) mail and return home if possible
        self.move_straight_until_color("black")
        if self.packages_delivered == 2:
            self.return_home()

        # Validate third office and process it if necessary
        self.move_straight_until_color("orange")
        if self.packages_delivered < 2 and self.validate_entrance():
            self.process_office()

        # Turn on second corner
        self.move_straight_until_color("black")
        self.turn_x_degrees(88)

        # Skip third (invalid) mail
        self.move_straight_until_color("black")

        # Turn on third corner
        self.move_straight_until_color("black")
        self.turn_x_degrees(88)

        # Validate fourth office and process it if necessary
        self.move_straight_until_color("orange")
        if self.packages_delivered < 2 and self.validate_entrance():
            self.process_office()

        # Visit fourth (valid) mail and return home whether failed or not
        self.move_straight_until_color("black")
        self.return_home()

    # Main functions for robot logic
    
    # Move straight until specified color is detected
    def move_straight_until_color(self, color):
        print(f"Move straight until color {color} is detected")
        self.move_straight(1)
        while True:
            if self.color_sensing_system.detect_black_event.is_set() and color == "black":
                self.color_sensing_system.detect_black_event.clear()
                break
            elif self.color_sensing_system.detect_orange_event.is_set() and color == "orange":
                self.color_sensing_system.detect_orange_event.clear()
                break
            elif self.color_sensing_system.detect_blue_event.is_set() and color == "blue":
                self.color_sensing_system.detect_blue_event.clear()
                break
            
            self.check_stop_emergency_event()
            self.readjust_alignment_if_necessary()

        self.stop_moving()

    # Return False if color red detected at entrance and True otherwise
    def validate_entrance(self):
        print("Return False if color red detected at entrance and True otherwise")
        self.move_straight(1)

        # 2 seconds to check entrance
        while time.time() - time.time() < 2:
            self.check_stop_emergency_event()

            if self.color_sensing_system.detect_red_event.is_set():
                self.color_sensing_system.detect_red_event.clear()
                self.stop_moving()
                return False

        self.stop_moving()
        return True

    # Robot behaviour to process office and return back to initial path
    def process_office(self):
        self.turn_x_degrees(88)
        self.visit_office()
        self.exit_office()
        self.turn_x_degrees(-88)

    def return_home(self):
        self.turn_x_degrees(88)
        self.move_straight_until_color("blue")
        self.stop_robot()

    # Turn x degrees (+ right, - left)
    def turn_x_degrees(self, angle):
        print(f"Turn {angle} degrees (+ right, - left)")
        if angle > 0:
            self.left_wheel.set_dps(Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
            self.right_wheel.set_dps(-Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
        elif angle < 0:
            self.left_wheel.set_dps(-Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
            self.right_wheel.set_dps(Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
        else:
            return

        while self.gyro_sensor.gyro_sensor.get_abs_measure() < angle:
            pass

        self.stop_moving()
        self.gyro_sensor.gyro_sensor.reset_measure()

    # Additional helper functions

    # Sweep office and drop package on green sticker
    def visit_office(self):
        print("Sweep office and drop package on green sticker")

        # 5 sweeps of the office
        for _ in range(5) and not self.packages_dropped:
            self.check_stop_emergency_event()

            # Advance a little to cover the next area of the office
            self.move_straight(1)
            time.sleep(1)
            self.stop_moving()

            # Sweep across the width of the office
            self.color_sensing_system.sweeper.reset_encoder()
            self.color_sensing_system.sweeper.set_position(180)

            # Catch any green event if detected for 2 seconds and get the angle of the sweeper
            angle = 0
            while time.time() - time.time() < 2:
                self.check_stop_emergency_event()

                if self.color_sensing_system.detect_green_event.is_set():
                    self.color_sensing_system.detect_green_event.clear()
                    angle = -(self.color_sensing_system.sweeper.get_position() - 90)
                    self.packages_dropped = True
            self.color_sensing_system.sweeper.wait_is_stopped()

            # Return sweeper back to default position
            self.color_sensing_system.sweeper.set_position(-180)
            self.color_sensing_system.sweeper.wait_is_stopped()

            # Drop package on green sticker if detected
            if self.packages_dropped:
                self.turn_x_degrees(angle)
                self.drop_off_package()
                self.turn_x_degrees(-angle)

    # Move backwards until color orange is detected
    def exit_office(self):
        print("Move backwards until color orange is detected")
        self.move_straight(-1)
        while not self.color_sensing_system.detect_orange_event.is_set():
            self.check_stop_emergency_event()

        self.color_sensing_system.detect_orange_event.clear()
        self.stop_moving()

    # Shut down and exit program
    def stop_robot(self):
        print("Shut down and exit program")
        self.stop_moving()
        self.color_sensing_system.stop_detecting_color()
        self.gyro_sensor.stop_monitoring_orientation()
        self.emergency_touch_sensor.stop_detecting_emergency()
        reset_brick()
        os._exit(1)

    # Move straight
    def move_straight(self, direction):
        print("Move straight")
        self.left_wheel.set_dps(direction * Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
        self.right_wheel.set_dps(direction * Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)

    # Readjust alignment to move straight if necessary
    def readjust_alignment_if_necessary(self):
        if self.gyro_sensor.readjust_right_event.is_set():
            self.left_wheel.set_dps(Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION + Robot.REALIGNMENT_CORRECTION)
            self.right_wheel.set_dps(Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
            self.gyro_sensor.readjust_right_event.clear()
        elif self.gyro_sensor.readjust_left_event.is_set():
            self.left_wheel.set_dps(Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
            self.right_wheel.set_dps(Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION + Robot.REALIGNMENT_CORRECTION)
            self.gyro_sensor.readjust_left_event.clear()
        else:
            self.left_wheel.set_dps(Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
            self.right_wheel.set_dps(Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)

    # Stop all movement of wheels
    def stop_moving(self):
        print("Stop all movement of wheels")
        self.left_wheel.set_dps(0)
        self.right_wheel.set_dps(0)
        time.sleep(1)

    # Drop off package and play sound
    def drop_off_package(self):
        print("Drop off package and play sound")
        self.stop_moving()
        self.drop_off_system.deliver_package(self.packages_delivered)
        self.speaker.play_delivery_tone()
        self.packages_delivered += 1
        self.packages_dropped = False

    # Check if emergency event is set
    def check_stop_emergency_event(self):
        if self.emergency_touch_sensor.stop_emergency_event.is_set():
            self.stop_robot()