import threading
import time
import math
from utils.brick import EV3ColorSensor, Motor

# RGB reference data (normalized)
color_data = {
    'orange': [173.44, 81.67, 27.17],
    'yellow': [199.61, 164.11, 39.06],
    'white': [234.59, 245.94, 296.59],
    'green': [106.35, 169.82, 41.88],
    'red': [140.06, 18.89, 22.22],
    'black': [33.70, 35.45, 21.35],
    'blue': [114.95, 167.65, 247.30],
    'grey': [177, 188, 221]
}


def detect_color_from_rgb(rgb):
    """
    Detect the closest matching color using raw RGB values

    Args:
        rgb: tuple of (R, G, B) values

    Returns:
        str: name of the closest matching color
    """
    r, g, b = rgb

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

    return closest_color


class   ColorSensingSystem:

    def __init__(self, sensor_port, motor_port):
        self.color_sensor = EV3ColorSensor(sensor_port)
        self.motor = Motor(motor_port)
        self.most_recent_color = None
        self.prev_color = None
        self.color_sensing_thread = None
        self.sweep_thread = None
        self.motor_position = None
        self.stop_sensing_flag = threading.Event()
        self.stop_sweep_flag = threading.Event()
        self.detect_hallway_on_right_flag = threading.Event()
        self.detect_invalid_entrance_flag = threading.Event()
        self.detect_valid_entrance_flag = threading.Event()
        self.detect_valid_sticker_flag = threading.Event()
        self.detect_home_flag = threading.Event()
        self.detect_room_flag = threading.Event()
        self.detect_room_end_flag = threading.Event()
        self.detect_room_exit_flag = threading.Event()
        self.color_lock = threading.Lock()

    def move_sensor_side_to_side(self):
        """Moves sensor side to side for sticker detection"""
        while True:
            if not self.stop_sweep_flag.is_set():
                self.motor.reset_encoder()
                self.move.set_power(20)
                time.sleep(2)
                self.move.set_power(-20)
                time.sleep(2)

    def start_sweep(self):
        if self.sweep_thread and self.sweep_thread.is_alive():
            return
        self.sweep_thread = threading.Thread(target=self.detect_color_loop, daemon=True)
        self.stop_sweep_flag.set()
        self.sweep_thread.start()

    def stop_sweep(self):
        self.stop_sweep_flag.set()
        if self.sweep_thread and self.sweep_thread.is_alive():
            self.sweep_thread.join()

    def detect_color(self):
        """
        Detect the color in front of the sensor and return a string:
        'Black', 'White', 'Red', 'Green', 'Orange', or 'Unknown'.
        """
        rgb = self.color_sensor.get_rgb()  # returns list [R, G, B]
        print(f"RGB sensed: {rgb}")
        return self.detect_color_from_rgb(rgb)

    def detect_color_loop(self):
        while not self.stop_sensing_flag.is_set():
            prev_color = self.most_recent_color
            color = self.detect_color()
            with self.color_lock:
                if self.color == "black":
                    self.detect_hallway_on_right_flag.set()
                elif color == "red":
                    self.detect_invalid_entrance_flag.set()
                elif color == "blue":
                    self.detect_home_flag.set()
                elif color == "green":
                    self.motor_position = self.motor.get_position()
                    self.detect_valid_sticker_flag.set()
                elif color == "yellow" or color == "orange":
                    self.detect_room_flag.set()
                elif self.prev_color == "yellow" and (color == "white" or color=="grey"):
                    self.detect_room_end_flag.set()
                elif self.prev_color == "yellow" and color == "orange":
                    self.detect_room_exit_flag.set()
                self.prev_color = prev_color
                self.most_recent_color = color
            print(f"Detected Color: {color}. Previous Color: {prev_color}")
            time.sleep(0.5)

    def start_detecting_color(self):
        if self.color_sensing_thread and self.color_sensing_thread.is_alive():
            return
        self.stop_sensing_flag.clear()
        self.color_sensing_thread = threading.Thread(target=self.detect_color_loop, daemon=True)
        self.color_sensing_thread.start()
    
    def stop_detecting_color(self):
        self.stop_sensing_flag.set()
        if self.color_sensing_thread and self.color_sensing_thread.is_alive():
            self.color_sensing_thread.join()