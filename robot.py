import re
import time
from turtle import color
from wheel import Wheel
from us_sensor import UltrasonicSensor
from color_sensing_system import ColorSensingSystem
from speaker import Speaker
from drop_off_system import DropOffSystem
from utils.brick import TouchSensor
import threading


class Robot:
    def __init__(self):
        self.right_wheel = Wheel('B')
        self.left_wheel = Wheel('C')
        self.drop_off_system = DropOffSystem('A')
        self.speaker = Speaker()
        self.us_sensor = UltrasonicSensor()
        self.color_sensing_system = ColorSensingSystem()
        self.emergency_touch_sensor = TouchSensor(1)
        self.move_thread = None
        self.stop_flag = threading.Event()

    def turn_right(self, deg:int):
        self.stop_moving()
        t1=threading.Thread(target=self.left_wheel.rotate_wheel_degrees, args=(deg))
        t2=threading.Thread(target=self.right_wheel.rotate_wheel_degrees, args=(-deg))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        self.us_sensor.wall_pointed_to = "long"

    def turn_left(self, deg:int):
        self.stop_moving()
        t1=threading.Thread(target=self.left_wheel.rotate_wheel_degrees, args=(-deg))
        t2=threading.Thread(target=self.right_wheel.rotate_wheel_degrees, args=(deg))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
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

    def move_forward(self, power:int):
        self.stop_moving()
        self.stop_flag.clear()
        def move_loop():
            self.left_wheel.spin_wheel_continuously(power)
            self.right_wheel.spin_wheel_continuously(power)

            while not self.stop_flag.is_set():
                with self.us_sensor.lock:
                    direction = self.us_sensor.latest_direction

                if direction and direction != "ok":
                    self.readjust_alignment(direction)
                    
                time.sleep(0.3)
            
            self.left_wheel.stop_spinning()
            self.right_wheel.stop_spinning()
                
        self.move_thread = threading.Thread(target=move_loop, daemon=True)
        self.move_thread.start()
    
    def stop_moving(self):
        self.stop_flag.set()
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
            self.move_forward(20)
            if color == "Orange":
                self.stop_moving()
                return True
        return False
            
    def go_back_to_hallway(self):
        pass

    def enter_room(self):
        pass
    
    def sweep_room(self):
        pass

    def drop_off_package(self):
        self.stop_moving()
        self.drop_off_system.deliver_package()
        self.speaker.play_delivery_tone()

    def go_home(self):
        pass

    def emergency_stop(self):
        pass