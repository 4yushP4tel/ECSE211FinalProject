import threading
from utils.brick import EV3UltrasonicSensor


class UltrasonicSensor:
    # Distances are always on the right of the robot
    SHORT_DISTANCE_FROM_WALL = 5
    THRESHOLD_DISTANCE = 0.5
    UPPER_LIMIT = SHORT_DISTANCE_FROM_WALL + THRESHOLD_DISTANCE
    LOWER_LIMIT = SHORT_DISTANCE_FROM_WALL - THRESHOLD_DISTANCE

    def __init__(self, sensor_port):
        self.us_sensor = EV3UltrasonicSensor(sensor_port)
        self.readjustment_direction = "ok"
        self.monitor_distance_thread = None
        self.stop_distance_event = threading.Event()

    # Start distance monitoring loop in thread
    def start_monitoring_distance(self):
        print("Start distance monitoring in thread")
        self.monitor_distance_thread = threading.Thread(target=self.monitor_distance_loop, daemon=True)
        self.monitor_distance_thread.start()

    # Stop distance monitoring loop in thread and wait until it ends before continuing
    def stop_monitoring_distance(self):
        print("Stop distance monitoring loop in thread and wait until it ends before continuing")
        self.stop_distance_event.set()
        if self.monitor_distance_thread and self.monitor_distance_thread.is_alive():
            self.monitor_distance_thread.join()

    # Continuously monitor distance and set readjustment direction for robot to catch
    def monitor_distance_loop(self):
        while not self.stop_distance_event.is_set():
            distance = self.us_sensor.get_cm()
            self.readjustment_direction = self.check_adjustment(distance)

    # Check adjustment direction needed
    def check_adjustment(self, distance):
        return "left" if distance > UltrasonicSensor.UPPER_LIMIT else "right" if distance < UltrasonicSensor.LOWER_LIMIT else "ok"
