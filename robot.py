import os
import time
from components.wheel import Wheel
from components.gyro_sensor import GyroSensor
from components.color_sensing_system import ColorSensingSystem
from components.speaker import Speaker
from components.drop_off_system import DropOffSystem
from utils.brick import TouchSensor, reset_brick, wait_ready_sensors
import threading

# Map of right turns in the delivery
RIGHT_TURNS = ["room",
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
    FORWARD_MOVEMENT_POWER_RIGHT = 15
    FORWARD_MOVEMENT_POWER_LEFT = FORWARD_MOVEMENT_POWER_RIGHT
    POWER_FOR_TURN = 15
    EXIT_ROOM_POWER = 10

    CHECK_READJUST_TIME_INTERVAL = 0.1

    def __init__(self):
        # Initialization of sensors and motors
        self.right_wheel = Wheel('B')
        self.left_wheel = Wheel('C')
        self.drop_off_system = DropOffSystem('A')
        self.speaker = Speaker()
        self.gyro_sensor = GyroSensor(4)
        self.color_sensing_system = ColorSensingSystem(3, 'D')
        self.emergency_touch_sensor = TouchSensor(1)
        self.counter_lock = threading.Lock()
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
        while True:
            print(self.right_turns_passed, RIGHT_TURNS[int(self.right_turns_passed)])
            if self.emergency_flag.is_set():
                self.emergency_stop()

            # if self.gyro_sensor.readjust_robot_flag.is_set():
            #    with self.gyro_sensor.orientation_lock:
            #        self.readjust_alignment()
            else:
                self.move_straight(1)

            # Turn right on valid intersections and then start moving again
            if self.color_sensing_system.detect_hallway_on_right_flag.is_set():
                self.color_sensing_system.detect_hallway_on_right_flag.clear()
                print("Detected path on right")
                time.sleep(0.5)
                self.stop_moving()
                
                with self.counter_lock:
                    turn_detected = RIGHT_TURNS[int(self.right_turns_passed)]
                    self.right_turns_passed += 0.5
                    print(f"<-----------------Turn detected: {turn_detected}----------------------->")

                # Right turn into home if all packages delivered
                if turn_detected == "home_valid" and self.packages_delivered == 2:
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.turn_x_deg(90)
                    self.gyro_sensor.check_if_moving_straight_on_path = True
                    self.head_home()
                    break

                # Skip right turn due to invalid home
                elif turn_detected == "home_invalid":
                    time.sleep(0.2)
                    continue

                # Right turn on corner
                elif turn_detected == "turn":
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.turn_x_deg(90)
                    self.gyro_sensor.check_if_moving_straight_on_path = True

                # Right turn into room if not all packages delivered
                elif turn_detected == "room" and self.packages_delivered != 2:
                    self.gyro_sensor.check_if_moving_straight_on_path = False
                    self.turn_x_deg(90)
                    self.validate_room_entrance()
                    self.gyro_sensor.check_if_moving_straight_on_path = True

    # TODO
    def readjust_alignment(self):
        # this would take info from the US sensor to check the distance from
        # the right wall and readjust if the distance is too large or small
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

            if current > 0:
                with self.wheel_lock:
                    self.left_wheel.spin_wheel_continuously(int(Robot.FORWARD_MOVEMENT_POWER_LEFT))
                    self.right_wheel.spin_wheel_continuously(
                        Robot.FORWARD_MOVEMENT_POWER_RIGHT + readjust_power_increase)
            else:
                with self.wheel_lock:
                    self.left_wheel.spin_wheel_continuously(
                        int(Robot.FORWARD_MOVEMENT_POWER_LEFT + readjust_power_increase))
                    self.right_wheel.spin_wheel_continuously(-Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            time.sleep(Robot.CHECK_READJUST_TIME_INTERVAL)
        if self.gyro_sensor.readjust_robot_flag.is_set():
            self.gyro_sensor.readjust_robot_flag.clear()
        print("Readjustment complete")

    def turn_x_deg(self, angle, power=POWER_FOR_TURN):
        print(f"Turn {angle} degrees (+ right, - left)")
        if angle > 0:
            self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT)
            self.right_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            while self.gyro_sensor.orientation < angle:
                if self.emergency_flag.is_set():
                    self.emergency_stop()
                time.sleep(0.01)
        elif angle < 0:
            self.left_wheel.motor.set_power(-Robot.FORWARD_MOVEMENT_POWER_LEFT)
            self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
            while self.gyro_sensor.orientation > angle:
                if self.emergency_flag.is_set():
                    self.emergency_stop()
                time.sleep(0.01)
        else:
            return

        self.stop_moving()
        self.gyro_sensor.reset_orientation()

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
        self.color_sensing_system.move_sensor_to_front()
        time.sleep(0.5)
        self.move_straight(1)
        time.sleep(1.5)
        self.stop_moving()
        if self.color_sensing_system.detect_invalid_entrance_flag.is_set():
            self.color_sensing_system.detect_invalid_entrance_flag.clear()
            print("detected invalid entrance")
            self.stop_moving()
            self.color_sensing_system.move_sensor_to_right_side()
            self.handle_meeting_room()
        else:
            self.color_sensing_system.detect_valid_entrance_flag.clear()
            print("detected valid entrance")
            self.color_sensing_system.move_sensor_to_right_side()
            self.handle_non_meeting_room()

    # Skip room
    def handle_meeting_room(self):
        self.move_straight(-1)
        time.sleep(1)
        self.stop_moving()
        self.turn_x_deg(270)
        self.color_sensing_system.move_sensor_to_right_side()

    # Process room and deliver package
    def handle_non_meeting_room(self):
        for i in range(7):  # check this out if this actually works
            if self.emergency_flag.is_set():
                self.emergency_stop()

            # Advance a little to cover the next area of the office
            self.move_straight(1)
            time.sleep(0.7)
            self.stop_moving()

            # Sweep across the width of the office
            self.color_sensing_system.motor.reset_encoder()
            self.color_sensing_system.motor.set_limits(dps=90)
            self.color_sensing_system.motor.set_position(-180)

            # Catch any green event if detected within 3 seconds of the sweep and get the angle of the sweeper
            angle = 0
            for _ in range(60):
                if self.emergency_flag.is_set():
                    self.emergency_stop()
                time.sleep(0.05)

                if self.color_sensing_system.detect_valid_sticker_flag.is_set() and not self.packages_dropped:
                    self.color_sensing_system.detect_valid_sticker_flag.clear()
                    print("STOPPING ARM")
                    self.color_sensing_system.motor.set_dps(0)
                    self.stop_moving()
                    print(f"ARM POSITION {self.color_sensing_system.motor.get_position()}")
                    angle = self.color_sensing_system.motor.get_position() + 90
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
                current_orientation = self.gyro_sensor.orientation
                self.turn_x_deg(angle)
                self.drop_off_package()
                self.turn_x_deg(-angle)

                # Exit sweeping loop
                break

        self.return_to_hallway_after_delivery()

    # Return home
    def head_home(self):
        # might need to add some code to be able to readjust if needed since the 
        # distance is very large
        self.color_sensing_system.move_sensor_to_front()

        while not self.color_sensing_system.detect_entered_home_flag.is_set():

            if self.gyro_sensor.readjust_robot_flag.is_set():
                with self.gyro_sensor.orientation_lock:
                    self.readjust_alignment()
            else:
                self.move_straight(1)
            time.sleep(0.05)
        # exits the loop as soon as the flag is set
        # let the robot move a little more forward into the room before stopping it
        time.sleep(2)
        self.stop_moving()
        self.color_sensing_system.detect_entered_home_flag.clear()
        self.speaker.play_mission_complete_tone()
        print("MISSION COMPLETE. ROBOT IS HOME.")
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
        self.color_sensing_system.move_sensor_to_right_side()
        self.move_straight(-1)
        while not self.color_sensing_system.detect_room_exit_flag.is_set():
            time.sleep(0.01)
        time.sleep(2)
        self.stop_moving()
        self.turn_x_deg(270)
        self.color_sensing_system.detect_room_exit_flag.clear()

