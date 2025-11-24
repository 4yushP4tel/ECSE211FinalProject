import os
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
    FORWARD_MOVEMENT_POWER=12
    POWER_FOR_TURN=15
    EXIT_ROOM_POWER=10
    READJUST_POWER=15
    CHECK_READJUST_TIME_INTERVAL = 0.1
    def __init__(self):
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
                print("EMERGENCY BUTTON PRESSED!")
                self.emergency_flag.set()
                self.emergency_stop()
                break
            time.sleep(0.05)

    def turn_right_90(self, power=POWER_FOR_TURN):
        print("Turning right")
        while True:
            with self.gyro_sensor.orientation_lock:
                current_orientation = self.gyro_sensor.orientation
            #print(f"Current orientation: {current_orientation}")
            if current_orientation > 88:
                break
            with self.wheel_lock:
                self.left_wheel.spin_wheel_continuously(power)
                self.right_wheel.spin_wheel_continuously(-power)
        self.stop_moving()
        self.gyro_sensor.reset_orientation()

    def turn_left_90(self, power=POWER_FOR_TURN):
        print("Turning left")
        while True:
            with self.gyro_sensor.orientation_lock:
                current_orientation = self.gyro_sensor.orientation
            
            if current_orientation < -88:
                break
            with self.wheel_lock:
                self.left_wheel.spin_wheel_continuously(-power)
                self.right_wheel.spin_wheel_continuously(power)
        self.stop_moving()
        self.gyro_sensor.reset_orientation()

    def readjust_alignment(self):
        # this would take info from the US sensor to check the distance from
        #the right wall and readjust if the distance is too large or small
        print("Readjusting")
        self.stop_moving()
        while True:
            with self.gyro_sensor.orientation_lock:
                current = self.gyro_sensor.orientation
            
            if abs(current) <= 1:
                print("Alignment OK")
                self.stop_moving()
                break

            if current>0:
                with self.wheel_lock:
                    self.left_wheel.spin_wheel_continuously(-Robot.READJUST_POWER)
                    self.right_wheel.spin_wheel_continuously(Robot.READJUST_POWER)
            else:
                with self.wheel_lock:
                    self.left_wheel.spin_wheel_continuously(Robot.READJUST_POWER)
                    self.right_wheel.spin_wheel_continuously(-Robot.READJUST_POWER)
            time.sleep(Robot.CHECK_READJUST_TIME_INTERVAL)
        if self.gyro_sensor.readjust_robot_flag.is_set():
            self.gyro_sensor.readjust_robot_flag.clear()
        print("Readjustment complete")

    def move_in_hallway(self, power:int=FORWARD_MOVEMENT_POWER):
        while True:
            if self.emergency_flag.is_set():
                return
            
            #if self.gyro_sensor.readjust_robot_flag.is_set():
            #    with self.gyro_sensor.orientation_lock:
            #        self.readjust_alignment()
            else:
                with self.wheel_lock:
                    self.left_wheel.spin_wheel_continuously(1.25*power)
                    self.right_wheel.spin_wheel_continuously(power)

            # Turn right on valid intersections and then start moving again
            if self.color_sensing_system.detect_hallway_on_right_flag.is_set():
                print("Detected path on right")
                time.sleep(0.3)
                self.stop_moving()

                if self.right_turns_passed >= len(RIGHT_TURNS):
                    print("No more RIGHT_TURNS entries — ignoring right path")
                    self.color_sensing_system.detect_hallway_on_right_flag.clear()
                    continue

                turn_detected = RIGHT_TURNS[self.right_turns_passed]

                if turn_detected == "home_valid" and self.go_home:
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.turn_right_90()
                    self.gyro_sensor.reset_orientation()
                    self.gyro_sensor.check_if_moving_straight_on_path = True
                    self.right_turns_passed += 1
                    self.color_sensing_system.detect_hallway_on_right_flag.clear()
                    self.head_home_after_turn()
                    break

                elif turn_detected == "home_invalid":
                    self.right_turns_passed += 1

                elif turn_detected == "turn":
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.turn_right_90()
                    self.gyro_sensor.reset_orientation()
                    self.gyro_sensor.check_if_moving_straight_on_path = True
                    self.gyro_sensor.reset_orientation()
                    self.right_turns_passed += 1
                    
                elif turn_detected == "room" and not self.go_home:
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.turn_right_90()
                    self.right_turns_passed += 1
                    self.detected_room_action()
                    self.gyro_sensor.reset_orientation()
                    self.gyro_sensor.check_if_moving_straight_on_path = True
                
                if self.color_sensing_system.detect_hallway_on_right_flag.is_set():
                    self.color_sensing_system.detect_hallway_on_right_flag.clear()
                
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
        if self.color_sensing_system.detect_valid_entrance_flag.is_set():
            print("detected valid entrance")
            self.handle_non_meeting_room()
            self.color_sensing_system.detect_valid_entrance_flag.clear()
        elif self.color_sensing_system.detect_invalid_entrance_flag.is_set():
            print("detected invalid entrance")
            self.handle_meeting_room()
            self.color_sensing_system.detect_invalid_entrance_flag.clear()
        self.color_sensing_system.move_sensor_to_right_side()
    
    def handle_non_meeting_room(self):
        position_of_green_sticker = self.sweep_room_for_green_sticker()
        if position_of_green_sticker != float("inf"):
            self.rotate_for_delivery(90-position_of_green_sticker)
            if self.color_sensing_system.is_in_front or self.color_sensing_system.motor.get_position()==self.color_sensing_system.FRONT_POSITION:
                self.color_sensing_system.move_sensor_to_right_side()
            self.drop_off_package()
            self.rotate_for_delivery(0) # 90 deg for the arm represents 0 for the robot
        self.return_in_hallway_after_delivery()

    def sweep_room_for_green_sticker(self)->int:
            #returns the angle at which the color sensor detects the green sticker
        for _ in range(10):
            self.stop_moving()
            if self.color_sensing_system.detect_room_end.is_set():
                return float("inf")
            if self.color_sensing_system.detect_valid_sticker_flag.is_set():
                self.color_sensing_system.motor.set_power(0)
                print("detected the green sticker")
                self.color_sensing_system.detect_valid_sticker_flag.clear()
                return self.color_sensing_system.motor.get_position()
            self.color_sensing_system.move_sensor_side_to_side()
            self.move_slightly_forward_for_sweep()
            time.sleep(0.5)
        print("could not find the green sticker")
        return float("inf")
    
    def rotate_for_delivery(self, target_angle_of_gyro: int):
        print("Rotating the robot for delivery")

        if target_angle_of_gyro > 0: #right
            left_power = Robot.POWER_FOR_TURN
            right_power = -Robot.POWER_FOR_TURN
            done = lambda cur: cur>=target_angle_of_gyro
            
        else: #left
            left_power = -Robot.POWER_FOR_TURN
            right_power = Robot.POWER_FOR_TURN
            done = lambda cur: cur<=target_angle_of_gyro
        
        while True:
            with self.gyro_sensor.orientation_lock:
                current = self.gyro_sensor.orientation
            
            if done(current):
                break
                
            with self.wheel_lock:
                self.left_wheel.spin_wheel_continuously(left_power)
                self.right_wheel.spin_wheel_continuously(right_power)
            
        self.stop_moving()
        
    def return_in_hallway_after_delivery(self):
        self.color_sensing_system.move_sensor_to_right_side()
        with self.wheel_lock:
            self.left_wheel.spin_wheel_continuously(-Robot.EXIT_ROOM_POWER)
            self.right_wheel.spin_wheel_continuously(-Robot.EXIT_ROOM_POWER)
        while not self.color_sensing_system.detect_room_exit_flag.is_set():
            time.sleep(0.05)
        time.sleep(2)
        self.stop_moving()
        self.turn_right_90()
        self.turn_right_90()
        self.turn_right_90()
        self.color_sensing_system.detect_room_exit_flag.clear()

    def handle_meeting_room(self):
        self.turn_left_90()
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
                    self.left_wheel.spin_wheel_continuously(1.2*Robot.FORWARD_MOVEMENT_POWER)
                    self.right_wheel.spin_wheel_continuously(Robot.FORWARD_MOVEMENT_POWER)
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

    def move_slightly_forward_for_sweep(self, wheel_rotation=100):
        self.left_wheel.rotate_wheel_degrees(wheel_rotation)
        self.right_wheel.rotate_wheel_degrees(wheel_rotation)
        
    def emergency_stop(self):
        with self.wheel_lock:
            self.stop_moving()
        self.color_sensing_system.stop_detecting_color()
        print("EMERGENCY STOP ACTIVATED")
        reset_brick()
        os._exit(1)