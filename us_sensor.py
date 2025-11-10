from utils.brick import EV3UltrasonicSensor

class UltrasonicSensor:
    # the distances are always on the right of the robot
    SHORT_DISTANCE_FROM_WALL = 13 #cm
    LONG_DISTANCE_FROM_WALL = 85 #cm
    ACCEPTABLE_DISTANCES = {
        "short": (11, 15),
        "long": (83, 87)
    }
    def __init__(self):
        self.us_sensor = EV3UltrasonicSensor(4)
        self.us_sensor.set_mode_distance_cm()

    def get_distance(self)->float:
        distance = self.us_sensor.get_cm()
        if distance is None:
            print("US sensor did not read a distance")
            return float('inf')
        return distance

    def check_adjustment(self, curr_distance: int, wall_pointed_to:str) -> str:
        if wall_pointed_to not in UltrasonicSensor.ACCEPTABLE_DISTANCES.keys():
            print(f"Invalid wall_pointed_to: {wall_pointed_to}. Must be 'short' or 'long'.")
        
        low, high = UltrasonicSensor.ACCEPTABLE_DISTANCES[wall_pointed_to]
        return "l" if curr_distance>high else "r" if curr_distance<low else "ok"