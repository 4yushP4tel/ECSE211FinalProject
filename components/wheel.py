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

    def move_straight_dps(self, dps: int, direction: int = 1):
        """Move wheel at specified DPS with direction.
        
        Args:
            dps: Speed in degrees per second
            direction: 1 for forward, -1 for backward (default: 1)
        """
        self.spin_wheel_at_dps(dps * direction)

    def stop_spinning(self):
        """Stop the wheel (works for both power and DPS control)"""
        self.motor.set_dps(0)  # Stop using DPS (cleaner than set_power for DPS-controlled motors)