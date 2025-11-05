from utils.brick import EV3UltrasonicSensor

class UltrasonicSensor:
    SHORT_DISTANCE_FROM_WALL = 13 #cm
    LONG_DISTANCE_FROM_WALL = 85 #cm

    def get_distance(self):
        pass

    def check_if_in_acceptable_range(self, distance: int):
        # should check if in some range 
        pass