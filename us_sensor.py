import threading
from time import time
from utils.brick import EV3UltrasonicSensor

class UltrasonicSensor:
    # the distances are always on the right of the robot
    SHORT_DISTANCE_FROM_WALL = 13
    LONG_DISTANCE_FROM_WALL = 85
    THRESHOLD_DISTANCE = 1
    ACCEPTABLE_DISTANCES = {
        "short": (SHORT_DISTANCE_FROM_WALL-THRESHOLD_DISTANCE, SHORT_DISTANCE_FROM_WALL+THRESHOLD_DISTANCE),
        "long": (LONG_DISTANCE_FROM_WALL-THRESHOLD_DISTANCE, LONG_DISTANCE_FROM_WALL+THRESHOLD_DISTANCE)
    }
    def __init__(self):
        self.us_sensor = EV3UltrasonicSensor(4)
        self.wall_pointed_to = "short"
        self.latest_distance = float('inf')
        self.latest_direction = "ok"
        self.lock = threading.Lock()
        self.stop_flag = threading.Event()
        self.monitor_thread = None

    def start_monitoring_distance(self):
        #allows to monitor the distance in the background
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        self.stop_flag.clear()
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring_distance(self):
        self.stop_flag.set()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join()

    def monitor_loop(self):
        while not self.stop_flag.is_set():
            distance = self.get_distance()
            direction = self.check_adjustment(distance, self.wall_pointed_to)
            with self.lock:
                self.latest_distance = distance
                self.latest_direction = direction
            time.sleep(0.2)

    def get_distance(self)->float:
        distance = self.us_sensor.get_cm()
        if distance is None:
            print("US sensor did not read a distance")
            return float('inf')
        return distance

    def check_adjustment(self, curr_distance: int, wall_pointed_to:str) -> str:
        if wall_pointed_to not in UltrasonicSensor.ACCEPTABLE_DISTANCES.keys():
            print(f"Invalid wall_pointed_to: {wall_pointed_to}. Must be 'short' or 'long'.")
        
        low, high = UltrasonicSensor.ACCEPTABLE_DISTANCES[wall_pointed_to]
        return "l" if curr_distance>high else "r" if curr_distance<low else "ok"