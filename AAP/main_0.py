"""
-- AAP by Barth with SO-100 arm by LEROBOT --
last update 05/05/2025

move to 0 position.
this is the rest position
"""
from feurt_driver import FEURTDriver
from config import MOTOR_LIMITS
import time

driver = FEURTDriver()

print("[INFO] move motors in 0 position")
print("------------------------------------------------------------------")

# order of motors
motor_order = [2, 4, 1, 6, 5, 3]
step = 50
delay = 0.05

for motor_id in motor_order:
    limits = MOTOR_LIMITS[motor_id]
    min_pos = limits["min"]
    max_pos = limits["max"]
    center = limits["center"]
    modulo = limits["modulo"]

    # choice of position depending on the engine
    if motor_id == 1:
        target = center
    elif motor_id == 2:
        target = min_pos
    elif motor_id == 3:
        travel = (max_pos - min_pos) % modulo
        target = (min_pos +120 + (3 * travel) // 4) % modulo
    elif motor_id == 4:
        target = max_pos
    elif motor_id == 5:
        travel = (max_pos - min_pos) % modulo
        target = (min_pos + travel // 4) % modulo  
    elif motor_id == 6:
        target = center

    print("=" * 60)
    print(f"[INFO] Motor {motor_id} => go to {target}")

    try:
        current = driver.read_position(motor_id)
    except RuntimeError:
        print(f"[WARNING] Impossible to read {motor_id} => skip")
        continue

    print(f"[INFO] Current position of {motor_id} : {current}")

    if current < target:
        step_value = abs(step)
    else:
        step_value = -abs(step)

    pos = current
    while True:
        pos += step_value

        if (step_value > 0 and pos >= target) or (step_value < 0 and pos <= target):
            break

        if not (min_pos <= pos <= max_pos):
            print(f"[WARNING] Position {pos} engine out of limits {motor_id} => stop")
            break

        driver.move_motor(motor_id, pos)
        time.sleep(delay)

    driver.move_motor(motor_id, target)
    time.sleep(0.1)

print("[INFO] All motors are in 0 position")
print("------------------------------------------------------------------")