import os
import sys
import time
from components.wheel import Wheel
from components.us_sensor import UltrasonicSensor
from components.color_sensing_system import ColorSensingSystem
from components.speaker import Speaker
from components.drop_off_system import DropOffSystem
from utils.brick import TouchSensor, reset_brick, wait_ready_sensors
import threading

# This will store what each right turn which we detect means
RIGHT_TURNS = ["room",
               "home_valid",
               "turn",
               "room",
               "home_invalid",
               "turn",
               "room",
               "home_valid",
               "room",
               "home_invalid",
               "turn"]


class Robot:
    def __init__(self):
        self.right_turns_passed = 0
        self.packages_delivered = 0
        self.package_dropped = False
        self.room_swept = False
        self.location = "outside"
        self.right_wheel = Wheel('B')
        self.left_wheel = Wheel('C')
        self.drop_off_system = DropOffSystem('A')
        self.speaker = Speaker()
        self.us_sensor = UltrasonicSensor(1)
        self.color_sensing_system = ColorSensingSystem(2, 'D')
        self.emergency_touch_sensor = TouchSensor(3)
        self.move_thread = None
        self.go_home_flag = threading.Event()
        wait_ready_sensors()

    def start_delivery(self, power: int):
        self.stop_moving()
        self.color_sensing_system.start_detecting_color()
        self.color_sensing_system.start_sweep()
        self.us_sensor.start_monitoring_distance()

        while True:
            if self.emergency_touch_sensor.is_pressed():
                self.emergency_stop()

            with self.us_sensor.lock:
                direction = self.us_sensor.latest_readjustment_direction

            # Turn right on valid intersections (color BLACK)
            if self.color_sensing_system.detect_hallway_on_right_flag.is_set() and self.location == "outside":
                self.turn_right_valid()

            # Exit on invalid offices or upon completion (color RED or color YELLOW prev and ORANGE)
            elif self.location == "hallway" and (self.color_sensing_system.detect_invalid_entrance_flag.is_set() or self.color_sensing_system.detect_room_exit_flag.is_set()):
                self.turn_back_to_outside()

            # Go in mail room and remain inside after job done (color BLUE)
            elif self.color_sensing_system.detect_home_flag.is_set() and self.go_home_flag.is_set():
                self.return_to_mail_room()

            # Drop off package on green sticker (color GREEN)
            elif self.color_sensing_system.detect_valid_sticker_flag.is_set() and self.location == "hallway" and not self.room_swept:
                self.drop_package_on_sticker()

            # Sweep room (color ORANGE or YELLOW)
            elif self.color_sensing_system.detect_room_flag.is_set() and not self.room_swept:
                self.sweep_room()

            # Turn back when end of room reached (color YELLOW prev and WHITE)
            elif self.color_sensing_system.detect_room_end_flag.is_set():
                self.room_end_return()

            # Adjust robot wheel movement
            self.adjust_movement()

    def turn_right_valid(self):
        print("Detected path on (color BLACK)")
        self.stop_moving()
        self.location = "hallway"

        if RIGHT_TURNS[self.right_turns_passed] == "home_valid" and not self.go_home_flag.is_set():
            pass
        elif RIGHT_TURNS[self.right_turns_passed] != "home_invalid":
            self.turn_right_90()
            if RIGHT_TURNS[self.right_turns_passed] == "room":
                self.room_swept = False
                self.color_sensing_system.stop_sweep_flag.clear()

        self.right_turns_passed += 1
        self.color_sensing_system.detect_hallway_on_right_flag.clear()

    def turn_back_to_outside(self):
        print("Go back to outside (color RED or color YELLOW prev and ORANGE)")
        self.location = "outside"
        self.stop_moving()
        self.color_sensing_system.stop_sweep_flag.set()
        self.turn_left_90()
        self.room_swept = False
        self.color_sensing_system.detect_invalid_entrance_flag.clear()

    def return_to_mail_room(self):
        print("Detected mail room (color BLUE)")
        self.right_wheel.spin_wheel_continuously(power)
        self.left_wheel.spin_wheel_continuously(power)
        time.sleep(3)
        self.color_sensing_system.detect_home_flag.clear()
        self.emergency_stop()

    def drop_package_on_sticker(self):
        print("Found green sticker (color GREEN)")
        self.stop_moving()
        self.color_sensing_system.stop_sweep_flag.set()

        # Rotate to sticker, drop package and go back to original alignment
        angle = self.color_sensing_system.motor_position
        self.right_wheel.rotate_wheel_degrees(angle)
        self.left_wheel.rotate_wheel_degrees(-angle)
        self.right_wheel.motor.wait_is_stopped()
        self.drop_off_package()
        self.right_wheel.rotate_wheel_degrees(-angle)
        self.left_wheel.rotate_wheel_degrees(angle)
        self.right_wheel.motor.wait_is_stopped()

        # Flag robot to back out of room
        self.room_swept = True
        self.color_sensing_system.detect_valid_sticker_flag.clear()

    def sweep_room(self):
        if self.color_sensing_system.stop_sweep_flag.is_set():
            self.color_sensing_system.stop_sweep_flag.clear()
        self.color_sensing_system.detect_room_flag.clear()

    def room_end_return(self):
        self.room_swept = True
        self.color_sensing_system.detect_room_end_flag.clear()

    def adjust_movement(self):
        if self.location == "outside":
            self.readjust_alignment(direction, base_power=power)
        elif self.room_swept:
            self.left_wheel.spin_wheel_continuously(-power)
            self.right_wheel.spin_wheel_continuously(-power)
        else:
            self.left_wheel.spin_wheel_continuously(power)
            self.right_wheel.spin_wheel_continuously(power)

    def turn_right_90(self, power=15, right_turn_90_deg_delay=1.5):
        self.stop_moving()
        print("Turning right")
        self.left_wheel.spin_wheel_continuously(power)
        self.right_wheel.spin_wheel_continuously(-power)
        time.sleep(right_turn_90_deg_delay)
        self.stop_moving()

    def turn_left_90(self, power=15, left_turn_90_deg_delay=1.5):
        self.stop_moving()
        print("Turning left")
        self.left_wheel.spin_wheel_continuously(-power)
        self.right_wheel.spin_wheel_continuously(power)
        time.sleep(left_turn_90_deg_delay)
        self.stop_moving()

    def readjust_alignment(self, direction: str, base_power=20, correction=8):
        # If direction == "ok", just drive straight
        if direction == "ok":
            self.left_wheel.spin_wheel_continuously(base_power)
            self.right_wheel.spin_wheel_continuously(base_power)
            return

        # If robot is too close to wall → turn slightly left
        if direction == "left":
            self.left_wheel.spin_wheel_continuously(base_power - correction)
            self.right_wheel.spin_wheel_continuously(base_power + correction)
        # If robot is too far from wall → turn slightly right
        elif direction == "right":
            self.left_wheel.spin_wheel_continuously(base_power + correction)
            self.right_wheel.spin_wheel_continuously(base_power - correction)

    def stop_moving(self):
        self.left_wheel.stop_spinning()
        self.right_wheel.stop_spinning()

    def drop_off_package(self):
        self.stop_moving()
        self.drop_off_system.deliver_package(self.packages_delivered)
        self.speaker.play_delivery_tone()
        print("PACKAGED DROPPED")
        self.packages_delivered += 1
        self.package_dropped = True
        if self.packages_delivered == 2:
            self.go_home_flag.set()

    def emergency_stop(self):
        self.stop_moving()
        self.color_sensing_system.stop_detecting_color()
        self.color_sensing_system.stop_sweep()
        self.us_sensor.stop_monitoring_distance()
        print("EMERGENCY STOP ACTIVATED")
        reset_brick()
        os._exit(1)
