import os
import time
from components.wheel import Wheel
from components.gyro_sensor import GyroSensor, THRESHOLD_FOR_READJUST
from components.color_sensing_system import ColorSensingSystem
from components.speaker import Speaker
from components.drop_off_system import DropOffSystem
from utils.brick import TouchSensor, reset_brick, wait_ready_sensors
import threading

# Map of right turns in the delivery
RIGHT_TURNS_OLD = ["room",
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


RIGHT_TURNS = [
               "home_invalid",
               "turn", 
               "room", # room top left
               "home_valid",
               "turn",
               "room", # room top right
               "home_invalid",
               "turn",
               "room", # room bottom right
               "home_valid",
               "room", # room bottom left
               "turn",
               "home_invalid",
               "turn",
               "home_invalid",
               "home_valid"
               ]

class Robot:
    FORWARD_MOVEMENT_POWER_RIGHT = 22.8
    FORWARD_MOVEMENT_POWER_LEFT = 23
    POWER_FOR_TURN = 15
    EXIT_ROOM_POWER = 10

    CHECK_READJUST_TIME_INTERVAL = 0.1

    def __init__(self):
        # Initialization of sensors and motors
        reset_brick()
        self.right_wheel = Wheel('B')
        self.left_wheel = Wheel('C')
        self.drop_off_system = DropOffSystem('A')
        self.speaker = Speaker()
        self.gyro_sensor = GyroSensor(4)
        self.color_sensing_system = ColorSensingSystem(3, 'D')
        self.emergency_touch_sensor = TouchSensor(2)
        wait_ready_sensors()
        time.sleep(1)  # give some time to stabilize sensors

        # Emergency stop thread attributes
        self.emergency_thread = None
        self.emergency_flag = threading.Event()
        self.wheel_lock = threading.Lock()  # using this to ensure no conflicts with emergency stop and main thread

        # Start the thread
        self.start_emergency_monitoring()
        self.color_sensing_system.start_detecting_color()
        self.gyro_sensor.start_monitoring_orientation()

        # Additional attributes for robot logic
        self.packages_dropped = False
        self.right_turns_passed = 0
        self.packages_delivered = 0

    # Main method to activate the robot and start the delivery process
    def main(self):
        # Start the delivery
        self.start_delivery()
        self.stop_moving()

        # Stop the threads
        self.color_sensing_system.stop_detecting_color()
        self.gyro_sensor.stop_monitoring_orientation()
        self.stop_emergency_monitoring()

    # Main robot logic for the delivery, written for potential reusability for more complex mappings
    def start_delivery(self):
        # Soft-start to prevent initial twitching
        #print("Starting with soft-start to prevent twitching...")
        #normal_power_left = Robot.FORWARD_MOVEMENT_POWER_LEFT
        #normal_power_right = Robot.FORWARD_MOVEMENT_POWER_RIGHT
        
        # Set low initial power
        #Robot.FORWARD_MOVEMENT_POWER_LEFT = 12
        #Robot.FORWARD_MOVEMENT_POWER_RIGHT = 13
        #self.move_straight(1)
        
        # Wait for 3 seconds but check for realignment during soft-start
        #start_time = time.time()
        #while time.time() - start_time < 3:
        #    if self.emergency_flag.is_set():
        #        self.emergency_stop()
        #    
        #    # Check if robot needs realignment even during soft-start
        #    if self.gyro_sensor.readjust_robot_flag.is_set() and self.color_sensing_system.is_in_hallway:
        #        self.stop_moving()
        #        self.realign_to_zero()
        #        self.move_straight(1)  # Resume moving after realignment
            
        #    time.sleep(0.05)
        
        # Restore normal power
        #Robot.FORWARD_MOVEMENT_POWER_LEFT = normal_power_left
        #Robot.FORWARD_MOVEMENT_POWER_RIGHT = normal_power_right
        #print("Soft-start complete, resuming normal speed")
        while True:
            # print(self.right_turns_passed, RIGHT_TURNS[int(self.right_turns_passed)])
            if self.emergency_flag.is_set():
                self.emergency_stop()

            # Check if color sensor has failed - pause all actions until recovery
            if self.color_sensing_system.sensor_failed_flag.is_set():
                self.stop_moving()
                print("Robot paused: Waiting for color sensor to recover...")

                while self.color_sensing_system.sensor_failed_flag.is_set():
                    time.sleep(0.5)
                    if self.emergency_flag.is_set():
                        self.emergency_stop()
                print("Sensor recovered, resuming operations...")
                time.sleep(0.2)  # Give sensor a moment to stabilize

            # Check if robot needs realignment while in hallway
            if self.gyro_sensor.readjust_robot_flag.is_set() and self.color_sensing_system.is_in_hallway:
                self.realign_to_zero()
                self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT)
                self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
                self.move_straight(1)  # Resume forward movement after realignment in hallway
                continue # we dont want to run realignment logic followed by turn logic right
            else:
                self.move_straight(1)

            # Turn right on valid intersections and then start moving again
            if self.color_sensing_system.detect_hallway_on_right_flag.is_set():
                
                print("Detected path on right")
                print(RIGHT_TURNS[self.right_turns_passed])
                time.sleep(0.2)
                self.stop_moving()
                
                turn_detected = RIGHT_TURNS[int(self.right_turns_passed)]
                self.right_turns_passed +=1
                print(f"<-----------------Turn detected in main loop: {turn_detected}----------------------->")

                # Right turn into home if all packages delivered
                if turn_detected == "home_valid" and self.packages_delivered == 2:
                    print("HEADING HOME LLLLLLLLLLLLLLLLLLLLLLLLLLL")
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.color_sensing_system.is_in_hallway = False
                    self.color_sensing_system.is_handling_room = True
                    self.color_sensing_system.is_heading_home = True
                    self.turn_x_deg(90 - self.gyro_sensor.get_orientation())
                    
                    # Fine-tune alignment after turn
                    time.sleep(0.2)
                    current_orientation = self.gyro_sensor.orientation
                    if abs(current_orientation) > 1:
                        print(f"Fine-tuning orientation from {current_orientation} to 0")
                        self.turn_x_deg(-current_orientation)
                    
                    self.gyro_sensor.check_if_moving_straight_on_path = True
                    self.head_home()
                    break

                # Skip right turn due to invalid home
                elif turn_detected == "home_invalid":
                    # time.sleep(0.2)
                    print("Robot: Home invalid")
            

                # Right turn on corner
                elif turn_detected == "turn":
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.realign_to_zero()
                    self.turn_x_deg(90 - self.gyro_sensor.get_orientation())
                    self.gyro_sensor.check_if_moving_straight_on_path = True
                    
                    # Move forward to clear the intersection
                    self.move_straight(1)
                    time.sleep(0.1)
                    
                    self.stop_moving()

                # Right turn into room if not all packages delivered
                elif turn_detected == "room" and self.packages_delivered != 2:
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.color_sensing_system.is_in_hallway = False
                    self.color_sensing_system.is_handling_room = True
                    
                    # go straight to align to center of intersection
                    self.move_straight(1)
                    time.sleep(0.15)
                    self.stop_moving()
                    
                    # turn right with readjustment factor
                    self.turn_x_deg(90 - self.gyro_sensor.get_orientation())
                    
                    # process room
                    self.validate_room_entrance()
                    self.gyro_sensor.check_if_moving_straight_on_path = True
                    
                self.color_sensing_system.detect_hallway_on_right_flag.clear()

    def realign_to_zero(self):
        """
        Simple realignment method: rotate the robot back to 0 degrees orientation.
        This is called when the robot drifts while moving straight in the hallway.
        IMPORTANT: Turns to absolute 0° without resetting orientation.
        """
        print(f"Realigning robot from {self.gyro_sensor.orientation} degrees to 0")
        self.stop_moving()
        
        # Set cooldown timer FIRST to prevent re-trigger during the turn
        self.gyro_sensor.last_readjust_time = time.time()
        
        # Clear the flag
        if self.gyro_sensor.readjust_robot_flag.is_set():
            self.gyro_sensor.readjust_robot_flag.clear()
        
        # Turn directly to 0° (absolute) without resetting
        self.turn_to_orientation(0)
        
        print("Realignment complete")

    def turn_to_orientation(self, target_orientation, power=POWER_FOR_TURN):
        """
        Turn to an absolute orientation without resetting.
        Used for realignment to return to 0°.
        
        Args:
            target_orientation: Absolute orientation to turn to (usually 0)
            power: Motor power for turning
        """
        current = self.gyro_sensor.orientation
        print(f"Turning from {current}° to {target_orientation}°")
        
        threshold_reached = False
        if current < target_orientation:  # Need to turn right
            self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT)
            self.right_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            while self.gyro_sensor.orientation < target_orientation:
                if not threshold_reached and self.gyro_sensor.orientation > target_orientation - 20:
                    self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT * 0.4)
                    self.right_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_RIGHT * 0.4)
                    threshold_reached = True
                if self.emergency_flag.is_set():
                    self.emergency_stop()
                time.sleep(0.01)
        elif current > target_orientation:  # Need to turn left
            self.left_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_LEFT)
            self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            while self.gyro_sensor.orientation > target_orientation:
                if not threshold_reached and self.gyro_sensor.orientation < target_orientation + 20:
                    self.left_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_LEFT * 0.4)
                    self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT * 0.4)
                    threshold_reached = True
                if self.emergency_flag.is_set():
                    self.emergency_stop()
                time.sleep(0.01)
        
        self.stop_moving()
        print(f"Turn complete. Current orientation: {self.gyro_sensor.orientation}°")
    
    def turn_x_deg(self, angle, power=POWER_FOR_TURN, reset_after=True):
        """
        Turn the robot by a specified angle.
        
        Args:
            angle: Degrees to turn (+ right, - left) RELATIVE to current orientation
            power: Motor power for turning
            reset_after: If True, reset orientation to 0 after turn. If False, keep current reference frame.
        """
        print(f"Turn {angle} degrees (+ right, - left)")
        
        # Calculate target orientation: current + relative turn amount
        starting_orientation = self.gyro_sensor.orientation
        target_orientation = starting_orientation + angle
        print(f"Starting: {starting_orientation}°, Target: {target_orientation}°")
        
        threshold_reached = False
        if angle > 0:
            self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT)
            self.right_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            while self.gyro_sensor.orientation < target_orientation:
                if not threshold_reached and self.gyro_sensor.orientation > target_orientation - 20:
                    self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT * 0.47)
                    self.right_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_RIGHT * 0.47)
                    threshold_reached = True
                if self.emergency_flag.is_set():
                    self.emergency_stop()
                time.sleep(0.01)
        elif angle < 0:
            self.left_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_LEFT)
            self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            while self.gyro_sensor.orientation > target_orientation:
                if not threshold_reached and self.gyro_sensor.orientation < target_orientation + 20:
                    self.left_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_LEFT * 0.47)
                    self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT * 0.47)
                    threshold_reached = True
                if self.emergency_flag.is_set():
                    self.emergency_stop()
                time.sleep(0.01)
        else:
            return

        self.stop_moving()
        
        if reset_after:
            # Wait for gyro to stabilize at exactly the target angle before resetting
            print(f"Waiting for orientation to stabilize at {target_orientation} degrees...")
            stable_count = 0
            tolerance = 1  # degrees
            required_stable_readings = 3
            
            while stable_count < required_stable_readings:
                current = self.gyro_sensor.orientation
                if abs(current - target_orientation) <= tolerance:
                    stable_count += 1
                else:
                    stable_count = 0
                time.sleep(0.05)
                
                if self.emergency_flag.is_set():
                    self.emergency_stop()
            
            print(f"Orientation stabilized at {self.gyro_sensor.orientation} degrees, resetting...")
            self.gyro_sensor.reset_orientation()
        else:
            # For turns in rooms, don't reset - keep the same zero reference
            print(f"Turn complete. Current orientation: {self.gyro_sensor.orientation} degrees (no reset)")

    # Turn until current orientation of robot reaches desired orientation
    def turn_until_x_orientation(self, angle, power=POWER_FOR_TURN):
        print(f"Turn {angle - self.gyro_sensor.orientation} degrees (+ right, - left)")
        if angle > self.gyro_sensor.orientation:
            self.left_wheel.motor.set_power(power)
            self.right_wheel.motor.set_power(-power)
            while self.gyro_sensor.orientation < angle:
                pass
        elif angle < self.gyro_sensor.orientation:
            self.left_wheel.motor.set_power(-power)
            self.right_wheel.motor.set_power(power)
            while self.gyro_sensor.orientation > angle:
                pass
        else:
            return

        self.stop_moving()

    # Validate the entrance and proceed to process room or skip it
    def validate_room_entrance(self):
        #  move sensor over the red pad
        self.color_sensing_system.move_sensor_to_front(POSITION=-93)
        self.move_straight(1)
        
        print("CHECKING FOR RED PAD")
        time.sleep(0.6)
        self.stop_moving()
        self.realign_to_zero()
        
        
        # time.sleep(0.5)
        
        # Move forward while checking for realignment
        # start_time = time.time()
        # while time.time() - start_time < 0.5: # For the next 0.65 seconds
         #   if self.emergency_flag.is_set():
          #      self.emergency_stop()
           # 
            #if self.gyro_sensor.readjust_robot_flag.is_set():
             #   self.stop_moving()
              #  self.realign_to_zero()
               # self.move_straight(1)
                # Don't resume moving - we're entering a room, not in hallway
            
            #time.sleep(0.05)
        
        #self.stop_moving()
        
        
        print("CHECKING DETECT_INVALID_ENTRANCE_FLAG")
        if self.color_sensing_system.detect_invalid_entrance_flag.is_set():
            self.color_sensing_system.detect_invalid_entrance_flag.clear()
            print("detected invalid entrance")
            self.stop_moving()
            self.handle_meeting_room()
        else:
            print("detected valid entrance")
            self.color_sensing_system.move_sensor_to_right_side()
            self.move_straight(1)
            time.sleep(0.5)
            self.stop_moving()
            self.realign_to_zero()
            
            #start_time = time.time()
            #while time.time() - start_time < 0.65: # For the next 0.65 seconds
            #    if self.emergency_flag.is_set():
            #        self.emergency_stop()
            #    
            #    if self.gyro_sensor.readjust_robot_flag.is_set():
           #         self.stop_moving()
            #        self.realign_to_zero()
            
            # time.sleep(0.4)
            #self.stop_moving()
            self.handle_non_meeting_room()

    # Skip room
    def handle_meeting_room(self):
        # Color sensor is already at front from validate_room_entrance
        self.move_straight(-1)
        
        # Count consecutive orange detections to exit room
        orange_count = 0
        while orange_count < 2:
            if self.emergency_flag.is_set():
                self.emergency_stop()
            
            if self.gyro_sensor.readjust_robot_flag.is_set():
                self.stop_moving()
                self.realign_to_zero()
                self.move_straight(-1)  # Resume moving backward after realignment
            
            # Check current color
            with self.color_sensing_system.color_lock:
                current_color = self.color_sensing_system.most_recent_color
            
            if current_color == "orange":
                orange_count += 1
                print(f"Orange detected ({orange_count}/2)")
                time.sleep(0.1)  # Small delay to avoid counting same detection multiple times
            else:
                orange_count = 0  # Reset if non-orange detected
            
            time.sleep(0.05)
        
        self.move_straight(1)
        time.sleep(0.3)
        self.stop_moving()
        print("Exited meeting room - detected orange twice")
        
        self.turn_x_deg(270 - self.gyro_sensor.get_orientation())
        
        # Fine-tune alignment after turn to ensure parallel to wall
        time.sleep(0.2)
        current_orientation = self.gyro_sensor.orientation
        if abs(current_orientation) > 1:
            print(f"Fine-tuning orientation from {current_orientation} to 0")
            self.turn_x_deg(-current_orientation)
        
        self.color_sensing_system.move_sensor_to_right_side()
        
        # Reset state flags back to hallway mode
        self.color_sensing_system.is_handling_room = False
        self.color_sensing_system.is_in_hallway = True
        
        # Move forward to clear the intersection and prevent re-detection
        self.move_straight(1)
        
        start_time = time.time()
        while time.time() - start_time < 0.5:
            if self.emergency_flag.is_set():
                self.emergency_stop()
            
            if self.gyro_sensor.readjust_robot_flag.is_set():
                self.stop_moving()
                self.realign_to_zero()
                self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT)
                self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
                self.move_straight(1)  # Resume moving forward after realignment
            
            time.sleep(0.05)
        
        self.stop_moving()

    # Process room and deliver package
    def handle_non_meeting_room(self):
        self.color_sensing_system.detect_valid_sticker_flag.clear()
        for i in range(6):  # check this out if this actually works
            if self.emergency_flag.is_set():
                self.emergency_stop()

            # Sweep across the width of the office
            self.color_sensing_system.motor.reset_encoder()
            self.color_sensing_system.motor.set_limits(dps=150)
            self.color_sensing_system.motor.set_position(-180)

            # Catch any green event if detected within 3 seconds of the sweep and get the angle of the sweeper
            angle = 0
            for _ in range(60):
                if self.emergency_flag.is_set():
                    self.emergency_stop()
                time.sleep(0.02)

                if self.color_sensing_system.detect_valid_sticker_flag.is_set() and not self.packages_dropped:
                    print("STOPPING ARM")
                    self.color_sensing_system.motor.set_dps(0)
                    self.stop_moving()
                    print(f"ARM POSITION {self.color_sensing_system.motor.get_position()}")
                    angle = self.color_sensing_system.motor.get_position() + 90
                    print(f"ANGLE: {angle}")

                    self.packages_dropped = True
            self.color_sensing_system.motor.wait_is_stopped()

            # Return sweeper back to default position
            self.color_sensing_system.motor.set_limits(dps=120)
            self.color_sensing_system.motor.set_position(5)
            self.color_sensing_system.motor.wait_is_stopped()
            time.sleep(1.4)
            
            
            # Advance a little to cover the next area of the office
            # Drop package on green sticker if detected
            if self.packages_dropped:
                current_orientation = self.gyro_sensor.orientation
                new_angle = angle - self.gyro_sensor.get_orientation()
                print(f"Turning to package: current={self.gyro_sensor.orientation}°, turning {new_angle}°")
                
                # Turn to package WITHOUT resetting (keep reference frame)
                self.turn_x_deg(new_angle, reset_after=False)
                self.drop_off_package()
                
                # Turn back to original orientation WITHOUT resetting
                self.turn_x_deg(-new_angle, reset_after=False)
                print(f"Returned to orientation: {self.gyro_sensor.orientation}°")
                
                self.packages_dropped = False
                # Exit sweeping loop
                self.color_sensing_system.detect_valid_sticker_flag.clear()
                break
            self.move_straight(1)
            time.sleep(0.5)
            self.stop_moving()
            self.realign_to_zero()
            
            # Move forward while checking for realignment
            #start_time = time.time()
            
            #while time.time() - start_time < 0.5:
            #    if self.emergency_flag.is_set():
            #        self.emergency_stop()
                
            #    if self.gyro_sensor.readjust_robot_flag.is_set():
                    
             #       self.stop_moving()
             #       
             #       self.realign_to_zero()
             #       self.move_straight(1)
                    # Don't resume moving - we're in a room, not hallway
                
             #   time.sleep(0.05)
            
           # self.stop_moving()
            
            
        self.color_sensing_system.detect_valid_sticker_flag.clear()
        self.return_to_hallway_after_delivery()

    # Return home
    def head_home(self):
        # might need to add some code to be able to readjust if needed since the 
        # distance is very large
        self.color_sensing_system.move_sensor_to_front()
        self.color_sensing_system.detect_entered_home_flag.clear()

        while not self.color_sensing_system.detect_entered_home_flag.is_set():
            if self.emergency_flag.is_set():
                self.emergency_stop()

            if self.gyro_sensor.readjust_robot_flag.is_set():
                self.stop_moving()
                self.realign_to_zero()
                self.move_straight(1)
            else:
                self.move_straight(1)
            time.sleep(0.05)
        # exits the loop as soon as the flag is set
        # let the robot move a little more forward into the room before stopping it
        time.sleep(3.5)
        self.stop_moving()
        self.color_sensing_system.detect_entered_home_flag.clear()
        self.speaker.play_mission_complete_tone()
        print("MISSION COMPLETE. ROBOT IS HOME.")
        time.sleep(3)
        self.emergency_stop()

    # Methods handling emergency stop and its thread
    def start_emergency_monitoring(self):
        # a dedicated thread to monitor the emergency button
        self.emergency_thread = threading.Thread(target=self.monitor_emergency_button, daemon=True)
        self.emergency_thread.start()
        print("Emergency monitoring thread started")

    def stop_emergency_monitoring(self):
        self.emergency_flag.set()
        print("Emergency monitoring thread stopped")

    def monitor_emergency_button(self):
        # this runs in its own thread, all other functions should just return if
        # the button has been pressed
        while not self.emergency_flag.is_set():
            if self.emergency_touch_sensor.is_pressed():
                self.emergency_flag.set()
                print("EMERGENCY BUTTON PRESSED!")
                self.emergency_stop()
                self.emergency_flag.clear()
                break
            time.sleep(0.05)

    def emergency_stop(self):
        self.stop_moving()
        self.color_sensing_system.stop_detecting_color()
        self.gyro_sensor.stop_monitoring_orientation()
        print("EMERGENCY STOP ACTIVATED")
        reset_brick()
        os._exit(1)

    # Helper methods
    def move_straight(self, direction):
        with self.wheel_lock:
            self.left_wheel.spin_wheel_continuously(direction * Robot.FORWARD_MOVEMENT_POWER_LEFT)
            self.right_wheel.spin_wheel_continuously(direction * Robot.FORWARD_MOVEMENT_POWER_RIGHT)

    def move_straight_time(self, direction, time):
        time_interval = 0.1
        # we check at every time internval for readjustment
        for i in range(int(time / time_interval)):
            self.move_straight(direction)
            
            time.sleep(time_interval)
            if self.emergency_flag.is_set():
                self.emergency_stop()
                
            if self.gyro_sensor.readjust_robot_flag.is_set():
                    
                self.stop_moving()
                    
                self.realign_to_zero()
            
        
        

    def stop_moving(self):
        with self.wheel_lock:
            self.left_wheel.stop_spinning()
            self.right_wheel.stop_spinning()

    def drop_off_package(self):
        self.stop_moving()
        self.drop_off_system.deliver_package(self.packages_delivered)
        self.speaker.play_delivery_tone()
        print("PACKAGE DROPPED")
        self.packages_delivered += 1

    def return_to_hallway_after_delivery(self):
        # Move color sensor to front to detect orange tape
        self.color_sensing_system.move_sensor_to_front()
        print("TRYING TO MOVE BACKWARDS ||||||||||||||||||||||||||||||||||||||||||||")
        self.move_straight(-1)
        
        # Count consecutive orange detections
        orange_count = 0
        while orange_count < 2:
            if self.emergency_flag.is_set():
                self.emergency_stop()
            
            if self.gyro_sensor.readjust_robot_flag.is_set():
                self.stop_moving()
                self.realign_to_zero()
                self.move_straight(-1)  # Resume moving backward after realignment
            
            # Check current color
            with self.color_sensing_system.color_lock:
                current_color = self.color_sensing_system.most_recent_color
            
            if current_color == "orange":
                orange_count += 1
                print(f"Orange detected ({orange_count}/2)")
                time.sleep(0.1)  # Small delay to avoid counting same detection multiple times
            else:
                orange_count = 0  # Reset if non-orange detected
        
        self.stop_moving()
        # Needs to move straight a bit to stay aligned on right side of black line
        self.move_straight(1)
        time.sleep(0.4)
        self.stop_moving()
        # time.sleep(0.1)
        print("Exited room - detected orange twice")
        
        # Turn back to hallway
        self.turn_x_deg(270 - self.gyro_sensor.get_orientation())
        
        # Fine-tune alignment after turn to ensure parallel to wall
        time.sleep(0.2)
        current_orientation = self.gyro_sensor.orientation
        if abs(current_orientation) > 1:
            print(f"Fine-tuning orientation from {current_orientation} to 0")
            self.turn_x_deg(-current_orientation)
        
        self.color_sensing_system.move_sensor_to_right_side()
        
        # Reset state flags back to hallway mode
        self.color_sensing_system.is_handling_room = False
        self.color_sensing_system.is_in_hallway = True
        
        # Move forward to clear the intersection and prevent re-detection
        self.move_straight(1)
        
        start_time = time.time()
        while time.time() - start_time < 0.5:
            if self.emergency_flag.is_set():
                self.emergency_stop()
            
            if self.gyro_sensor.readjust_robot_flag.is_set():
                self.stop_moving()
                self.realign_to_zero()
                self.move_straight(1)  # Resume moving forward after realignment
            
            time.sleep(0.05)
        
        self.stop_moving()

