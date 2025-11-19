from utils.brick import Motor
import time

class DropOffSystem:
    def __init__(self, motor_port):
        self.motor = Motor(motor_port)
        

    def deliver_package(self, packages_delivered: int):
        """
        This sytem will move the small motor in a full circle
        to drop push the lowest package off the stack and allow the next one to
        fall in place to then be delivered after.
        """
        self.motor.set_limits(dps=90)
        self.motor.reset_encoder() # sets the curr position to 0
        self.motor.get_position()
        if packages_delivered == 0:
            self.motor.set_position(89)
            self.motor.wait_is_stopped()
            self.motor.set_position(0)
            self.motor.wait_is_stopped()
        else:
            self.motor.set_position(179)
            self.motor.wait_is_stopped()
            self.motor.set_position(0)
            self.motor.wait_is_stopped()
