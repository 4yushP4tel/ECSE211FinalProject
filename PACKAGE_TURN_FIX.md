# Package Delivery Turn Direction Fix

## The Problem

When the robot detects a package and calculates a positive angle, it was turning **LEFT** instead of **RIGHT**.

Additionally, you wanted the robot to **always prefer turning right** (clockwise), except when the package is very close to the left (where a small left turn is more efficient).

## The Solution

Applied **two fixes**:

### Fix 1: Sign Inversion Correction
The sensor motor's position convention was inverted relative to the robot's turn convention.

**Before:**
```python
raw_angle = angle - self.gyro_sensor.get_orientation()
```

**After:**
```python
raw_angle = -(angle - self.gyro_sensor.get_orientation())  # Negated!
```

This ensures:
- Positive `raw_angle` → Turn RIGHT
- Negative `raw_angle` → Turn LEFT

### Fix 2: Prefer Right Turns
For packages far to the left, instead of turning left 270°, the robot now turns right 90° (the "long way").

**Logic:**
```python
LEFT_TURN_THRESHOLD = 45  # degrees

if raw_angle < 0 and raw_angle >= -LEFT_TURN_THRESHOLD:
    # Small left turn (0° to -45°) - turn left
    new_angle = raw_angle
elif raw_angle < 0:
    # Large left turn (<-45°) - turn right instead
    new_angle = 360 + raw_angle  # Convert to right turn
else:
    # Positive angle - turn right normally
    new_angle = raw_angle
```

## Turn Behavior Examples

| Package Location | Raw Angle | Action | Actual Turn |
|-----------------|-----------|--------|-------------|
| Directly right | +90° | Turn right | +90° (right) |
| Behind right | +135° | Turn right | +135° (right) |
| Directly behind | +180° | Turn right | +180° (right) |
| Behind left | -135° | Turn right (long way) | +225° (right) |
| Directly left | -90° | Turn right (long way) | +270° (right) |
| Close left | -30° | Turn left (efficient) | -30° (left) |
| Slight left | -10° | Turn left (efficient) | -10° (left) |

## Threshold Configuration

The `LEFT_TURN_THRESHOLD = 45` determines when to allow left turns:

- **Smaller threshold (e.g., 30°)** → Fewer left turns, more right turns
- **Larger threshold (e.g., 60°)** → More left turns, fewer right turns

**Current setting: 45°** means:
- Package within **45° to the left** → Small left turn
- Package **more than 45° to the left** → Right turn (long way)

### Adjust if needed:
```python
# In robot.py, line ~619
LEFT_TURN_THRESHOLD = 45  # Change this value
```

**Examples:**
- `LEFT_TURN_THRESHOLD = 0` → NEVER turn left (always right)
- `LEFT_TURN_THRESHOLD = 90` → Allow left turns up to 90° (directly left)
- `LEFT_TURN_THRESHOLD = 180` → Allow all left turns (disables prefer-right behavior)

## Debug Output

When the robot detects a package, you'll see:

```
STOPPING ARM
ARM POSITION <motor_position>
CALCULATED ANGLE: <angle>
  (motor_pos=<value> + 90 = <angle>)
  → Sticker detected on RIGHT/LEFT side of robot

Package on RIGHT/BEHIND: turning RIGHT 85.0°
  Current orientation=0°, computed raw_angle=85.0° → final turn=85.0°
  (sensor motor position=<pos>, target angle=<angle>)
```

Or for left-side packages:

```
Package on LEFT side (small): turning LEFT -25.0°
  Current orientation=0°, computed raw_angle=-25.0° → final turn=-25.0°
```

Or for far-left packages:

```
Package on LEFT side (far): turning RIGHT 270.0° (long way)
  Current orientation=0°, computed raw_angle=-90.0° → final turn=270.0°
```

## What Changed in Code

**File:** `robot.py`, lines ~612-637 (in `handle_non_meeting_room()`)

1. **Added negation** to fix sign convention
2. **Added threshold-based logic** to prefer right turns
3. **Enhanced debug output** to show decision-making

## Testing the Fix

1. **Run the robot** and observe the package delivery behavior
2. **Check debug output** to verify:
   - Is the raw angle sign correct?
   - Does it choose the right direction?
   - Does the robot turn the expected way?
3. **Adjust threshold** if needed based on your preferences

## Expected Behavior Now

✅ Positive angles → Robot turns **RIGHT**  
✅ Negative angles (small) → Robot turns **LEFT** (efficient)  
✅ Negative angles (large) → Robot turns **RIGHT** (long way, consistent)  
✅ More predictable and consistent turning behavior  
✅ Faster package delivery (prefers efficient direction)  

---

## Quick Reference

**Variables:**
- `motor_pos` = Color sensor motor position when package detected
- `angle` = `motor_pos + 90` (target angle in robot frame)
- `raw_angle` = `-(angle - current_orientation)` (turn needed, sign-corrected)
- `new_angle` = Final turn angle after applying prefer-right logic

**Turn Convention:**
- `+angle` = Turn RIGHT (clockwise)
- `-angle` = Turn LEFT (counter-clockwise)

