import threading
import time
import math
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

class   ColorSensingSystem:
    FRONT_POSITION = -93
    ALL_THE_WAY_LEFT_POSITION = -180

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
        self.detect_room_exit_flag = threading.Event()
        self.detect_entered_home_flag = threading.Event()
        self.detect_room = threading.Event()
        self.detect_room_end = threading.Event()
        self.color_lock = threading.Lock()
        self.motor.reset_encoder()
        self.motor.set_limits(power=20, dps=150)

    def move_sensor_to_front(self):
        """Moves the sensor to the front of the robot when it tries to enter a room."""
        self.motor.set_position(ColorSensingSystem.FRONT_POSITION)
        self.motor.wait_is_stopped()
        self.is_in_front = True
        time.sleep(0.2)

    def move_sensor_to_right_side(self):
        """Moves the sensor back to the side of the robot after it leaves a room."""
        self.motor.set_position(0)
        self.motor.wait_is_stopped()
        self.is_in_front = False
        time.sleep(0.2)

    def move_sensor_side_to_side(self):
        """Moves sensor side to side for sticker detection"""
        self.motor.set_position(0)
        print("stopped finish" + f" {self.motor.get_position()}")
        time.sleep(1.5)
        self.motor.set_position(ColorSensingSystem.ALL_THE_WAY_LEFT_POSITION)
        print("stopped finish 2" + f" {self.motor.get_position()}")
        time.sleep(1.5)
        self.is_in_front = False
        

    def detect_color(self):
        """
        Detect the color in front of the sensor and return a string:
        'Black', 'White', 'Red', 'Green', 'Orange', or 'Unknown'.
        """
        rgb = self.color_sensor.get_rgb()  # returns list [R, G, B]
        print(f"RGB sensed: {rgb}")
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
            color = self.detect_color()
            print(color)
            if color[0] is None:
                color = self.prev_color
            with self.color_lock:
                self.prev_color = self.most_recent_color
                self.most_recent_color = color
                if (self.prev_color in ["white","grey", "orange", "yellow", "blue", "green"]) and color == "black":
                    self.detect_hallway_on_right_flag.set()
                elif color == "red":
                    self.detect_invalid_entrance_flag.set()
                elif self.prev_color == "orange" and color == "yellow":
                    self.detect_valid_entrance_flag.set()
                elif self.prev_color=="yellow" and color=="orange":
                    self.detect_room_exit_flag.set()
                elif self.prev_color=="green" and color == "green":
                    self.detect_valid_sticker_flag.set()
                elif self.prev_color == "yellow" and (color in ["white","grey"]):
                    self.detect_room_end.set()
                elif self.prev_color=="orange" and color=="blue":
                    self.detect_entered_home_flag.set()

            print(f"Detected Color: {color}. Previous Color: {self.prev_color}")
            time.sleep(0.05)

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

