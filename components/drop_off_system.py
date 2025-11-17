from utils.brick import Motor

class DropOffSystem:
    def __init__(self, motor_port):
        self.motor = Motor(motor_port)

    def deliver_package(self, packages_delivered):
        """
        This sytem will move the small motor in a full circle
        to drop push the lowest package off the stack and allow the next one to
        fall in place to then be delivered after.
        """
        self.motor.reset_encoder() # sets the curr position to 0
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
