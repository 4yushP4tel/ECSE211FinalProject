import time
from utils.brick import EV3GyroSensor, wait_ready_sensors
import threading

THRESHOLD_FOR_READJUST = 2

class GyroSensor:
     # Increased from 5 to reduce frequent corrections
    def __init__(self, port):
        self.sensor = EV3GyroSensor(port)
        self.orientation = 0
        self.orientation_lock = threading.Lock()
        self.monitor_orientation_thread = None
        self.stop_orientation_monitoring_flag = threading.Event()
        self.readjust_robot_flag = threading.Event()
        self.check_if_moving_straight_on_path = True
        self.last_readjust_time = 0  # Track last realignment to prevent wobbling
        self.readjust_cooldown = 2.0  # Seconds to wait before allowing another realignment
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
        #print(f"Current orientation: {orientation}")
        return orientation
    
    def monitor_orientation_loop(self):
        while not self.stop_orientation_monitoring_flag.is_set():
            with self.orientation_lock:
                self.orientation = self.get_orientation()
            if self.orientation is None:
                time.sleep(0.01)
                continue
            
            # Check if readjustment is needed and cooldown period has passed
            if (self.orientation is not None and 
                (self.orientation > THRESHOLD_FOR_READJUST or self.orientation < -(THRESHOLD_FOR_READJUST))):
                
                # Only trigger if enough time has passed since last realignment (prevent wobbling)
                time_since_last = time.time() - self.last_readjust_time
                if time_since_last >= self.readjust_cooldown:
                    print(f"readjustment needed, the orientation is: {self.orientation}")
                    self.readjust_robot_flag.set()
                else:
                    # Still in cooldown period
                    pass
            
            time.sleep(0.01)

    def set_readjust_cooldown(self, cooldown_seconds):
        """
        Temporarily change the realignment cooldown period.
        Useful for situations that need more/less frequent realignment.
        
        Args:
            cooldown_seconds: Time in seconds between realignment triggers
        """
        self.readjust_cooldown = cooldown_seconds
        print(f"Realignment cooldown set to {cooldown_seconds}s")
    
    def reset_orientation(self):
        #this should be done when the robot is turning into some room some
        
        self.stop_orientation_monitoring_flag.set()
        
        if self.monitor_orientation_thread and self.monitor_orientation_thread.is_alive():
            self.monitor_orientation_thread.join()
        
        self.sensor.set_mode(EV3GyroSensor.Mode.DPS)
        time.sleep(0.01)
        self.sensor.set_mode(EV3GyroSensor.Mode.ABS)
        time.sleep(0.01)

        self.stop_orientation_monitoring_flag.clear()

        self.start_monitoring_orientation()

        with self.orientation_lock:
            self.orientation=0


        print("Gyro reset complete")


