import threading
import time
from utils.brick import TouchSensor

class EmergencyStopSystem:

    def __init__(self, sensor_port):
        self.touch_sensor = TouchSensor(sensor_port)
        self.emergency_thread = None
        self.stop_emergency_event = threading.Event()

    # Start emergency detection loop in thread
    def start_detecting_emergency(self):
        print("Start emergency detection loop in thread")
        self.emergency_thread = threading.Thread(target=self.detect_emergency_loop, daemon=True)

    # Stop emergency detection loop and wait until it ends before continuing
    def stop_detecting_emergency(self):
        print("Stop color detection loop in thread and wait until it ends before continuing")
        self.stop_emergency_event.set()
        if self.emergency_thread and self.emergency_thread.is_alive():
            self.emergency_thread.join()

    # Continuously detect emergency button and emergency event for robot to catch
    def detect_emergency_loop(self):
        while not self.stop_emergency_event.is_set():
            time.sleep(0.5)
            if self.touch_sensor.is_pressed():
                self.stop_emergency_event.set()

