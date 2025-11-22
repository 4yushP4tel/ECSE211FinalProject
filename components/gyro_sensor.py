import time
from utils.brick import EV3GyroSensor, wait_ready_sensors
import threading

class GyroSensor:
    THRESHOLD_FOR_READJUST = 8
    def __init__(self, port):
        self.sensor = EV3GyroSensor(port)
        self.orientation = 0
        self.orientation_lock = threading.Lock()
        self.monitor_orientation_thread = None
        self.stop_orientation_monitoring_flag = threading.Event()
        self.readjust_robot_flag = threading.Event()
        self.check_if_moving_straight_on_path = False
        self.reset_orientation()
    
    def start_monitoring_orientation(self):
        if self.monitor_orientation_thread and self.monitor_orientation_thread.is_alive():
            return
        self.stop_orientation_monitoring_flag.clear()
        self.monitor_orientation_thread = threading.Thread(target=self.monitor_orientation_loop, daemon=True)
        self.monitor_orientation_thread.start()

    def stop_monitoring_orientation(self):
        self.stop_orientation_monitoring_flag.set()
        if self.monitor_orientation_thread and self.monitor_orientation_thread.is_alive():
            self.monitor_orientation_thread.join()
    
    def get_orientation(self):
        orientation = self.sensor.get_abs_measure()
        print(f"Robot orientation: {orientation}")
        return orientation
    
    def monitor_orientation_loop(self):
        while not self.stop_orientation_monitoring_flag.is_set():
            with self.orientation_lock:
                self.orientation = self.get_orientation()
            if ((self.orientation > GyroSensor.THRESHOLD_FOR_READJUST
            or self.orientation < -GyroSensor.THRESHOLD_FOR_READJUST)
            and self.check_if_moving_straight_on_path
            ):
                self.readjust_robot_flag.set()
            time.sleep(0.1)

    def reset_orientation(self):
        #this should be done when the robot is turning into some room some 
        with self.orientation_lock:
            self.sensor.reset_measure()
            self.orientation=0


