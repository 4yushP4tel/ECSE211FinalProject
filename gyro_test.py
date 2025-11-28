import time
from utils.brick import EV3GyroSensor, wait_ready_sensors

# Initialize gyro sensor with correct port (1 to 4)
gyro_sensor = EV3GyroSensor(2)
wait_ready_sensors(debug=True)

# If not moved, should print angle of 0
print(f"{gyro_sensor.get_abs_measure()}")
gyro_sensor.reset_measure()

while True:
    print(gyro_sensor.get_abs_measure())
    time.sleep(0.5)
# Rotate gyro by 90 degrees and record angle
time.sleep(10)
print(f"Expected: 90 \nResult: {gyro_sensor.get_abs_measure()}")

# Rotate gyro by 360 degrees and record angle
#time.sleep(10)
#print(f"Expected: 450 \nResult: {gyro_sensor.get_abs_measure()}")

# Reset gyro angle
#gyro_sensor.reset_measure()
#print(f"Expected: 0\nResult: {gyro_sensor.get_abs_measure()}")

# Rotate gyro by 10 degrees and record angle
#time.sleep(10)
#print(f"Expected: 10\nResult: {gyro_sensor.get_abs_measure()}")

#Rotate gyro by -20 degrees and record angle
#time.sleep(10)
#print(f"Expected: -10\nResult: {gyro_sensor.get_abs_measure()}")

