import sys
import time
from components.wheel import Wheel
from components.us_sensor import UltrasonicSensor
from components.color_sensing_system import ColorSensingSystem
from components.speaker import Speaker
from components.drop_off_system import DropOffSystem
from utils.brick import TouchSensor
import threading

# this will store what each right turn which we detect means
RIGHT_TURNS = ["turn",
                "room",
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
    def __init__(self):
        self.right_turns_passed = 0
        self.packages_delivered = 0
        self.right_wheel = Wheel('B')
        self.left_wheel = Wheel('C')
        self.drop_off_system = DropOffSystem('A')
        self.speaker = Speaker()
        self.us_sensor = UltrasonicSensor()
        self.color_sensing_system = ColorSensingSystem()
        self.emergency_touch_sensor = TouchSensor(1)
        self.move_thread = None
        self.stop_flag = threading.Event()
        self.go_home_flag = threading.Event()

    def turn_right(self, power:int):
        self.stop_moving()
        print("Turning right")
        while self.color_sensing_system.most_recent_color != "Black" and self.color_sensing_system.prev_color == "White":
            self.left_wheel.spin_wheel_continuously(power)
            self.right_wheel.spin_wheel_continuously(-power)
        self.us_sensor.wall_pointed_to = "long"

    def turn_left(self, power:int):
        self.stop_moving()
        print("Turning left")
        self.left_wheel.spin_wheel_continuously(-power)
        self.right_wheel.spin_wheel_continuously(power)
        self.us_sensor.wall_pointed_to = "short"

    def readjust_alignment(self, direction: str):
        # this would take info from the US sensor to check the distnace from
        #the right wall and readjust if the distance is too large or small
        readjustment_angle_of_rotation = 3
        if direction == "ok":
            return
        elif direction == "l":
            self.turn_left(readjustment_angle_of_rotation)
            time.sleep(0.5)
        elif direction == "r":
            self.turn_right(readjustment_angle_of_rotation)
            time.sleep(0.5)
        return

    def move(self, power:int):
        self.stop_moving()
        if self.stop_flag.is_set():
            self.stop_flag.clear()
        self.color_sensing_system.start_detecting_color()
        def move_loop():
            self.us_sensor.start_monitoring_distance()
            self.left_wheel.spin_wheel_continuously(power)
            self.right_wheel.spin_wheel_continuously(power)

            while not self.stop_flag.is_set():
                if self.emergency_touch_sensor.is_pressed():
                    self.emergency_stop()

                with self.us_sensor.lock:
                    direction = self.us_sensor.latest_direction
                
                if self.color_sensing_system.detect_hallway_on_right_flag.is_set():
                    print("Detected hallway on right")
                    self.stop_flag.set()
                    self.color_sensing_system.detect_hallway_on_right_flag.clear()
                    
                    self.left_wheel.stop_spinning()
                    self.right_wheel.stop_spinning()
                    if(RIGHT_TURNS[self.right_turns_passed]!="home_invalid"):
                        self.turn_right(20)
                    self.right_turns_passed += 1
                    self.stop_flag.clear()
                    self.left_wheel.spin_wheel_continuously(power/5)
                    self.right_wheel.spin_wheel_continuously(power/5)

                if direction and direction != "ok":
                    self.readjust_alignment(direction)
                    
                time.sleep(0.3)
            
            self.left_wheel.stop_spinning()
            self.right_wheel.stop_spinning()
                
        self.move_thread = threading.Thread(target=move_loop, daemon=True)
        self.move_thread.start()
    
    def stop_moving(self):
        if not self.stop_flag.is_set():
            self.stop_flag.set()
        self.us_sensor.stop_monitoring_distance()
        if self.move_thread and self.move_thread.is_alive():
            self.move_thread.join()
        time.sleep(0.2)

    def check_could_enter_room(self) -> bool:
        self.turn_right(10)
        time.sleep(0.5)
        self.color_sensing_system.move_sensor_to_front()
        time.sleep(0.5)
        color = self.color_sensing_system.detect_color()
        while color != "Red":
            self.move(20)
            if color == "Orange":
                self.stop_moving()
                return True
        return False
            
    def go_back_to_hallway(self, power:int):
        """
        the power is the power at which you should move backwards
        """
        self.stop_moving()
        while self.color_sensing_system.most_recent_color != "Black":
            # basically moving backwards
            self.move(-power)
        time.sleep(0.5)
        self.turn_left(10)
        time.sleep(0.5)
        self.stop_moving()

    def enter_room(self):
        pass
    
    def sweep_room(self):
        pass

    def drop_off_package(self):
        self.stop_moving()
        self.drop_off_system.deliver_package()
        self.speaker.play_delivery_tone()
        self.packages_delivered += 1
        if self.packages_delivered == 2:
            self.go_home_flag.set()

    def go_home(self):
        pass

    def emergency_stop(self):
        self.left_wheel.stop_spinning()
        self.right_wheel.stop_spinning()
        self.color_sensing_system.stop_detecting_color()
        sys.exit(1)