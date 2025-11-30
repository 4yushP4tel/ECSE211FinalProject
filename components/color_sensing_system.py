import threading
import time
import math
from utils.brick import EV3ColorSensor, Motor

# RGB reference data (normalized)
color_data = {
    'orange': [86.0, 37.333333333333336, 16.866666666666667],
    'orange_front':[155.33333333333334, 70.4, 23.6],
    'yellow': [100.2, 73.73333333333333, 23.4],
    'yellow_front': [187.4, 149.8, 40.733333333333334],
    'white': [115.26666666666667, 106.6, 156.06666666666666],
    'green': [47.53333333333333, 64.13333333333334, 21.666666666666668],
    'green_front': [88.06666666666666, 131.26666666666668, 37.333333333333336],
    'red': [75.8, 12.866666666666667, 15.533333333333333],
    'red_front': [116.33333333333333, 16.2, 20.4],
    'black': [41.0, 27.133333333333333, 45.666666666666664],
    'blue': [109.93333333333334, 155.06666666666666, 233.0],
    'grey': [117.73333333333333, 111.53333333333333, 161.86666666666667]
}


class ColorSensingSystem:
    FRONT_POSITION = -90

    def __init__(self, sensor_port, motor_port):
        self.color_sensor = EV3ColorSensor(sensor_port)
        self.motor = Motor(motor_port)
        self.most_recent_color = None
        self.prev_color = None
        self.color_sensing_thread = None
        self.stop_sensing_flag = threading.Event()
        self.detect_hallway_on_right_flag = threading.Event()
        self.detect_invalid_entrance_flag = threading.Event()
        self.detect_valid_sticker_flag = threading.Event()
        self.detect_room_exit_flag = threading.Event()
        self.detect_entered_home_flag = threading.Event()
        self.sensor_failed_flag = threading.Event()
        self.color_lock = threading.Lock()
        self.motor.reset_encoder()
        self.motor.set_limits(power=25)
        self.is_in_hallway = True
        self.is_handling_room = False
        self.consecutive_none_count = 0
        self.is_heading_home = False

    def move_sensor_to_front(self):
        """Moves the sensor to the front of the robot when it tries to enter a room."""
        # Stop any ongoing movement first
        self.motor.set_dps(0)
        time.sleep(0.1)
        
        # Set position with controlled speed
        self.motor.set_limits(dps=120)
        self.motor.set_position(ColorSensingSystem.FRONT_POSITION)
        self.motor.wait_is_stopped()
        time.sleep(0.5)
        
        # Verify position and correct if needed
        current_pos = self.motor.get_position()
        if abs(current_pos - ColorSensingSystem.FRONT_POSITION) > 5:
            #print(f"Color sensor position off by {current_pos - ColorSensingSystem.FRONT_POSITION} degrees, correcting...")
            self.motor.set_position(ColorSensingSystem.FRONT_POSITION)
            self.motor.wait_is_stopped()
            time.sleep(0.3)

    def move_sensor_to_right_side(self):
        """Moves the sensor back to the side of the robot after it leaves a room."""
        # Stop any ongoing movement first
        self.motor.set_dps(0)
        time.sleep(0.1)
        
        # Set position with controlled speed
        self.motor.set_limits(dps=120)
        self.motor.set_position(0)
        self.motor.wait_is_stopped()
        time.sleep(0.5)
        
        # Verify position and correct if needed
        current_pos = self.motor.get_position()
        if abs(current_pos) > 1:
            #print(f"Color sensor position off by {current_pos} degrees, correcting...")
            self.motor.set_position(0)
            self.motor.wait_is_stopped()
            time.sleep(0.3)

    def detect_color(self):
        """
        Detect the color in front of the sensor and return a string:
        'Black', 'White', 'Red', 'Green', 'Orange', or 'Unknown'.
        """
        rgb = self.color_sensor.get_rgb()  # returns list [R, G, B]
        #print(f"RGB sensed: {rgb}")
        return self.detect_color_from_rgb(rgb)

    def detect_color_from_rgb(self, rgb):
        """
        Detect the closest matching color using raw RGB values
        
        Args:
            rgb: tuple of (R, G, B) values
        
        Returns:
            str: name of the closest matching color
        """
        r, g, b = rgb
        if r is None or g is None or b is None:
            return None
        if r + g + b == 0:
            return None
        min_distance = float('inf')
        closest_color = None

        # Calculate Euclidean distance to each color
        for color_name, color_mean in color_data.items():
            distance = math.sqrt(
                (r - color_mean[0]) ** 2 +
                (g - color_mean[1]) ** 2 +
                (b - color_mean[2]) ** 2
            )

            if distance < min_distance:
                min_distance = distance
                closest_color = color_name
        print(f"Closest color: {closest_color}")
        if closest_color.endswith('_front'):
            closest_color = closest_color[:-6]
        return closest_color

    def detect_color_loop(self):
        while not self.stop_sensing_flag.is_set():
            color = self.detect_color()
            #print(f"COLOR: {color}")
            
            # Track consecutive None readings for sensor failure detection
            if color is None:
                self.consecutive_none_count += 1
                if self.consecutive_none_count >= 3:
                    if not self.sensor_failed_flag.is_set():
                        print("WARNING: Color sensor failed! Waiting for recovery...")
                        self.sensor_failed_flag.set()
            else:
                # Sensor recovered
                if self.consecutive_none_count >= 3:
                    print("Color sensor recovered!")
                self.consecutive_none_count = 0
                if self.sensor_failed_flag.is_set():
                    self.sensor_failed_flag.clear()
            
            if color is not None:
                with self.color_lock:
                    self.prev_color = self.most_recent_color
                    self.most_recent_color = color
                    if self.prev_color in {"white", "grey", "yellow", "red", "orange", "blue", "green"} and color == "black" and self.is_in_hallway:
                        if self.detect_color() == "black":
                            print("<---------------------turn detected------------------------->")
                        
                            self.detect_hallway_on_right_flag.set()
                    elif self.prev_color == "orange" and color == "red" and self.is_handling_room:
                        if self.detect_color() == "red":
                            print("<----------------------invalid entrance detected------------------------>")
                            self.detect_invalid_entrance_flag.set()
                    elif self.prev_color == "yellow" and color == "orange" and self.is_handling_room:
                        if self.detect_color() == "orange":
                            self.detect_room_exit_flag.set()
                            print("<-------------------------exit detected--------------------->")
                    elif self.prev_color == "yellow" and color == "green" and self.is_handling_room:
                        if self.detect_color() == "green":
                            self.detect_valid_sticker_flag.set()
                            print("<-------------------------valid sticket detected--------------------->")
                    elif self.prev_color == "orange" and color == "orange" and self.is_heading_home:
                        self.detect_entered_home_flag.set()
                        print("<-------------------------home detected--------------------->")

            #print(f"Detected Color: {color}. Previous Color: {self.prev_color}")
            time.sleep(0.08)

    def start_detecting_color(self):
        if self.color_sensing_thread and self.color_sensing_thread.is_alive():
            print("THREAD DIED")
            return
        self.stop_sensing_flag.clear()
        self.color_sensing_thread = threading.Thread(target=self.detect_color_loop, daemon=True)
        self.color_sensing_thread.start()

    def stop_detecting_color(self):
        self.stop_sensing_flag.set()
        if self.color_sensing_thread and self.color_sensing_thread.is_alive():
            self.color_sensing_thread.join()

