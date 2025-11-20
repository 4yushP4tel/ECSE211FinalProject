from utils.brick import Motor

class Wheel:
    def __init__(self, port):
        self.motor = Motor(port)

    def rotate_wheel_degrees(self, degrees:int):
        self.motor.reset_encoder()
        self.motor.set_limits(dps=90)
        self.motor.set_position(degrees)

    def spin_wheel_continuously(self, power:int):
        self.motor.set_power(power)

    def stop_spinning(self):
        self.motor.set_power(0)