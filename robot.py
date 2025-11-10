import re
import time
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

    def turn_right(self, deg:int):
        self.stop_moving()
        t1=threading.Thread(target=self.left_wheel.rotate_wheel_degrees, args=(deg))
        t2=threading.Thread(target=self.right_wheel.rotate_wheel_degrees, args=(-deg))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    def turn_left(self, deg:int):
        self.stop_moving()
        t1=threading.Thread(target=self.left_wheel.rotate_wheel_degrees, args=(-deg))
        t2=threading.Thread(target=self.right_wheel.rotate_wheel_degrees, args=(deg))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    def readjust_alignment(self, direction: str):
        # this would take info from the US sensor to check the distnace from
        #the right wall and readjust if the distance is too large or small
        readjustment_angle_of_rotation = 3
        if direction == "ok":
            return
        elif direction == "l":
            self.turn_left(readjustment_angle_of_rotation)
        elif direction == "r":
            self.turn_right(readjustment_angle_of_rotation)
        return

    def move_forward(self, power:int):
        self.left_wheel.spin_wheel_continuously(power)
        self.right_wheel.spin_wheel_continuously(power)
    
    def stop_moving(self):
        t1 = threading.Thread(target=self.left_wheel.stop_spinning)
        t2 = threading.Thread(target=self.right_wheel.stop_spinning)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        time.sleep(0.5)

    def move_towards_room(self):
        self.color_sensing_system.move_sensor_to_front()
        self.move_forward(30) # want to move slowly to not miss possible red square

    def check_could_enter_room(self) -> bool:
        if (self.color_sensing_system.is_in_front):
            if self.color_sensing_system.detect_color() == "Red":
                return False
            else:
                return True
            


    def go_back_to_hallway(self):
        pass

    def enter_room(self):
        pass
    
    def sweep_room(self):
        pass

    def drop_off_package(self):
        self.drop_off_system.deliver_package()
        self.speaker.play_delivery_tone()

    def go_home(self):
        pass

    def emergency_stop(self):
        pass

if __name__ == "__main__":
    pass