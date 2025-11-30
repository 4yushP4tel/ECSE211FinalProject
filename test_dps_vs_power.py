"""
Test script to compare set_power vs set_dps for straight-line movement.

This script will help you evaluate which method provides better straight-line precision.
It tests both approaches and measures drift using the gyro sensor.
"""

import time
from components.wheel import Wheel
from components.gyro_sensor import GyroSensor
from utils.brick import reset_brick, wait_ready_sensors

def test_power_based_movement():
    """Test straight movement using set_power (current approach)"""
    print("\n" + "="*60)
    print("TEST 1: Using set_power (open-loop control)")
    print("="*60)
    
    right_wheel = Wheel('B')
    left_wheel = Wheel('C')
    gyro_sensor = GyroSensor(4)
    
    wait_ready_sensors()
    time.sleep(1)
    
    # Reset gyro orientation
    gyro_sensor.reset_orientation()
    print(f"Starting orientation: {gyro_sensor.orientation}°")
    
    # Move forward for 3 seconds using power
    POWER_LEFT = 22.3
    POWER_RIGHT = 22.5
    
    print(f"Moving with LEFT={POWER_LEFT}%, RIGHT={POWER_RIGHT}%")
    left_wheel.spin_wheel_continuously(POWER_LEFT)
    right_wheel.spin_wheel_continuously(POWER_RIGHT)
    
    # Monitor drift over 3 seconds
    start_time = time.time()
    max_drift = 0
    while time.time() - start_time < 3:
        current_drift = abs(gyro_sensor.orientation)
        if current_drift > max_drift:
            max_drift = current_drift
        print(f"  Orientation: {gyro_sensor.orientation:+.2f}° | Max drift: {max_drift:.2f}°", end='\r')
        time.sleep(0.1)
    
    # Stop
    left_wheel.stop_spinning()
    right_wheel.stop_spinning()
    
    final_orientation = gyro_sensor.orientation
    print(f"\n\nFinal orientation: {final_orientation:+.2f}°")
    print(f"Maximum drift: {max_drift:.2f}°")
    
    return max_drift, final_orientation

def test_dps_based_movement():
    """Test straight movement using set_dps (closed-loop control)"""
    print("\n" + "="*60)
    print("TEST 2: Using set_dps (closed-loop control)")
    print("="*60)
    
    right_wheel = Wheel('B')
    left_wheel = Wheel('C')
    gyro_sensor = GyroSensor(4)
    
    wait_ready_sensors()
    time.sleep(1)
    
    # Reset gyro orientation
    gyro_sensor.reset_orientation()
    print(f"Starting orientation: {gyro_sensor.orientation}°")
    
    # Move forward for 3 seconds using DPS
    # You can configure different DPS for each wheel if needed
    DPS_LEFT = 300   # Adjust this if robot veers
    DPS_RIGHT = 300  # Adjust this if robot veers
    
    print(f"Moving with LEFT={DPS_LEFT} dps, RIGHT={DPS_RIGHT} dps")
    left_wheel.spin_wheel_at_dps(DPS_LEFT)
    right_wheel.spin_wheel_at_dps(DPS_RIGHT)
    
    # Monitor drift over 3 seconds
    start_time = time.time()
    max_drift = 0
    while time.time() - start_time < 3:
        current_drift = abs(gyro_sensor.orientation)
        if current_drift > max_drift:
            max_drift = current_drift
        print(f"  Orientation: {gyro_sensor.orientation:+.2f}° | Max drift: {max_drift:.2f}°", end='\r')
        time.sleep(0.1)
    
    # Stop
    left_wheel.stop_spinning()
    right_wheel.stop_spinning()
    
    final_orientation = gyro_sensor.orientation
    print(f"\n\nFinal orientation: {final_orientation:+.2f}°")
    print(f"Maximum drift: {max_drift:.2f}°")
    
    return max_drift, final_orientation

def main():
    try:
        print("\n" + "#"*60)
        print("# Comparing set_power vs set_dps for straight movement")
        print("#"*60)
        print("\nThis test will:")
        print("1. Move the robot forward for 3 seconds using set_power")
        print("2. Wait for 2 seconds")
        print("3. Move the robot forward for 3 seconds using set_dps")
        print("4. Compare the drift in both cases")
        print("\nPress Enter when ready to start...")
        input()
        
        # Test 1: Power-based
        power_max_drift, power_final = test_power_based_movement()
        
        print("\n\nWaiting 2 seconds before next test...")
        time.sleep(2)
        
        # Test 2: DPS-based
        dps_max_drift, dps_final = test_dps_based_movement()
        
        # Summary
        print("\n" + "="*60)
        print("COMPARISON SUMMARY")
        print("="*60)
        print(f"set_power approach:")
        print(f"  - Max drift:         {power_max_drift:.2f}°")
        print(f"  - Final orientation: {power_final:+.2f}°")
        print(f"\nset_dps approach:")
        print(f"  - Max drift:         {dps_max_drift:.2f}°")
        print(f"  - Final orientation: {dps_final:+.2f}°")
        
        improvement = ((power_max_drift - dps_max_drift) / power_max_drift * 100) if power_max_drift > 0 else 0
        print(f"\nImprovement: {improvement:+.1f}% {'(better)' if improvement > 0 else '(worse)'}")
        
        if dps_max_drift < power_max_drift:
            print("\n✓ set_dps provides BETTER straight-line precision!")
        elif dps_max_drift > power_max_drift:
            print("\n✗ set_dps provides WORSE straight-line precision")
        else:
            print("\n= Both methods show similar precision")
        
        print("\n" + "="*60)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    finally:
        reset_brick()

if __name__ == "__main__":
    main()

