# Package Delivery Turn Direction Fix

## The Problem

When delivering packages, if the calculated angle is **positive**, the robot turns **LEFT** instead of **RIGHT**.

## Why This Happens

The issue is in how the sensor's motor position is converted to a robot turn angle.

### Current Code (Line 591 & 608):
```python
angle = self.color_sensing_system.motor.get_position() + 90
new_angle = angle - self.gyro_sensor.get_orientation()
```

### The Turn Convention (Confirmed Correct):
In `turn_x_deg()`:
- **Positive angle** → Turn RIGHT (left wheel forward, right wheel back)
- **Negative angle** → Turn LEFT (left wheel back, right wheel forward)

---

## Root Cause Options

### Option 1: Sign Convention is Inverted
The motor position and the desired turn angle have opposite sign conventions.

**Fix:** Negate the calculated angle
```python
new_angle = -(angle - self.gyro_sensor.get_orientation())
```

**When to use:** If the sensor motor's positive direction means "turn left" instead of "turn right"

### Option 2: The +90 Offset is Wrong
The `+ 90` might not be the correct offset, or it might need to be `- 90` instead.

**Fix:** Change the offset sign
```python
angle = self.color_sensing_system.motor.get_position() - 90  # Changed from +90
```

**When to use:** If the sensor coordinate frame needs a different offset

---

## Current Implementation

I've already applied **Option 1** (negating the angle):

```python
new_angle = -(angle - self.gyro_sensor.get_orientation())
```

And added debug output to help diagnose:
```python
print(f"  (sensor motor position was {motor_pos}, angle={angle})")
```

---

## How to Test & Choose the Right Fix

### Test 1: Observe the motor position
When the robot detects a green sticker:
1. Look at the debug output: `ARM POSITION <value>`
2. Note if it says "RIGHT side" or "LEFT side"
3. Observe which way the robot actually turns

### Test 2: Expected Behavior

| Sensor Detects On | Motor Position | Should Turn |
|-------------------|----------------|-------------|
| Right side | Positive (e.g., +45) | RIGHT |
| Left side | Negative (e.g., -45) | LEFT |
| Center | Near 0 | Minimal/None |

### Test 3: Try Each Fix

#### Currently Active: Option 1 (Negated angle)
```python
new_angle = -(angle - self.gyro_sensor.get_orientation())
```

If this **doesn't work**, try **Option 2**:

Change line 591:
```python
# FROM:
angle = self.color_sensing_system.motor.get_position() + 90

# TO:
angle = self.color_sensing_system.motor.get_position() - 90
```

And revert line 608 back to:
```python
# Revert to:
new_angle = angle - self.gyro_sensor.get_orientation()
```

---

## Debug Output Explanation

When you run the robot, you'll see:
```
STOPPING ARM
ARM POSITION <motor_pos>
CALCULATED ANGLE: <angle>
  (motor_pos=<value> + 90 = <angle>)
  → Sticker detected on RIGHT/LEFT side of robot
Turning to package: current=<curr_orient>°, turning <new_angle>°
  (sensor motor position was <motor_pos>, angle=<angle>)
```

**Use this to verify:**
1. Is the "RIGHT/LEFT side" detection correct?
2. Does the turn angle have the right sign?
3. Does the robot turn the correct direction?

---

## Alternative: Simplified Approach

If both options above don't work, consider this simpler approach:

**Replace the entire angle calculation** (lines 591 & 608):

```python
# Option 3: Direct approach
# The motor position directly indicates turn direction
angle = self.color_sensing_system.motor.get_position()
new_angle = -angle  # Negate if sign convention is opposite
print(f"Motor at {angle}°, turning {new_angle}°")
```

This removes the `+ 90` offset entirely and uses the motor position directly.

---

## Recommendation

1. **Test current fix (Option 1)** - Already applied
2. If robot still turns wrong direction → **Try Option 2**
3. If still wrong → **Try Option 3** (simplified)
4. Once working, **remove the `+ 90` offset** if it's not needed

The `+ 90` suggests there was an original offset/calibration, but it might not be correct for your setup.

