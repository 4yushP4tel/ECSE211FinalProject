# DPS Migration Checklist

## Summary: Where Power is Still Used

### 🔴 HIGH PRIORITY - Main Movement Methods

| Location | Current Code | Replacement | Status |
|----------|-------------|-------------|---------|
| **Line 144** | `move_straight(1)` in main loop after realignment | `move_straight_dps(1)` | ⚠️ TODO |
| **Line 146-147** | Manual `set_power()` after realignment | Remove (use method) | ⚠️ TODO |
| **Line 187** | `turn_x_deg(90)` for corner turns | `turn_x_deg_dps(90)` | ⚠️ TODO |
| **Line 201** | `turn_x_deg(90)` for room entry | `turn_x_deg_dps(90)` | ⚠️ TODO |
| **Line 224** | `turn_to_orientation(0)` in realign | `turn_to_orientation_dps(0)` | ⚠️ TODO |

### 🟡 MEDIUM PRIORITY - Room Handling

| Location | Current Code | Replacement | Status |
|----------|-------------|-------------|---------|
| **Line 419** | `turn_x_deg(270)` exit meeting room | `turn_x_deg_dps(270)` | ⚠️ TODO |
| **Line 452-453** | Manual `set_power()` after realignment | `move_straight_dps(1)` | ⚠️ TODO |
| **Line 498** | `turn_x_deg()` in non-meeting room | `turn_x_deg_dps()` | ⚠️ TODO |
| **Line 502** | `turn_x_deg()` return from package | `turn_x_deg_dps()` | ⚠️ TODO |
| **Line 642** | `turn_x_deg(270)` exit room | `turn_x_deg_dps(270)` | ⚠️ TODO |

### 🟢 LOW PRIORITY - Supporting Methods

| Location | Method | Replacement Available | Status |
|----------|--------|----------------------|---------|
| **Lines 228-272** | `turn_to_orientation()` | `turn_to_orientation_dps()` | ✅ Created |
| **Lines 274-340** | `turn_x_deg()` | `turn_x_deg_dps()` | ✅ Created |
| **Lines 342-357** | `turn_until_x_orientation()` | Not needed | ⏸️ Legacy |

---

## Step-by-Step Migration Plan

### Phase 1: Test and Calibrate ✅ READY
```bash
cd /home/crestydy/please_work/ECSE211FinalProject
python3 test_dps_vs_power.py
```
**Goal:** Find optimal DPS values for your robot

---

### Phase 2: Update Constants (in `robot.py`)
```python
class Robot:
    # DPS values - adjust based on test results
    FORWARD_MOVEMENT_DPS_LEFT = 300   # Adjust if robot veers
    FORWARD_MOVEMENT_DPS_RIGHT = 300  # Adjust if robot veers
    TURN_DPS_LEFT = 200
    TURN_DPS_RIGHT = 200
```

---

### Phase 3: Replace Forward Movement

#### 3.1. Main Loop (Line 144)
**Before:**
```python
self.move_straight(1)
```
**After:**
```python
self.move_straight_dps(1)
```

#### 3.2. Main Loop After Realignment (Lines 139-141)
**Before:**
```python
self.realign_to_zero()
self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT)
self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
self.move_straight(1)
```
**After:**
```python
self.realign_to_zero()
self.move_straight_dps(1)
```

#### 3.3. All Other `move_straight()` Calls
**Find and replace:** Throughout the file
- `self.move_straight(1)` → `self.move_straight_dps(1)`
- `self.move_straight(-1)` → `self.move_straight_dps(-1)`

---

### Phase 4: Replace Realignment

#### 4.1. Realign Method (Line 224)
**Before:**
```python
def realign_to_zero(self):
    # ...
    self.turn_to_orientation(0)
```
**After:**
```python
def realign_to_zero(self):
    # ...
    self.turn_to_orientation_dps(0)
```

---

### Phase 5: Replace All Turning

#### 5.1. Corner Turns (Line 187)
**Before:**
```python
self.turn_x_deg(90 - self.gyro_sensor.get_orientation())
```
**After:**
```python
self.turn_x_deg_dps(90 - self.gyro_sensor.get_orientation())
```

