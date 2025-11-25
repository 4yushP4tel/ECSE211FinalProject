import os
import re
import sys
import time
from components.wheel import Wheel
from components.gyro_sensor import GyroSensor
from components.color_sensing_system import ColorSensingSystem
from components.speaker import Speaker
from components.drop_off_system import DropOffSystem
from utils.brick import TouchSensor, reset_brick, wait_ready_sensors
import threading

# This will store what each right turn which we detect means
RIGHT_TURNS = [ "room",
                "home_invalid",
                "turn",
                "room",
                "home_valid",
                "room",
                "turn",
                "home_invalid",
                "turn",
                "room",
                "home_valid"]

class Robot:
    FORWARD_MOVEMENT_POWER_RIGHT=15
    FORWARD_MOVEMENT_POWER_LEFT=FORWARD_MOVEMENT_POWER_RIGHT*1.25
    POWER_FOR_TURN=15
    EXIT_ROOM_POWER=10
    
    CHECK_READJUST_TIME_INTERVAL = 0.1
    def __init__(self):
        self.packages_dropped=False
        self.right_turns_passed = 0
        self.packages_delivered = 0
        self.right_wheel = Wheel('B')
        self.left_wheel = Wheel('C')
        self.drop_off_system = DropOffSystem('A')
        self.speaker = Speaker()
        self.gyro_sensor = GyroSensor(4)
        self.color_sensing_system = ColorSensingSystem(3, 'D')
        self.emergency_touch_sensor = TouchSensor(1)
        self.go_home = False 
        self.emergency_button_listener_thread = None
        self.emergency_flag = threading.Event()
        self.wheel_lock=threading.Lock() # using this to ensure no conflicts with emergency stop and main thread
        wait_ready_sensors()
        time.sleep(1)  # give some time to stabilize sensors

    def main(self):
        self.start_emergency_monitoring()
        self.color_sensing_system.start_detecting_color()
        self.gyro_sensor.start_monitoring_orientation()
        self.move_in_hallway() 
        self.stop_moving()
        self.color_sensing_system.stop_detecting_color()
        self.gyro_sensor.stop_monitoring_orientation() 

    def start_emergency_monitoring(self):
        # a dedicated thread to monitor the emergency button
        self.emergency_thread = threading.Thread(target=self.monitor_emergency_button, daemon=True)
        self.emergency_thread.start()
        print("Emergency monitoring thread started")
    
    def monitor_emergency_button(self):
        #this runs in its own thread, all other functions should just return if
        #the button has been pressed
        while not self.emergency_flag.is_set():
            if self.emergency_touch_sensor.is_pressed():
                self.emergency_flag.set()
                print("EMERGENCY BUTTON PRESSED!")
                self.emergency_stop()
                self.emergency_flag.clear()
                break
            time.sleep(0.05)

    def turn_x_deg(self, angle, power=POWER_FOR_TURN):
        print(f"Turn {angle} degrees (+ right, - left)")
        if angle > 0:
            self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT)
            self.right_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            while self.gyro_sensor.orientation < angle:
                pass
        elif angle < 0:
            self.left_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_LEFT)
            self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            while self.gyro_sensor.orientation > angle:
                pass
        else:
            return

        self.stop_moving()
        self.gyro_sensor.reset_orientation()

    def readjust_alignment(self):
        # this would take info from the US sensor to check the distance from
        #the right wall and readjust if the distance is too large or small
        readjust_power_increase = 5
        print("Readjusting")
        while True:
            if self.emergency_flag.is_set():
                self.emergency_stop()
            with self.gyro_sensor.orientation_lock:
                current = self.gyro_sensor.orientation
            
            if abs(current) <= 1:
                print("Alignment OK")
                self.stop_moving()
                break

            if current>0:
                with self.wheel_lock:
                    self.left_wheel.spin_wheel_continuously(Robot.FORWARD_MOVEMENT_POWER_LEFT)
                    self.right_wheel.spin_wheel_continuously(Robot.FORWARD_MOVEMENT_POWER_RIGHT + readjust_power_increase)
            else:
                with self.wheel_lock:
                    self.left_wheel.spin_wheel_continuously(Robot.FORWARD_MOVEMENT_POWER_LEFT+readjust_power_increase)
                    self.right_wheel.spin_wheel_continuously(-Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            time.sleep(Robot.CHECK_READJUST_TIME_INTERVAL)
        if self.gyro_sensor.readjust_robot_flag.is_set():
            self.gyro_sensor.readjust_robot_flag.clear()
        print("Readjustment complete")

    def move_in_hallway(self):
        while True:
            if self.emergency_flag.is_set():
                self.emergency_stop()
            
            #if self.gyro_sensor.readjust_robot_flag.is_set():
            #    with self.gyro_sensor.orientation_lock:
            #        self.readjust_alignment()
            else:
                with self.wheel_lock:
                    self.left_wheel.spin_wheel_continuously(Robot.FORWARD_MOVEMENT_POWER_LEFT)
                    self.right_wheel.spin_wheel_continuously(Robot.FORWARD_MOVEMENT_POWER_RIGHT)

            # Turn right on valid intersections and then start moving again
            if self.color_sensing_system.detect_hallway_on_right_flag.is_set():
                self.color_sensing_system.detect_hallway_on_right_flag.clear()
                print("Detected path on right")
                time.sleep(0.5)
                self.stop_moving()

                if self.right_turns_passed >= len(RIGHT_TURNS):
                    print("No more RIGHT_TURNS entries — ignoring right path")
                    continue

                turn_detected = RIGHT_TURNS[self.right_turns_passed]
                print(f"<-----------------this was deetcted: {turn_detected}----------------------->")

                if turn_detected == "home_valid" and self.go_home:
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.turn_x_deg(90)
                    self.gyro_sensor.reset_orientation()
                    self.gyro_sensor.check_if_moving_straight_on_path = True
                    self.right_turns_passed += 1
                    self.head_home_after_turn()
                    break

                elif turn_detected == "home_invalid":
                    self.right_turns_passed += 1

                elif turn_detected == "turn":
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.turn_x_deg(90)
                    self.gyro_sensor.reset_orientation()
                    self.gyro_sensor.check_if_moving_straight_on_path = True
                    self.gyro_sensor.reset_orientation()
                    self.right_turns_passed += 1
                    
                elif turn_detected == "room" and not self.go_home:
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.turn_x_deg(90)
                    self.right_turns_passed += 1
                    self.detected_room_action()
                    self.gyro_sensor.reset_orientation()
                    self.gyro_sensor.check_if_moving_straight_on_path = True
                
    def stop_moving(self):
        with self.wheel_lock:
            self.left_wheel.stop_spinning()
            self.right_wheel.stop_spinning()
    
    def detected_room_action(self):
        """
        this is done after turning right at some room
        """
        self.color_sensing_system.move_sensor_to_front()
        time.sleep(0.5)
        while not self.color_sensing_system.detect_invalid_entrance_flag.is_set() and \
            not self.color_sensing_system.detect_valid_entrance_flag.is_set():
            if self.emergency_flag.is_set():
                return
            with self.wheel_lock:
                self.left_wheel.spin_wheel_continuously(Robot.FORWARD_MOVEMENT_POWER_LEFT)
                self.right_wheel.spin_wheel_continuously(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            time.sleep(0.05)
        self.stop_moving()

        if self.color_sensing_system.detect_valid_entrance_flag.is_set():
            self.color_sensing_system.detect_valid_entrance_flag.clear()
            print("detected valid entrance")
            self.handle_non_meeting_room()
        elif self.color_sensing_system.detect_invalid_entrance_flag.is_set():
            self.color_sensing_system.detect_invalid_entrance_flag.clear()
            print("detected invalid entrance")
            self.stop_moving()
            self.handle_meeting_room()
        self.color_sensing_system.move_sensor_to_right_side()
    
    def handle_non_meeting_room(self)->int:
            #returns the angle at which the color sensor detects the green sticker
        self.color_sensing_system.move_sensor_to_right_side()
        self.move_slightly_forward_for_sweep(sleep=1) # this is just to allow the robot to be lined up
        for i in range(7): # check this out if this actually works
            if self.emergency_flag.is_set():
                self.emergency_stop()
            
            # Advance a little to cover the next area of the office
            self.move_slightly_forward_for_sweep()

            # Sweep across the width of the office
            self.color_sensing_system.motor.reset_encoder()
            self.color_sensing_system.motor.set_limits(dps=90)
            self.color_sensing_system.motor.set_position(-180)

            # Catch any green event if detected for 2 seconds and get the angle of the sweeper
            angle = 0
            
            for _ in range(60):
                if self.emergency_flag.is_set():
                    self.emergency_stop()
                time.sleep(0.05)

                if self.color_sensing_system.detect_valid_sticker_flag.is_set() and not self.packages_dropped:
                    print("STOPPING ARM")
                    self.color_sensing_system.motor.set_dps(0)
                    
                    self.stop_moving()
                    self.color_sensing_system.detect_valid_sticker_flag.clear()
                    # color arm zero at right
                    print(f"ARM POSITION {self.color_sensing_system.motor.get_position()} ")
                    angle = (self.color_sensing_system.motor.get_position() + 90)
                    print(f"ANGLE: {angle}")
                    
                    self.packages_dropped = True
            self.color_sensing_system.motor.wait_is_stopped()

            # Return sweeper back to default position
            self.color_sensing_system.motor.set_limits(dps=90)
            self.color_sensing_system.motor.set_position(0)
            self.color_sensing_system.motor.wait_is_stopped()
            time.sleep(3)

            # Drop package on green sticker if detected
            if self.packages_dropped:
                self.turn_x_deg(angle)
                self.drop_off_package()
                self.turn_x_deg(-(angle / 20))
                # reset_brick()
                break
        self.return_in_hallway_after_delivery()
            
    def return_in_hallway_after_delivery(self):
        self.color_sensing_system.move_sensor_to_right_side()
        with self.wheel_lock:
            self.left_wheel.spin_wheel_continuously(-Robot.EXIT_ROOM_POWER*1.25)
            self.right_wheel.spin_wheel_continuously(-Robot.EXIT_ROOM_POWER)
        while not self.color_sensing_system.detect_room_exit_flag.is_set():
            time.sleep(0.01)
        time.sleep(2)
        self.stop_moving()
        self.turn_x_deg(270)
        self.color_sensing_system.detect_room_exit_flag.clear()

    def handle_meeting_room(self):
        self.turn_x_deg(-90)
        self.color_sensing_system.move_sensor_to_right_side()
    
    def head_home_after_turn(self):
        # might need to add some code to be able to readjust if needed since the 
        # distance is very large
        if not self.color_sensing_system.is_in_front:
            self.color_sensing_system.move_sensor_to_front()

        while not self.color_sensing_system.detect_entered_home_flag.is_set():

            if self.gyro_sensor.readjust_robot_flag.is_set():
                with self.gyro_sensor.orientation_lock:
                    self.readjust_alignment()
            else:
                with self.wheel_lock:
                    self.left_wheel.spin_wheel_continuously(Robot.FORWARD_MOVEMENT_POWER_LEFT)
                    self.right_wheel.spin_wheel_continuously(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            time.sleep(0.05)
        # exits the loop as soon as the flag is set
        # let the robot move a little more forward into the room before stopping it
        time.sleep(2)
        self.stop_moving()
        self.color_sensing_system.detect_entered_home_flag.clear()
        self.speaker.play_mission_complete_tone()
        print("MISSION COMPLETE. ROBOT IS HOME.")
        self.emergency_stop()
            
    def drop_off_package(self):
        self.stop_moving()
        self.drop_off_system.deliver_package(self.packages_delivered)
        self.speaker.play_delivery_tone()
        print("PACKED DROPPED")
        self.packages_delivered += 1
        if self.packages_delivered == 2:
            self.go_home = True

    def move_slightly_forward_for_sweep(self, sleep = 0.75):
        move_forward_speed = 12
        with self.wheel_lock:
            self.left_wheel.spin_wheel_continuously(move_forward_speed*1.25)
            self.right_wheel.spin_wheel_continuously(move_forward_speed)
        time.sleep(sleep)
        self.stop_moving()
        
    def emergency_stop(self):
        self.color_sensing_system.stop_detecting_color()
        self.gyro_sensor.stop_monitoring_orientation()
        self.stop_moving()
        self.color_sensing_system.stop_detecting_color()
        print("EMERGENCY STOP ACTIVATED")
        reset_brick()
        os._exit(1)
        