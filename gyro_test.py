import time
from utils.brick import EV3GyroSensor

# Initialize gyro sensor with correct port (1 to 4)
gyro_sensor = EV3GyroSensor(4)

# If not moved, should print angle of 0
print(f"{gyro_sensor.get_abs_measure()}")

# Rotate gyro by 90 degrees and record angle
time.sleep(5)
print(f"Expected: 90"
      f"Result: {gyro_sensor.get_abs_measure()}")

# Rotate gyro by 360 degrees and record angle
time.sleep(5)
print(f"Expected: 450"
      f"Result: {gyro_sensor.get_abs_measure()}")

# Reset gyro angle
gyro_sensor.reset_measure()
print(f"Expected: 0"
      f"Result: {gyro_sensor.get_abs_measure()}")

# Rotate gyro by 10 degrees and record angle
time.sleep(5)
print(f"Expected: 10"
      f"Result: {gyro_sensor.get_abs_measure()}")

# Rotate gyro by -20 degrees and record angle
time.sleep(5)
print(f"Expected: -10"
      f"Result: {gyro_sensor.get_abs_measure()}")

