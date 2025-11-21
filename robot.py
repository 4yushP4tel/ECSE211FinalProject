import os
import time

from components.us_sensor import UltrasonicSensor
from components.color_sensing_system import ColorSensingSystem
from components.speaker import Speaker
from components.drop_off_system import DropOffSystem
from components.emergency_stop_system import EmergencyStopSystem
from utils.brick import reset_brick, wait_ready_sensors, Motor


class Robot:
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
        self.us_sensor = UltrasonicSensor(1)
        self.color_sensing_system = ColorSensingSystem(2, 'D')
        self.emergency_touch_sensor = EmergencyStopSystem(3)
        wait_ready_sensors()

        # 3 threads
        self.us_sensor.start_monitoring_distance()
        self.color_sensing_system.start_detecting_color()
        self.emergency_touch_sensor.start_detecting_emergency()

    # Main robot logic for the delivery
    def start_delivery(self):
        # Visit first office and process it if necessary
        self.move_straight_until_office()
        if self.packages_delivered < 2 and self.validate_entrance():
            self.turn_right_90()
            self.process_office()
            self.exit_office()
            self.turn_left_90()

        # Skip first (invalid) mail
        self.move_straight_until_black_line()

        # Turn on first corner
        self.move_straight_until_black_line()
        self.turn_right_90()

        # Visit second office and process it if necessary
        self.move_straight_until_office()
        if self.packages_delivered < 2 and self.validate_entrance():
            self.turn_right_90()
            self.process_office()
            self.exit_office()
            self.turn_left_90()

        # Visit second (valid) mail and return home if possible
        self.move_straight_until_black_line()
        if self.packages_delivered == 2:
            self.turn_right_90()
            self.move_straight_until_mail()
            self.stop_robot()

        # Visit third office and process it if necessary
        self.move_straight_until_office()
        if self.packages_delivered < 2 and self.validate_entrance():
            self.turn_right_90()
            self.process_office()
            self.exit_office()
            self.turn_left_90()

        # Turn on second corner
        self.move_straight_until_black_line()
        self.turn_right_90()

        # Skip third (invalid) mail
        self.move_straight_until_black_line()

        # Turn on third corner
        self.move_straight_until_black_line()
        self.turn_right_90()

        # Visit fourth office and process it if necessary
        self.move_straight_until_office()
        if self.packages_delivered < 2 and self.validate_entrance():
            self.turn_right_90()
            self.process_office()
            self.exit_office()
            self.turn_left_90()

        # Visit fourth (valid) mail and return home whether failed or not
        self.move_straight_until_black_line()
        self.turn_right_90()
        self.move_straight_until_mail()
        self.stop_robot()

    # Main functions for robot logic

    # Move straight until color black is detected
    def move_straight_until_black_line(self):
        print("Move straight until color black is detected")
        self.move_straight(1)
        while not self.color_sensing_system.detect_black_event.is_set():
            self.check_stop_emergency_event()

        self.color_sensing_system.detect_black_event.clear()
        self.stop_moving()

    # Move straight until color orange is detected
    def move_straight_until_office(self):
        print("Move straight until color orange is detected")
        self.move_straight(1)
        while not self.color_sensing_system.detect_orange_event.is_set():
            self.check_stop_emergency_event()

        self.color_sensing_system.detect_orange_event.clear()
        self.stop_moving()

    # Move straight until color blue is detected
    def move_straight_until_mail(self):
        print("Move straight until color blue is detected")
        self.move_straight(1)
        while not self.color_sensing_system.detect_blue_event.is_set():
            self.check_stop_emergency_event()

        self.color_sensing_system.detect_blue_event.clear()
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

    # Sweep office and drop package on green sticker
    def process_office(self):
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
                    angle = self.color_sensing_system.sweeper.get_position() - 90
                    self.packages_dropped = True
            self.color_sensing_system.sweeper.wait_is_stopped()

            # Return sweeper back to default position
            self.color_sensing_system.sweeper.set_position(-180)
            self.color_sensing_system.sweeper.wait_is_stopped()

            # Drop package on green sticker if detected
            # We could probably use the gyro sensor to have the exact alignment with the green sticker
            if self.packages_dropped:
                if angle < 0:
                    self.left_wheel.set_dps(Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
                    self.right_wheel.set_dps(-Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
                    time.sleep(0.01 * abs(angle))

                    self.stop_moving()
                    self.drop_off_package()

                    self.left_wheel.set_dps(-Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
                    self.right_wheel.set_dps(Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
                    time.sleep(0.01 * abs(angle))
                else:
                    self.left_wheel.set_dps(-Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
                    self.right_wheel.set_dps(Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
                    time.sleep(0.01 * abs(angle))

                    self.stop_moving()
                    self.drop_off_package()

                    self.left_wheel.set_dps(Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
                    self.right_wheel.set_dps(-Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
                    time.sleep(0.01 * abs(angle))

    # Move backwards until color orange is detected
    def exit_office(self):
        print("Move backwards until color orange is detected")
        self.move_straight(-1)
        while not self.color_sensing_system.detect_orange_event.is_set():
            self.check_stop_emergency_event()

        self.color_sensing_system.detect_orange_event.clear()
        self.stop_moving()

    # Turn 90 degrees to the right
    def turn_right_90(self):
        print("Turn 90 degrees to the right")
        self.left_wheel.set_dps(Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
        self.right_wheel.set_dps(-Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
        time.sleep(3)
        self.stop_moving()

    # Turn 90 degrees to the left
    def turn_left_90(self):
        print("Turn 90 degrees to the left")
        self.left_wheel.set_dps(Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
        self.right_wheel.set_dps(-Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)
        time.sleep(3)
        self.stop_moving()

    # Shut down and exit program
    def stop_robot(self):
        print("Shut down and exit program")
        self.stop_moving()
        self.color_sensing_system.stop_detecting_color()
        self.us_sensor.stop_monitoring_distance()
        self.emergency_touch_sensor.stop_detecting_emergency()
        reset_brick()
        os._exit(1)

    # Additional helper functions

    # Move straight
    def move_straight(self, direction):
        print("Move straight")
        self.left_wheel.set_dps(direction * Robot.LEFT_WHEEL_SPEED_WITH_CORRECTION)
        self.right_wheel.set_dps(direction * Robot.RIGHT_WHEEL_SPEED_WITH_CORRECTION)

    # Stop all movement of wheels
    def stop_moving(self):
        print("Stop all movement of wheels")
        self.left_wheel.set_dps(0)
        self.right_wheel.set_dps(0)

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