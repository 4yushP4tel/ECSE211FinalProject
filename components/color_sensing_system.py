import threading
import time
import math
from utils.brick import EV3ColorSensor, Motor

# RGB reference data (normalized)
color_data = {
    'orange': [193.73333333333332, 90.4, 33.2],
    'yellow': [231.33333333333334, 187.53333333333333, 47.0],
    'white': [139.8, 130.06666666666666, 191.46666666666667],
    'green': [108.8, 158.53333333333333, 45.13333333333333],
    'red': [145.13333333333333, 18.6, 26.866666666666667],
    'black': [25.733333333333334, 26.8, 28.933333333333334],
    'blue': [144.0, 209.66666666666666, 295.6666666666667],
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
        self.color_lock = threading.Lock()
        self.motor.reset_encoder()
        self.motor.set_limits(power=25)
        self.is_in_hallway = True
        self.is_handling_room = False

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
            print(f"Color sensor position off by {current_pos - ColorSensingSystem.FRONT_POSITION} degrees, correcting...")
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
        if abs(current_pos) > 5:
            print(f"Color sensor position off by {current_pos} degrees, correcting...")
            self.motor.set_position(0)
            self.motor.wait_is_stopped()
            time.sleep(0.3)

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

        return closest_color

    def detect_color_loop(self):
        while not self.stop_sensing_flag.is_set():
            color = self.detect_color()
            print(f"COLOR: {color}")
            if color is not None:
                with self.color_lock:
                    self.prev_color = self.most_recent_color
                    self.most_recent_color = color
                    if self.prev_color in {"white", "grey", "yellow", "red", "orange", "blue", "green"} and color == "black" and self.is_in_hallway:
                        print("<---------------------turn detected------------------------->")
                        
                        self.detect_hallway_on_right_flag.set()
                    elif self.prev_color == "orange" and color == "red" and self.is_handling_room:
                        if self.detect_color() == "red":
                            print("<----------------------invalid entrance detected------------------------>")
                            self.detect_invalid_entrance_flag.set()
                    elif self.prev_color == "yellow" and color == "orange" and self.is_handling_room:
                        self.detect_room_exit_flag.set()
                        print("<-------------------------exit detected--------------------->")
                    elif self.prev_color == "yellow" and color == "green" and self.is_handling_room:
                        if self.detect_color() == "green":
                            self.detect_valid_sticker_flag.set()
                            print("<-------------------------valid sticket detected--------------------->")
                    elif self.prev_color == "orange" and color == "blue" and self.is_handling_room:
                        self.detect_entered_home_flag.set()
                        print("<-------------------------home detected--------------------->")

            #print(f"Detected Color: {color}. Previous Color: {self.prev_color}")
            time.sleep(0.05)

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

