import threading
import math
import time
from utils.brick import EV3ColorSensor, Motor

# RGB reference data (normalized)
color_data = {
    'orange': [184, 84, 31],
    'yellow': [209, 172, 42],
    'white': [245, 252, 301],
    'green': [100, 154, 44],
    'red': [137, 20, 25],
    'black': [26, 22, 27],
    'blue': [114, 163, 238],
    'grey': [209, 213, 260]
}


class ColorSensingSystem:

    def __init__(self, sensor_port, motor_port):
        self.color_sensor = EV3ColorSensor(sensor_port)
        self.sweeper = Motor(motor_port)
        self.color_sensing_thread = None
        self.stop_color_event = threading.Event()
        self.detect_black_event = threading.Event()
        self.detect_orange_event = threading.Event()
        self.detect_blue_event = threading.Event()
        self.detect_red_event = threading.Event()
        self.detect_green_event = threading.Event()
        self.color_lock = threading.Lock()
        self.most_recent_color = None
        self.prev_color = None

    # Start color detection loop in thread
    def start_detecting_color(self):
        print("Color detection loop started in thread")
        self.stop_color_event.clear()
        self.color_sensing_thread = threading.Thread(target=self.detect_color_loop, daemon=True)
        self.color_sensing_thread.start()

    # Stop color detection loop in thread and wait until it ends before continuing
    def stop_detecting_color(self):
        print("Stop color detection loop in thread and wait until it ends before continuing")
        self.stop_color_event.set()
        if self.color_sensing_thread and self.color_sensing_thread.is_alive():
            self.color_sensing_thread.join()

    # Continuously detect color and set corresponding events for robot to catch
    def detect_color_loop(self):
        while not self.stop_color_event.is_set():
            color = self.detect_color_from_rgb(self.color_sensor.get_rgb())

            if color is not None:
                if color == "black":
                    self.detect_black_event.set()
                elif color == "orange":
                    self.detect_orange_event.set()
                elif color == "blue":
                    self.detect_blue_event.set()
                elif color == "red":
                    self.detect_red_event.set()
                elif color == "green" and self.prev_color and self.prev_color == "green":
                    self.detect_green_event.set()
            print(color)
            time.sleep(0.05)
            self.prev_color = color

    # Detect the closest matching color using raw RGB values
    def detect_color_from_rgb(self, rgb):
        r, g, b = rgb
        if r is None or g is None or b is None:
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
        return closest_color
