import os
import threading
import time

from components.gyro_sensor import GyroSensor
from components.color_sensing_system import ColorSensingSystem
from components.speaker import Speaker
from components.drop_off_system import DropOffSystem
from components.emergency_stop_system import EmergencyStopSystem
from utils.brick import reset_brick, wait_ready_sensors, Motor, TouchSensor


class Robot:
    REALIGNMENT_CORRECTION = 20
    DEFAULT_WHEEL_SPEED = 90
    LEFT_WHEEL_CORRECTION = 1.2
    RIGHT_WHEEL_CORRECTION = 1
    LEFT_WHEEL_SPEED_WITH_CORRECTION = DEFAULT_WHEEL_SPEED * LEFT_WHEEL_CORRECTION
    RIGHT_WHEEL_SPEED_WITH_CORRECTION = DEFAULT_WHEEL_SPEED * RIGHT_WHEEL_CORRECTION

    def __init__(self):
        self.packages_delivered = 0
        self.packages_dropped = False
        self.right_wheel = Motor('B')
        self.left_wheel = Motor('C')
        self.drop_off_system = DropOffSystem('A')
        self.speaker = Speaker()
        self.gyro_sensor = GyroSensor(4)
        self.color_sensing_system = ColorSensingSystem(3, 'D')
        self.emergency_touch_sensor = TouchSensor(1)
        wait_ready_sensors()

        # 3 threads
        self.gyro_sensor.start_monitoring_orientation()
        self.color_sensing_system.start_detecting_color()
        self.emergency_thread = None
        self.emergency_event = threading.Event()
        self.start_emergency_monitoring()

    # Main robot logic for the delivery
    def start_delivery(self):
        # Validate first office and process it if necessary
        self.move_straight_until_color("black")
        if self.packages_delivered < 2 and self.validate_entrance():
            self.process_office()

        # Skip first (invalid) mail
        self.move_straight_until_color("black")

        # Turn on first corner
        self.move_straight_until_color("black")
        self.turn_until_x_orientation(90)
        self.gyro_sensor.gyro_sensor.reset_measure()

        # Validate second office and process it if necessary
        self.move_straight_until_color("black")
        if self.packages_delivered < 2 and self.validate_entrance():
            self.process_office()

        # Visit second (valid) mail and return home if possible
        self.move_straight_until_color("black")
        if self.packages_delivered == 2:
            self.return_home()

        # Validate third office and process it if necessary
        self.move_straight_until_color("black")
        if self.packages_delivered < 2 and self.validate_entrance():
            self.process_office()

        # Turn on second corner
        self.move_straight_until_color("black")
        self.turn_until_x_orientation(90)
        self.gyro_sensor.gyro_sensor.reset_measure()

        # Skip third (invalid) mail
        self.move_straight_until_color("black")

        # Turn on third corner
        self.move_straight_until_color("black")
        self.turn_until_x_orientation(90)
        self.gyro_sensor.gyro_sensor.reset_measure()

        # Validate fourth office and process it if necessary
        self.move_straight_until_color("black")
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
            if self.emergency_event.is_set():
                self.emergency_event.clear()

            if self.color_sensing_system.detect_black_event.is_set() and color == "black":
                self.color_sensing_system.detect_black_event.clear()
                break
            elif self.color_sensing_system.detect_orange_event.is_set() and color == "orange":
                self.color_sensing_system.detect_orange_event.clear()
                break
            elif self.color_sensing_system.detect_blue_event.is_set() and color == "blue":
                self.color_sensing_system.detect_blue_event.clear()
                break

            # self.readjust_alignment_if_necessary()

        self.stop_moving()

    # Return False if color red detected at entrance and True otherwise
    def validate_entrance(self):
        print("Return False if color red detected at entrance and True otherwise")
        self.turn_until_x_orientation(90)
        self.color_sensing_system.sweeper.set_position(-90)
        self.move_straight(1)

        # 1 second to check entrance
        for i in range(20):
            if self.emergency_event.is_set():
                self.emergency_event.clear()
            time.sleep(0.05)

            if self.color_sensing_system.detect_red_event.is_set():
                self.color_sensing_system.detect_red_event.clear()
                self.stop_moving()
                self.turn_until_x_orientation(0)
                return False

        self.stop_moving()
        return True

    # Robot behaviour to process office and return back to initial path
    def process_office(self):
        self.visit_office()
        self.exit_office()

    def return_home(self):
        self.turn_until_x_orientation(90)
        self.move_straight_until_color("blue")
        self.emergency_stop()

    # Turn until current orientation of robot reaches desired orientation
    def turn_until_x_orientation(self, angle):
        print(f"Turn {angle - self.gyro_sensor.orientation} degrees (+ right, - left)")
        if angle > self.gyro_sensor.orientation:
            self.left_wheel.set_dps(Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
            self.right_wheel.set_dps(-Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
            while self.gyro_sensor.orientation < angle:
                pass
        elif angle < self.gyro_sensor.orientation:
            self.left_wheel.set_dps(-Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
            self.right_wheel.set_dps(Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
            while self.gyro_sensor.orientation > angle:
                pass
        else:
            return

        self.stop_moving()

    # Turn x degrees (+ right, - left)
    def turn_x_degrees(self, angle):
        print(f"Turn {angle} degrees (+ right, - left)")
        if angle > 0:
            self.left_wheel.set_dps(Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
            self.right_wheel.set_dps(-Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
            while self.gyro_sensor.orientation < angle:
                pass
        elif angle < 0:
            self.left_wheel.set_dps(-Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
            self.right_wheel.set_dps(Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
            while self.gyro_sensor.orientation > angle:
                pass
        else:
            return

        self.stop_moving()

    # Additional helper functions

    # Sweep office and drop package on green sticker
    def visit_office(self):
        print("Sweep office and drop package on green sticker")

        # 5 sweeps of the office
        for i in range(5):
            if self.emergency_event.is_set():
                self.emergency_event.clear()

            # Advance a little to cover the next area of the office
            self.move_straight(1)
            time.sleep(1)
            self.stop_moving()

            # Sweep across the width of the office
            self.color_sensing_system.sweeper.reset_encoder()
            self.color_sensing_system.sweeper.set_limits(dps=90)
            self.color_sensing_system.sweeper.set_position(-180)

            # Catch any green event if detected for 2 seconds and get the angle of the sweeper
            angle = 0

            for _ in range(60):
                if self.emergency_event.is_set():
                    self.emergency_event.clear()
                time.sleep(0.05)

                if self.color_sensing_system.detect_green_event.is_set() and not self.packages_dropped:
                    print("STOPPING ARM")
                    self.color_sensing_system.sweeper.set_dps(0)
                    self.stop_moving()
                    self.color_sensing_system.detect_green_event.clear()
                    print(f"ARM POSITION {self.color_sensing_system.sweeper.get_position()} ")
                    angle = (self.color_sensing_system.sweeper.get_position() + 90)
                    print(f"ANGLE: {angle}")

                    self.packages_dropped = True
            self.color_sensing_system.sweeper.wait_is_stopped()

            # Return sweeper back to default position
            self.color_sensing_system.sweeper.set_limits(dps=90)
            self.color_sensing_system.sweeper.set_position(0)
            self.color_sensing_system.sweeper.wait_is_stopped()
            time.sleep(2)

            # Drop package on green sticker if detected
            if self.packages_dropped:
                current_orientation = self.gyro_sensor.orientation
                self.turn_until_x_orientation(current_orientation + angle)
                self.drop_off_package()
                self.turn_until_x_orientation(current_orientation)
                break

    # Move backwards until color orange is detected
    def exit_office(self):
        print("Move backwards until color orange is detected")
        self.move_straight(-1)
        while not self.color_sensing_system.detect_orange_event.is_set():
            if self.emergency_event.is_set():
                self.emergency_event.clear()

        self.color_sensing_system.detect_orange_event.clear()
        self.stop_moving()
        self.turn_until_x_orientation(0)

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

    # Methods handling emergency stop and its thread
    def start_emergency_monitoring(self):
        # a dedicated thread to monitor the emergency button
        self.emergency_thread = threading.Thread(target=self.monitor_emergency_button, daemon=True)
        self.emergency_thread.start()
        print("Emergency monitoring thread started")

    def stop_emergency_monitoring(self):
        self.emergency_event.set()
        print("Emergency monitoring thread stopped")

    def monitor_emergency_button(self):
        # this runs in its own thread, all other functions should just return if
        # the button has been pressed
        while not self.emergency_event.is_set():
            if self.emergency_touch_sensor.is_pressed():
                self.emergency_event.set()
                print("EMERGENCY BUTTON PRESSED!")
                self.emergency_stop()
                self.emergency_event.clear()
                break
            time.sleep(0.05)

    def emergency_stop(self):
        self.stop_moving()
        self.color_sensing_system.stop_detecting_color()
        self.gyro_sensor.stop_monitoring_orientation()
        print("EMERGENCY STOP ACTIVATED")
        reset_brick()
        os._exit(1)