#### 5.2. Room Entry (Line 201)
**Before:**
```python
self.turn_x_deg(90 - self.gyro_sensor.get_orientation())
```
**After:**
```python
self.turn_x_deg_dps(90 - self.gyro_sensor.get_orientation())
```

#### 5.3. Home Entry (Line 165)
**Before:**
```python
self.turn_x_deg(90 - self.gyro_sensor.get_orientation())
```
**After:**
```python
self.turn_x_deg_dps(90 - self.gyro_sensor.get_orientation())
```

#### 5.4. Exit Room Turns (Lines 419, 642)
**Before:**
```python
self.turn_x_deg(270 - self.gyro_sensor.get_orientation())
```
**After:**
```python
self.turn_x_deg_dps(270 - self.gyro_sensor.get_orientation())
```

#### 5.5. Package Delivery Turns (Lines 498, 502)
**Before:**
```python
self.turn_x_deg(new_angle, reset_after=False)
self.turn_x_deg(-new_angle, reset_after=False)
```
**After:**
```python
self.turn_x_deg_dps(new_angle, reset_after=False)
self.turn_x_deg_dps(-new_angle, reset_after=False)
```

#### 5.6. Fine-tuning Turns (Lines 172, 426, 649)
**Before:**
```python
if abs(current_orientation) > 1:
    self.turn_x_deg(-current_orientation)
```
**After:**
```python
if abs(current_orientation) > 1:
    self.turn_x_deg_dps(-current_orientation)
```

---

### Phase 6: Handle Meeting Room Cleanup (Lines 447-454)
**Before:**
```python
if self.gyro_sensor.readjust_robot_flag.is_set():
    self.stop_moving()
    self.realign_to_zero()
    self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT)
    self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
    self.move_straight(1)
```
**After:**
```python
if self.gyro_sensor.readjust_robot_flag.is_set():
    self.stop_moving()
    self.realign_to_zero()
    self.move_straight_dps(1)
```

---

## Testing After Each Phase

After completing each phase, test:

### Phase 3 Testing (Forward Movement)
- [ ] Robot moves straight in hallway
- [ ] No excessive veering
- [ ] Consistent speed

### Phase 4 Testing (Realignment)
- [ ] Realignment corrections work
- [ ] Robot returns to 0° orientation
- [ ] Smooth transition back to forward movement

### Phase 5 Testing (Turning)
- [ ] 90° right turns at corners
- [ ] 90° right turns into rooms
- [ ] 270° left turns exiting rooms
- [ ] Package delivery turns
- [ ] Fine-tuning adjustments

### Full System Testing
- [ ] Complete circuit run
- [ ] Both packages delivered
- [ ] Returns home successfully
- [ ] Smooth transitions throughout

---

## Rollback Plan

If DPS causes issues, you can quickly revert:

1. **Keep backup:** Don't delete power-based methods immediately
2. **Gradual switch:** Test each phase before moving to next
3. **Quick revert:** Just change method calls back:
   - `move_straight_dps()` → `move_straight()`
   - `turn_x_deg_dps()` → `turn_x_deg()`
   - `turn_to_orientation_dps()` → `turn_to_orientation()`

---

## Expected Improvements

After full migration to DPS:

✅ **Straighter lines** - Robot maintains path better  
✅ **Consistent speed** - Even as battery drains  
✅ **Fewer realignments** - Better initial tracking  
✅ **Predictable turns** - Same angle every time  
✅ **Simpler tuning** - DPS values more intuitive  

---

## Quick Find & Replace Commands

For bulk replacement (use with caution - test each change!):

```python
# Forward movement
self.move_straight(1)  →  self.move_straight_dps(1)
self.move_straight(-1)  →  self.move_straight_dps(-1)

# Turning
self.turn_x_deg(  →  self.turn_x_deg_dps(
self.turn_to_orientation(  →  self.turn_to_orientation_dps(

# Manual power setting (remove these)
self.left_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_LEFT)
self.right_wheel.motor.set_power(Robot.FORWARD_MOVEMENT_POWER_RIGHT)
# Replace both lines with: self.move_straight_dps(1)
```

---

## Current Status

- [x] DPS methods created
- [x] Test script ready
- [ ] DPS values calibrated
- [ ] Phase 3 complete
- [ ] Phase 4 complete
- [ ] Phase 5 complete
- [ ] Phase 6 complete
- [ ] Full system tested

