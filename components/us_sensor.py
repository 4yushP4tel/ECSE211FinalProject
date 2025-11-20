import threading
import time
from utils.brick import EV3UltrasonicSensor

class UltrasonicSensor:
    # the distances are always on the right of the robot
    SHORT_DISTANCE_FROM_WALL = 5
    THRESHOLD_DISTANCE = 0.5
    ACCEPTABLE_DISTANCES = {
        "short": (SHORT_DISTANCE_FROM_WALL-THRESHOLD_DISTANCE, SHORT_DISTANCE_FROM_WALL+THRESHOLD_DISTANCE),
    }
    def __init__(self, sensor_port: int):
        self.us_sensor = EV3UltrasonicSensor(sensor_port)
        self.wall_pointed_to = "short"
        self.latest_distance = float('inf')
        self.latest_readjustment_direction = "ok"
        self.lock = threading.Lock()
        self.monitor_distance_thread = None

    def start_monitoring_distance(self):
        #allows to monitor the distance in the background
        if self.monitor_distance_thread and self.monitor_distance_thread.is_alive():
            return
        self.monitor_distance_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_distance_thread.start()
    
    def stop_monitoring_distance(self):
        if self.monitor_distance_thread and self.monitor_distance_thread.is_alive():
            self.monitor_distance_thread.join()

    def monitor_loop(self):
        while True:
            distance = self.get_distance()
            direction = self.check_adjustment(distance, self.wall_pointed_to)
            with self.lock:
                self.latest_distance = distance
                self.latest_readjustment_direction = direction
            print(f"US Sensor Distance: {distance} cm, Adjustment Needed: {direction}")

    def get_distance(self)->float:
        distance = self.us_sensor.get_cm()
        if distance is None:
            print("US sensor did not read a distance")
            return SHORT_DISTANCE_FROM_WALL
        return distance

    def check_adjustment(self, curr_distance: float, wall_pointed_to:str) -> str:
        low, high = UltrasonicSensor.ACCEPTABLE_DISTANCES[wall_pointed_to]
        return "left" if curr_distance>high else "right" if curr_distance<low else "ok"