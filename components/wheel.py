from utils.brick import Motor

class Wheel:
    def __init__(self, port):
        self.motor = Motor(port)

    def rotate_wheel_degrees(self, degrees: int):
        self.motor.reset_encoder()
        self.motor.set_limits(power=10, dps=125)
        self.motor.set_position(degrees)

    def spin_wheel_continuously(self, power:int):
        self.motor.set_power(power)
    
    def spin_wheel_at_dps(self, dps: int):
        """Spin wheel at a specific speed in degrees per second (closed-loop control)"""
        self.motor.set_dps(dps)
        actual_speed = self.motor.get_speed()

    def stop_spinning(self):
        """Stop the wheel (works for both power and DPS control)"""
        self.motor.set_dps(0)  # Stop using DPS (cleaner than set_power for DPS-controlled motors)