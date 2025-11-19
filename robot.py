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
RIGHT_TURNS = [ "room",
                "home_valid",
                "turn",
                "room",
                "home_invalid",
                "turn",
                "room",
                "home_valid",
                "room",
                "home_invalid",
                "turn" ]

class Robot:
    def __init__(self):
        self.right_turns_passed = 0
        self.packages_delivered = 0
        self.package_dropped = False
        self.room_swept = False
        self.location = "outside"
        self.right_wheel = Wheel('B')
        self.left_wheel = Wheel('C')
        self.drop_off_system = DropOffSystem('D')
        self.speaker = Speaker()
        self.us_sensor = UltrasonicSensor(1)
        self.color_sensing_system = ColorSensingSystem(4, 'A')
        self.emergency_touch_sensor = TouchSensor(2)
        self.move_thread = None
        self.go_home_flag = threading.Event()
        wait_ready_sensors()

    def turn_right(self, power):
        self.stop_moving()
        print("Turning right")
        while self.color_sensing_system.most_recent_color == "Black" and self.color_sensing_system.prev_color == "White":
            self.left_wheel.spin_wheel_continuously(power)
            self.right_wheel.spin_wheel_continuously(-power)
        self.stop_moving()
        self.us_sensor.wall_pointed_to = "long"

    def turn_left(self, power):
        self.stop_moving()
        print("Turning left")
        while self.color_sensing_system.most_recent_color == "Black" and self.color_sensing_system.prev_color == "White":
            self.left_wheel.spin_wheel_continuously(power)
            self.right_wheel.spin_wheel_continuously(-power)
        self.left_wheel.spin_wheel_continuously(-power)
        self.right_wheel.spin_wheel_continuously(power)
        self.us_sensor.wall_pointed_to = "short"

    def readjust_alignment(self, direction: str):
        # this would take info from the US sensor to check the distance from
        #the right wall and readjust if the distance is too large or small
        if direction == "ok":
            return
        
        self.stop_moving()
        readjustment_power = 15
        delay_time = 0.25

        if direction == "left":
            print("Readjusting left")
            # self.left_wheel.spin_wheel_continuously(-readjustment_power)
            self.right_wheel.spin_wheel_continuously(readjustment_power)
            time.sleep(delay_time)
            # self.left_wheel.stop_spinning()
            self.right_wheel.stop_spinning()

            # Counter-correction to straighten
            self.left_wheel.spin_wheel_continuously(readjustment_power)
            # self.right_wheel.spin_wheel_continuously(-readjustment_power // 2)
            time.sleep(delay_time)
            self.stop_moving()

        elif direction == "right":
            print("Readjusting right")
            # Turn slightly right
            self.left_wheel.spin_wheel_continuously(readjustment_power)
            self.right_wheel.spin_wheel_continuously(-readjustment_power)
            time.sleep(delay_time)
            self.stop_moving()

            # Counter-correction to straighten
            self.left_wheel.spin_wheel_continuously(-readjustment_power // 2)
            self.right_wheel.spin_wheel_continuously(readjustment_power // 2)
            time.sleep(delay_time / 2)
            self.stop_moving()

        with self.us_sensor.lock:
            direction = self.us_sensor.latest_direction
        
        print("Readjustment complete")

    def move(self, power:int):
        self.stop_moving()
        def move_loop():
            self.left_wheel.spin_wheel_continuously(power)
            self.right_wheel.spin_wheel_continuously(power)
            self.color_sensing_system.start_detecting_color()
            self.us_sensor.start_monitoring_distance()

            while true:
                if self.emergency_touch_sensor.is_pressed():
                    self.emergency_stop()

                with self.us_sensor.lock:
                    direction = self.us_sensor.latest_direction

                # Turn right on valid intersections
                if self.color_sensing_system.detect_hallway_on_right_flag.is_set():
                    print("Detected path on right")
                    self.stop_moving()
                    if self.location == "outside":
                        self.location = "hallway"
                    else:
                        self.location = "outside"
                    if RIGHT_TURNS[self.right_turns_passed] != "home_invalid":
                        self.turn_right(10)
                    elif RIGHT_TURNS[self.right_turns_passed] == "home_valid" and self.go_home_flag.is_set():
                        self.turn_right(10)
                    if RIGHT_TURNS[self.right_turns_passed]!= "home_invalid":
                        self.turn_right(10)
                    self.right_turns_passed += 1
                    self.left_wheel.spin_wheel_continuously(int(power/5))
                    self.right_wheel.spin_wheel_continuously(int(power/5))
                    self.color_sensing_system.detect_hallway_on_right_flag.clear()
                    self.room_swept = False
                # 180 on invalid offices
                elif self.color_sensing_system.detect_invalid_entrance_flag.is_set():
                    print("Invalid room, going back")
                    self.stop_moving()
                    self.left_wheel.rotate_wheel_continuously(90)
                    self.right_wheel.rotate_wheel_continuously(-90)
                    self.right_wheel.wait_is_stopped()
                    self.location = "outside"
                    self.left_wheel.spin_wheel_continuously(int(power/5))
                    self.right_wheel.spin_wheel_continuously(int(power/5))
                    self.color_sensing_system.detect_invalid_entrance_flag.clear()
                # Check room for valid entrance
                elif self.color_sensing_system.detect_valid_entrance_flag.is_set():
                    print("Valid room")
                    # Remains in mail room when done
                    if self.go_home_flag.is_set():
                        time.sleep(1)
                        break
                    self.color_sensing_system.detect_valid_entrance_flag.clear()
                # Sweep width of room to check for sticker
                elif self.color_sensing_system.detect_room.is_set() and not self.room_swept:
                    print("Sweeping area")
                    self.location = "room"
                    self.stop_moving()
                    if self.color_sensing_system.is_in_front:
                        self.color_sensing_system.move_sensor_to_side()
                    self.color_sensing_system.move_sensor_side_to_side()
                # Sweeping reaches end of room
                elif self.color_sensing_system.detect_room_end.is_set() and self.location == "room":
                    self.stop_moving()
                    self.turn_right(180)
                    self.left_wheel.spin_wheel_continuously(int(power / 5))
                    self.right_wheel.spin_wheel_continuously(int(power / 5))
                    self.color_sensing_system.detect_room_end.clear()
                    self.room_swept = True
                # Drop off package on green sticker
                elif self.color_sensing_system.detect_valid_sticker_flag.is_set():
                    print("Found green sticker")
                    self.stop_moving()
                    self.drop_off_package()
                    self.turn_right(180)
                    self.left_wheel.spin_wheel_continuously(int(power/5))
                    self.right_wheel.spin_wheel_continuously(int(power/5))
                    self.color_sensing_system.detect_valid_sticker_flag.clear()
                    self.room_swept = True

                if self.location == "outside" and direction != "ok":
                    self.readjust_alignment(direction)

                if self.location == "outside" and self.color_sensing_system.is_in_front:
                    self.color_sensing_system.move_sensor_to_side()
                elif self.location == "hallway" and self.package_dropped and self.color_sensing_system.is_in_front:
                    self.color_sensing_system.move_sensor_to_side()
                elif self.location == "hallway" and not self.package_dropped and not self.color_sensing_system.is_in_front:
                    self.color_sensing_system.move_sensor_to_front()
                self.package_dropped = False
            
            self.stop_moving()
            self.color_sensing_system.stop_detecting_color()
            self.us_sensor.stop_monitoring_distance()
                
        self.move_thread = threading.Thread(target=move_loop, daemon=True)
        self.move_thread.start()
    
    def stop_moving(self):
        self.left_wheel.stop_spinning()
        self.right_wheel.stop_spinning()

    def drop_off_package(self):
        self.stop_moving()
        self.speaker.play_delivery_tone()
        print("PACKED DROPPED")
        self.drop_off_system.deliver_package(self.packages_delivered)
        self.packages_delivered += 1
        self.package_dropped = True
        if self.packages_delivered == 2:
            self.go_home_flag.set()

    def emergency_stop(self):
        self.stop_moving()
        self.color_sensing_system.stop_detecting_color()
        self.us_sensor.stop_monitoring_distance()
        print("EMERGENCY STOP ACTIVATED")
        reset_brick()
        os._exit(1)