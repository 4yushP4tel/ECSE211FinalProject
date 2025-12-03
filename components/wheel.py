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
    
    def spin_wheel_at_dps(self, dps: int, power_limit: int = 50):
        """Spin wheel at a specific speed in degrees per second (closed-loop control)
        
        Args:
            dps: Target speed in degrees per second
            power_limit: Max power percentage to prevent brownouts (default: 50)
        """
        self.motor.set_limits(power=power_limit, dps=abs(dps))
        self.motor.set_dps(dps)

    def move_straight_dps(self, dps: int, direction: int = 1, power_limit: int = 50):
        """Move wheel at specified DPS with direction.
        
        Args:
            dps: Speed in degrees per second
            direction: 1 for forward, -1 for backward (default: 1)
            power_limit: Max power percentage to prevent brownouts (default: 50)
        """
        self.spin_wheel_at_dps(dps * direction, power_limit)

    def stop_spinning(self):
        """Stop the wheel (works for both power and DPS control)"""
        self.motor.set_dps(0)  # Stop using DPS (cleaner than set_power for DPS-controlled motors)