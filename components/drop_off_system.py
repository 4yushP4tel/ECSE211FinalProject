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
        #self.motor.set_limits(dps=90)
        self.motor.reset_encoder() # sets the curr position to 0
        print(self.motor.get_position())
        print(f"packages delivered: {packages_delivered}")
        if packages_delivered == 0:
            self.motor.set_power(8)
            time.sleep(1)
            print(self.motor.get_position())
            self.motor.set_power(0)
            time.sleep(0.25)
            self.motor.set_power(-8)
            time.sleep(1)
            self.motor.set_power(0)
        else:
            self.motor.set_power(12)
            time.sleep(1.5)
            print(self.motor.get_position())
            self.motor.set_power(0)
            time.sleep(0.25)
            self.motor.set_power(-12)
            time.sleep(1.5)
            self.motor.set_power(0)
