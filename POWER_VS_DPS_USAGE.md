# Power vs DPS Usage in Robot Code

## Overview

This document explains where `set_power` is still being used in `robot.py` and why, plus how to migrate to DPS-based control for better precision.

---

## Current Status

### Places Still Using `set_power`:

1. **`move_straight()`** - Line 607-610
   - **Why:** Legacy method, currently the main movement method
   - **Should migrate to:** `move_straight_dps()`
   
2. **`turn_to_orientation()`** - Lines 249-265
   - **Why:** Used for realignment turns
   - **Should migrate to:** `turn_to_orientation_dps()` (now available)
   
3. **`turn_x_deg()`** - Lines 292-308
   - **Why:** Used for all major turning operations
   - **Should migrate to:** `turn_x_deg_dps()` (now available)

4. **`turn_until_x_orientation()`** - Lines 346-352
   - **Why:** Appears to be legacy/unused code
   - **Should:** Probably deprecate or create DPS version if needed

5. **After realignment in main loop** - Lines 146-147
   - **Why:** Manually setting power after realignment
   - **Should:** Call `move_straight_dps(1)` instead

6. **After realignment in `handle_meeting_room()`** - Lines 452-453
   - **Why:** Manually setting power after realignment
   - **Should:** Call `move_straight_dps(1)` instead

---

## Why DPS is Better Than Power

### `set_power` (Open-Loop Control)
- Just applies a percentage of power (-100 to 100%)
- **No feedback:** Doesn't adjust for variations
- **No compensation** for:
  - Motor manufacturing differences
  - Battery voltage changes
  - Friction differences
  - Load differences
- Requires manual calibration for each motor
- Speed varies with battery level

### `set_dps` (Closed-Loop Control)
- Sets target speed in degrees per second
- **Has feedback:** Continuously measures actual speed
- **Automatically compensates** for:
  - Motor differences
  - Battery voltage
  - Friction
  - Load changes
- Each motor independently maintains its target speed
- More consistent and predictable behavior

---

## Available DPS Methods

### Movement Methods

```python
# Original (power-based)
robot.move_straight(1)  # direction: 1=forward, -1=backward

# New (DPS-based) - RECOMMENDED
robot.move_straight_dps(1)  # direction: 1=forward, -1=backward
```

### Turning Methods

```python
# Original (power-based)
robot.turn_x_deg(90)                    # Turn 90° right
robot.turn_x_deg(-90)                   # Turn 90° left
robot.turn_to_orientation(0)            # Turn to absolute 0°

# New (DPS-based) - RECOMMENDED
robot.turn_x_deg_dps(90)                # Turn 90° right
robot.turn_x_deg_dps(-90)               # Turn 90° left
robot.turn_to_orientation_dps(0)        # Turn to absolute 0°

# In-place turning helper
robot.turn_in_place_dps(1)              # Turn right continuously
robot.turn_in_place_dps(-1)             # Turn left continuously
```

---

## Configuration Constants

### Power-Based (Old)
```python
FORWARD_MOVEMENT_POWER_LEFT = 22.3    # Different for each motor!
FORWARD_MOVEMENT_POWER_RIGHT = 22.5   # Manual calibration needed
POWER_FOR_TURN = 15
```

### DPS-Based (New)
```python
# Start with same values, adjust if robot still veers
FORWARD_MOVEMENT_DPS_LEFT = 300       # Can be different if needed
FORWARD_MOVEMENT_DPS_RIGHT = 300      # But usually same value works!
TURN_DPS_LEFT = 200
TURN_DPS_RIGHT = 200
```

**Key Difference:** With DPS, you can usually use the **same value** for both motors because closed-loop control compensates for hardware differences. Only adjust if the robot still veers after testing.

---

## Migration Strategy

### Step 1: Test Current Behavior
Run the test script to compare power vs DPS:
```bash
cd /home/crestydy/please_work/ECSE211FinalProject
python3 test_dps_vs_power.py
```

### Step 2: Calibrate DPS Values
If robot veers with DPS:
- If veers **right**: Decrease `FORWARD_MOVEMENT_DPS_RIGHT` or increase `FORWARD_MOVEMENT_DPS_LEFT`
- If veers **left**: Increase `FORWARD_MOVEMENT_DPS_RIGHT` or decrease `FORWARD_MOVEMENT_DPS_LEFT`

**Example:**
```python
# Robot veers slightly right with both at 300
FORWARD_MOVEMENT_DPS_LEFT = 300
FORWARD_MOVEMENT_DPS_RIGHT = 295  # Reduced by 5
```

### Step 3: Replace method calls one at a time

#### 3a. Replace forward movement
Find all instances of:
```python
self.move_straight(1)
```
Replace with:
```python
self.move_straight_dps(1)
```

#### 3b. Replace turning
Find all instances of:
```python
self.turn_x_deg(90)
self.turn_to_orientation(0)
```
Replace with:
```python
self.turn_x_deg_dps(90)
self.turn_to_orientation_dps(0)
```

#### 3c. Replace manual power setting after realignment
Find instances like:
```python
self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT)
self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
```
Replace with:
```python
self.move_straight_dps(1)
```

---

## Testing Checklist

After migrating to DPS, test:

- [ ] Straight-line movement in hallway
- [ ] Realignment corrections
- [ ] 90-degree turns at corners
- [ ] Entering rooms (90-degree turns)
- [ ] Exiting rooms (270-degree turns)
- [ ] Movement in rooms (sweeping)
- [ ] Backward movement when exiting
- [ ] Final approach to home

---

## Quick Reference: DPS Values

Typical DPS ranges for LEGO EV3 motors:
- **Maximum speed:** ~1250 dps (full throttle)
- **Slow precise movement:** 50-150 dps
- **Normal movement:** 200-400 dps
- **Fast movement:** 500-800 dps

For this robot:
- **Forward movement:** 300 dps ≈ 22-23% power
- **Turning:** 200 dps ≈ 15% power

---

## Benefits You Should See

After switching to DPS:

1. ✅ **More consistent straight-line movement** - less veering
2. ✅ **Better performance** as battery drains (power compensates)
3. ✅ **Simpler calibration** - usually same DPS for both motors
4. ✅ **More predictable behavior** across different surfaces
5. ✅ **Easier to tune** - speed in deg/sec is more intuitive than power %

---

## Common Issues & Solutions

### Issue: Robot still veers with DPS
**Solution:** Adjust DPS values for each motor independently:
```python
FORWARD_MOVEMENT_DPS_LEFT = 300
FORWARD_MOVEMENT_DPS_RIGHT = 295  # Adjust in increments of 5
```

### Issue: Robot turns too fast/slow
**Solution:** Adjust turn DPS values:
```python
TURN_DPS_LEFT = 180   # Slower turns
TURN_DPS_RIGHT = 180
```

### Issue: Robot doesn't maintain speed uphill
**Solution:** This is where DPS shines! It automatically increases power to maintain speed. If it's not working, check:
- Battery level (must be >7V)
- DPS value isn't exceeding motor capability (~1250 max)

---

## Next Steps

1. **Run test script** to see power vs DPS comparison
2. **Calibrate DPS values** if needed
3. **Gradually migrate** one movement type at a time
4. **Test thoroughly** after each change
5. **Keep power methods** as backup until fully tested

