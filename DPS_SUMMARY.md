# DPS Implementation Summary

## What Was Changed

### 1. ✅ Added Separate DPS Constants for Left/Right Wheels
**File:** `robot.py` (Lines 48-52)

```python
# You can now configure different DPS for each wheel
FORWARD_MOVEMENT_DPS_LEFT = 300   # Adjust independently
FORWARD_MOVEMENT_DPS_RIGHT = 300  # Adjust independently
TURN_DPS_LEFT = 200
TURN_DPS_RIGHT = 200
```

### 2. ✅ Added `spin_wheel_at_dps()` Method
**File:** `components/wheel.py`

New method for closed-loop speed control on individual wheels.

### 3. ✅ Created New DPS-Based Movement Methods
**File:** `robot.py`

#### a. `move_straight_dps(direction)`
- Replaces `move_straight()` with DPS control
- Uses separate `FORWARD_MOVEMENT_DPS_LEFT` and `FORWARD_MOVEMENT_DPS_RIGHT`

#### b. `turn_in_place_dps(direction)`
- Turn in place using DPS
- Direction: 1=right, -1=left

#### c. `turn_to_orientation_dps(target_orientation)`
- DPS version of `turn_to_orientation()`
- Used for realignment (turning to absolute angle like 0°)

#### d. `turn_x_deg_dps(angle, reset_after=True)`
- DPS version of `turn_x_deg()`
- Used for relative turns (e.g., turn 90° from current position)

### 4. ✅ Created Test Script
**File:** `test_dps_vs_power.py`

Compares power-based vs DPS-based movement to measure drift.

### 5. ✅ Created Documentation
- **POWER_VS_DPS_USAGE.md** - Comprehensive explanation of power vs DPS
- **MIGRATION_CHECKLIST.md** - Step-by-step migration guide

---

## Why Different DPS for Left/Right?

Even with closed-loop control, motors may have slight differences:
- Manufacturing tolerances
- Wear differences
- Mechanical friction differences
- Gear train differences

Having separate DPS values lets you fine-tune if the robot still veers slightly.

**In practice:** Start with both at 300, then adjust if needed:
- Robot veers **right** → Lower `FORWARD_MOVEMENT_DPS_RIGHT` or raise `LEFT`
- Robot veers **left** → Lower `FORWARD_MOVEMENT_DPS_LEFT` or raise `RIGHT`

---

## Where Power is Still Used

### Main Places:
1. **All `move_straight()` calls** - Line ~607 definition, used throughout
2. **All `turn_x_deg()` calls** - Lines 274-340, used for corners/rooms
3. **All `turn_to_orientation()` calls** - Lines 228-272, used for realignment
4. **Manual `set_power()` after realignment** - Lines 146-147, 452-453

### Why Power is Still Used:
- Original code uses these methods
- Need to test and calibrate DPS first
- Then gradually migrate to DPS methods
- Power methods kept as backup

---

## Next Steps

### 1. Test DPS vs Power
```bash
cd /home/crestydy/please_work/ECSE211FinalProject
python3 test_dps_vs_power.py
```

### 2. Calibrate DPS Values
Adjust constants in `robot.py` if robot veers:
```python
FORWARD_MOVEMENT_DPS_LEFT = 300   # ← Adjust these
FORWARD_MOVEMENT_DPS_RIGHT = 295  # ← Adjust these
```

### 3. Migrate to DPS Methods
Replace calls one at a time:
```python
# Before
self.move_straight(1)
self.turn_x_deg(90)

# After  
self.move_straight_dps(1)
self.turn_x_deg_dps(90)
```

See **MIGRATION_CHECKLIST.md** for complete step-by-step guide.

---

## Quick Reference

### Movement
```python
# Power-based (old)
robot.move_straight(1)         # Forward
robot.move_straight(-1)        # Backward

# DPS-based (new) ← USE THESE
robot.move_straight_dps(1)     # Forward
robot.move_straight_dps(-1)    # Backward
```

### Turning
```python
# Power-based (old)
robot.turn_x_deg(90)           # 90° right
robot.turn_x_deg(-90)          # 90° left  
robot.turn_to_orientation(0)   # Turn to 0°

# DPS-based (new) ← USE THESE
robot.turn_x_deg_dps(90)       # 90° right
robot.turn_x_deg_dps(-90)      # 90° left
robot.turn_to_orientation_dps(0)  # Turn to 0°
```

---

## Expected Benefits

✅ **Better straight-line precision** - Less veering  
✅ **Consistent speed** - Compensates for battery drain  
✅ **Predictable behavior** - Speed in deg/sec is absolute  
✅ **Easier calibration** - More intuitive than power percentages  
✅ **Better performance** - Adapts to surface/load changes  

---

## Files Modified

- ✅ `components/wheel.py` - Added `spin_wheel_at_dps()`
- ✅ `robot.py` - Added DPS constants and methods
- ✅ `test_dps_vs_power.py` - Test script (NEW)
- ✅ `POWER_VS_DPS_USAGE.md` - Documentation (NEW)
- ✅ `MIGRATION_CHECKLIST.md` - Migration guide (NEW)
- ✅ `DPS_SUMMARY.md` - This file (NEW)

