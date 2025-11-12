from utils.brick import Motor

class DropOffSystem:
    def __init__(self, motor_port):
        self.motor = Motor(motor_port)

    def deliver_package(self):
        """
        This sytem will move the small motor in a full circle
        to drop push the lowest package off the stack and allow the next one to
        fall in place to then be delivered after.
        """
        self.motor.reset_encoder() # sets the curr position to 0
        self.motor.set_dps(100)
        self.motor.set_position(359)
        self.motor.wait_is_stopped()