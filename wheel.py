from utils.brick import Motor

class Wheel:
    def _init_(self, port):
        self.motor = Motor(port)

    def rotate_wheel_degrees(self, degrees:int, power:int):
        self.motor.reset_encoder()
        self.motor.set_position(degrees)
        self.motor.wait_is_stopped()

    def spin_wheel_continuously(self, power:int):
        self.motor.set_power(power)

    def stop_spinning(self):
        self.motor.set_power(0)