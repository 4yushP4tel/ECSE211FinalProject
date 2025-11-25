from utils.brick import EV3GyroSensor
import threading


class GyroSensor:
    THRESHOLD_FOR_READJUST = 8

    def __init__(self, port):
        self.gyro_sensor = EV3GyroSensor(port)
        self.orientation = 0
        self.monitor_orientation_thread = None
        self.stop_orientation_event = threading.Event()
        self.readjust_left_event = threading.Event()
        self.readjust_right_event = threading.Event()

    # Start orientation monitoring loop in thread
    def start_monitoring_orientation(self):
        print("Start distance monitoring loop in thread")
        self.monitor_orientation_thread = threading.Thread(target=self.monitor_orientation_loop, daemon=True)
        self.monitor_orientation_thread.start()

    # Stop orientation monitoring loop in thread and wait until it ends before continuing
    def stop_monitoring_orientation(self):
        print("Stop orientation monitoring loop in thread and wait until it ends before continuing")
        self.stop_orientation_event.set()
        if self.monitor_orientation_thread and self.monitor_orientation_thread.is_alive():
            self.monitor_orientation_thread.join()

    # Continuously monitor orientation and set corresponding events for robot to catch
    def monitor_orientation_loop(self):
        while not self.stop_orientation_event.is_set():
            self.orientation = self.gyro_sensor.get_abs_measure()

            if self.orientation > GyroSensor.THRESHOLD_FOR_READJUST:
                self.readjust_left_event.set()
            elif self.orientation < -GyroSensor.THRESHOLD_FOR_READJUST:
                self.readjust_right_event.set()
