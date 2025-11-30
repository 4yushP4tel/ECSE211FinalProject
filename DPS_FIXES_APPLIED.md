# DPS Issues Fixed

## Problem 1: DPS Values Not Taking Effect

### Issue
You set `FORWARD_MOVEMENT_DPS_RIGHT = 400` and `FORWARD_MOVEMENT_DPS_LEFT = 300`, but both wheels seemed to be moving at the same speed as when both were 300.

### Root Causes Found & Fixed

#### ✅ Fix 1: Removed Redundant `set_power()` Calls
**Problem:** After realignment, the code was calling:
```python
self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT)  # = 0!
self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT)  # = 0!
```

Since you set these power constants to 0, this was **stopping the motors** right after calling `move_straight_dps()`!

**Fixed:** Removed these lines from:
- Main loop realignment (line ~146)
- Room exit realignment (line ~559)

#### ✅ Fix 2: Changed `stop_spinning()` to Use DPS
**Problem:** The `stop_spinning()` method was using `set_power(0)`, which according to motor documentation:
- "SOLIDLY STOPS the motor"
- "IT RESETS any limits defined by 'Motor.set_limits(power, dps)'"

This was interfering with DPS control by resetting the limits every time the robot stopped.

**Fixed:** Changed from:
```python
def stop_spinning(self):
    self.motor.set_power(0)
```

To:
```python
def stop_spinning(self):
    self.motor.set_dps(0)  # Stop using DPS (cleaner for DPS-controlled motors)
```

### Why This Matters

**`set_power(0)` behavior:**
- Resets DPS limits
- Switches motor back to power-based control
- Next `set_dps()` call has to re-establish control

**`set_dps(0)` behavior:**
- Maintains DPS control mode
- Just sets target speed to 0
- Next `set_dps()` call is instantaneous
- Smoother transitions

---

## Problem 2: Backing Up Needs More Frequent Realignment

### Issue
When backing out of rooms, movement is less consistent and needs more frequent realignment checks.

### Solution Applied

#### ✅ Added Dynamic Cooldown Control

**New method in GyroSensor:**
```python
def set_readjust_cooldown(self, cooldown_seconds):
    """Temporarily change the realignment cooldown period"""
    self.readjust_cooldown = cooldown_seconds
```

**Applied in room exit functions:**

1. **`handle_meeting_room()`:**
   - Sets cooldown to **0.5s** before backing up
   - Restores to **2.0s** after exiting

2. **`return_to_hallway_after_delivery()`:**
   - Sets cooldown to **0.5s** before backing up
   - Restores to **2.0s** after exiting

### Behavior Comparison

| Situation | Old Cooldown | New Cooldown | Realignment Frequency |
|-----------|--------------|--------------|----------------------|
| Forward in hallway | 2.0s | 2.0s | Same (every 2s) |
| Forward in room | 2.0s | 2.0s | Same (every 2s) |
| **Backing out of room** | 2.0s | **0.5s** | **4x more frequent!** |

---

## Testing the Fixes

### Test 1: Verify DPS Difference

Run the robot and observe:
1. **With LEFT=300, RIGHT=400:** Robot should veer left (right motor faster)
2. **With LEFT=400, RIGHT=300:** Robot should veer right (left motor faster)

If veering is now visible, the DPS control is working! 🎉

### Test 2: Tune DPS Values

Once DPS is working, adjust to make robot go straight:

**If robot veers LEFT:**
- Right motor is too fast
- Lower `FORWARD_MOVEMENT_DPS_RIGHT`
- Or raise `FORWARD_MOVEMENT_DPS_LEFT`

**If robot veers RIGHT:**
- Left motor is too fast
- Lower `FORWARD_MOVEMENT_DPS_LEFT`
- Or raise `FORWARD_MOVEMENT_DPS_RIGHT`

**Example tuning:**
```python
# Robot veers left with 300/400
FORWARD_MOVEMENT_DPS_LEFT = 300
FORWARD_MOVEMENT_DPS_RIGHT = 295  # Reduced by 5

# Test, adjust, repeat until straight
```

### Test 3: Verify Backward Realignment

When robot backs out of room:
- Watch for realignment corrections
- Should happen up to every 0.5s (instead of 2.0s)
- Robot should maintain straighter path when backing up

---

## Summary of Changes

### Files Modified

1. **`components/wheel.py`:**
   - ✅ Changed `stop_spinning()` to use `set_dps(0)` instead of `set_power(0)`

2. **`components/gyro_sensor.py`:**
   - ✅ Added `set_readjust_cooldown()` method for dynamic cooldown control

3. **`robot.py`:**
   - ✅ Removed redundant `set_power()` calls after realignment (2 locations)
   - ✅ Added cooldown reduction (0.5s) when backing out of rooms
   - ✅ Added cooldown restoration (2.0s) after exiting rooms

---

## Expected Behavior Now

✅ **DPS control should work properly**
- Different DPS values will cause visible speed differences
- No more interference from `set_power()` calls
- Smoother stop/start transitions

✅ **Backward movement more stable**
- Realignment checks every 0.5s instead of 2.0s
- Robot corrects drift 4x more frequently
- Straighter path when backing out

✅ **Forward movement unchanged**
- Still checks every 2.0s (prevents wobbling)
- Maintains smooth forward navigation

---

## Current DPS Settings

```python
# In robot.py
FORWARD_MOVEMENT_DPS_LEFT = 300
FORWARD_MOVEMENT_DPS_RIGHT = 400  # You have this set higher

# For turning
TURN_DPS_LEFT = 200
TURN_DPS_RIGHT = 200
```

**Note:** With RIGHT=400 and LEFT=300, robot will likely veer **left** (right wheel faster). Adjust as needed based on testing!

---

## Troubleshooting

### If DPS still doesn't seem to work:

1. **Check battery level:** Low battery affects motor control
2. **Check motor connections:** Ensure motors are properly connected
3. **Add debug output:** Print actual motor speeds:
   ```python
   print(f"Left motor: {self.left_wheel.motor.get_speed()} dps")
   print(f"Right motor: {self.right_wheel.motor.get_speed()} dps")
   ```
4. **Verify DPS limits:** Ensure not hitting motor max (~1250 dps)

### If backing up still inconsistent:

1. **Reduce cooldown further:** Try 0.3s or 0.2s
2. **Check surface:** Backing up on uneven surface affects stability
3. **Verify realignment triggers:** Check debug output for "readjustment needed"

