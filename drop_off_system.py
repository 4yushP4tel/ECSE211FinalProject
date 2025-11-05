from utils.brick import Motor

class DropOffSystem:
    def __init__(self, motor_port):
        self.motor = Motor(motor_port)

    def deliver_package(self):
        pass