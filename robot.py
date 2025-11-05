from wheel import Wheel
from us_sensor import UltrasonicSensor
from color_sensing_system import ColorSensingSystem
from speaker import Speaker
from drop_off_system import DropOffSystem
from utils.brick import TouchSensor


class Robot:
    def __init__(self):
        self.right_wheel = Wheel('B')
        self.left_wheel = Wheel('C')
        self.drop_off_system = DropOffSystem('A')
        self.speaker = Speaker()
        self.us_sensor = UltrasonicSensor()
        self.color_sensor = ColorSensingSystem()
        self.emergency_touch_sensor = TouchSensor(1)

    def turn_right(self):
        pass

    def turn_left(self):
        pass

    def move_forward(self):
        pass

    def move_to_room(self):
        pass

    def check_could_enter_room(self):
        pass

    def go_back_to_hallway(self):
        pass

    def enter_room(self):
        pass
    
    def sweep_room(self):
        pass

    def drop_off_package(self):
        pass

    def stop(self):
        pass

    def go_home(self):
        pass

    def emergency_stop(self):
        pass

if __name__ == "__main__":
    pass