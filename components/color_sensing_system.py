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
    'blue': [114.95, 167.65, 247.30]
}

class   ColorSensingSystem:
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
        time.sleep(0.2)

    def move_sensor_to_side(self):
        """Moves the sensor back to the side of the robot after it leaves a room."""
        self.motor.reset_encoder()
        self.motor.set_position(-ColorSensingSystem.TURN_DEGREES)
        self.motor.wait_is_stopped()
        self.is_in_front = False
        time.sleep(0.2)

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
        print(f"RGB sensed: {rgb}")
        return self._detect_color_from_rgb(rgb)


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
    
    def detect_color_loop(self):
        while not self.stop_sensing_flag.is_set():
            prev_color = self.most_recent_color
            color = self.detect_color()
            with self.color_lock:
                if self.prev_color == "white" and color == "black":
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

    def detect_hallway_on_right(self):
        if(not self.is_in_front()):
            color = self.detect_color()
            return color.lower() == "black"
        return False