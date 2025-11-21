import threading
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


class ColorSensingSystem:

    def __init__(self, sensor_port, motor_port):
        self.color_sensor = EV3ColorSensor(sensor_port)
        self.sweeper = Motor(motor_port)
        self.most_recent_color = ""
        self.color_sensing_thread = None
        self.stop_color_event = threading.Event()
        self.detect_black_event = threading.Event()
        self.detect_orange_event = threading.Event()
        self.detect_blue_event = threading.Event()
        self.detect_red_event = threading.Event()
        self.detect_green_event = threading.Event()

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

            if color == "black":
                self.detect_black_event.set()
            elif color == "orange":
                self.detect_orange_event.set()
            elif color == "blue":
                self.detect_blue_event.set()
            elif color == "red":
                self.detect_red_event.set()
            elif color == "green":
                self.detect_green_event.set()

            self.most_recent_color = color

    # Detect the closest matching color using raw RGB values
    def detect_color_from_rgb(self, rgb):
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
