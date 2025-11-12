import threading
import time
import math
from utils.brick import EV3ColorSensor, Motor

# RGB reference data (normalized)
COLOR_DATA = {
    'blue': [0.06712646376600084, 0.19955909935902516, 0.733314436874974],
    'green': [0.10571292211720401, 0.608008307045022, 0.286278770837774],
    'red': [0.7538291750818987, 0.11987803436533612, 0.12629279055276518],
    'yellow': [0.5812878420188876, 0.3296251012413786, 0.08908705673973374],
    'no_color': [0.2910104513580598, 0.24223880535893885, 0.46675074328300137],
    'black': [0, 0, 0],
    'white': [1, 1, 1],
    'orange': [0.7, 0.3, 0.0]  # approximate
}

class ColorSensingSystem:
    TURN_DEGREES = 90

    def __init__(self, sensor_port, motor_port):
        self.color_sensor = EV3ColorSensor(sensor_port)
        self.motor = Motor(motor_port)
        self.is_in_front = False
        self.most_recent_color = None
        self.prev_color=None
        self.color_sensing_thread = None
        self.stop_sensing_flag = threading.Event()
        self.detect_hallway_on_right_flag = threading.Event()
        self.detect_invalid_entrance_flag = threading.Event()
        self.detect_valid_entrance_flag = threading.Event()
        self.detect_valid_sticker_flag = threading.Event()
        self.detect_room = threading.Event()
        self.detect_room_end = threading.Event()
        self.color_lock = threading.Lock()

    def move_sensor_to_front(self):
        """Moves the sensor to the front of the robot when it tries to enter a room."""
        self.motor.reset_encoder()
        self.motor.set_position(ColorSensingSystem.TURN_DEGREES)
        self.motor.wait_is_stopped()
        self.is_in_front = True
        time.sleep(0.5)

    def move_sensor_to_side(self):
        """Moves the sensor back to the side of the robot after it leaves a room."""
        self.motor.reset_encoder()
        self.motor.set_position(-ColorSensingSystem.TURN_DEGREES)
        self.motor.wait_is_stopped()
        self.is_in_front = False
        time.sleep(0.5)

    def move_sensor_side_to_side(self):
        """Moves sensor side to side for sticker detection"""
        self.motor.reset_encoder()
        self.move_sensor_to_side()
        self.motor.set_dps(100)
        self.motor.set_position(-150)

    def detect_color(self):
        """
        Detect the color in front of the sensor and return a string:
        'Black', 'White', 'Red', 'Green', 'Orange', or 'Unknown'.
        """
        rgb = self.color_sensor.get_rgb()  # returns list [R, G, B]
        return self._detect_color_from_rgb(rgb)

    def _detect_color_from_rgb(self, rgb):
        """Internal helper: detect closest color from RGB using Euclidean distance."""
        r, g, b = rgb
        denominator = r + g + b
        if denominator == 0:
            normalized_rgb = [0, 0, 0]
        else:
            normalized_rgb = [r / denominator, g / denominator, b / denominator]

        min_distance = float('inf')
        closest_color = 'Unknown'
        for color_name, color_mean in COLOR_DATA.items():
            distance = math.sqrt(
                (normalized_rgb[0] - color_mean[0]) ** 2 +
                (normalized_rgb[1] - color_mean[1]) ** 2 +
                (normalized_rgb[2] - color_mean[2]) ** 2
            )
            if distance < min_distance:
                min_distance = distance
                closest_color = color_name

        return closest_color.capitalize()  # e.g., "Red", "Green"
    
    def detect_color_loop(self):
        while not self.stop_sensing_flag.is_set():
            prev_color = self.most_recent_color
            color = self.detect_color()
            with self.color_lock:
                if self.prev_color == "White" and color == "Black":
                    self.detect_hallway_on_right_flag.set()
                elif color == "red":
                    self.detect_invalid_entrance_flag.set()
                elif color == "orange":
                    self.detect_valid_entrance_flag.set()
                elif color == "green":
                    self.detect_valid_sticker_flag.set()
                elif color == "yellow":
                    self.detect_room.set()
                elif self.prev_color == "yellow" and color == "white":
                    self.detect_room_end.set()
                self.prev_color = prev_color
                self.most_recent_color = color
            time.sleep(0.2)

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

    def detect_hallway_on_right(self):
        if(not self.is_in_front()):
            color = self.detect_color()
            return color.lower() == "Black"
        return False