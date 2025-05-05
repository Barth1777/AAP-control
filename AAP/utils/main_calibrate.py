"""
-- AAP by Barth with SO-100 arm by LEROBOT --
last update 05/05/2025

program to calibrate all motors from terminal
"""
from feurt_driver import FEURTDriver
import time

driver = FEURTDriver()

motor_ids = [1, 2, 3, 4, 5, 6]

print("[INFO] CALIBRATION MODE")
print("-------------------------------------------------")

def relax():
    motor_ids = [1, 2, 3, 4, 5, 6]  # motor id

    print("[INFO] RELAX ALL : All enines will be released")

    for motor_id in motor_ids:
        driver.set_torque(motor_id, False)
        print(f"[INFO] Motor {motor_id} released")

    driver.reconnect()# reconnect driver to get position data

    print("[INFO] All  engines are released")

# Torque OFF all
relax()
print("[INFO] All motors are released => you can move them freely")
MOTOR_LIMITS = {}

try:
    for motor_id in motor_ids:
        print("\n" + "="*60)
        print(f"[INFO] Engine calibration: {motor_id}")

        print("[INFO] Real-time display of positions => Ctrl+C to capture position")

        try:
            while True:
                pos = driver.read_position(motor_id)
                print(f"\rCurrent motor position : {motor_id} : {pos}", end="")
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n[INFO] Capturing positions")

        input("=> Set the motor to its LEFT END (min) then press Enter")
        pos_min = driver.read_position(motor_id)

        input("=> Set the motor to its RIGHT END (max) then press Enter")
        pos_max = driver.read_position(motor_id)

        input("=> Put the motor in its CENTER POSITION and then press Enter")
        pos_center = driver.read_position(motor_id)

        if pos_min == pos_max or pos_min == pos_center or pos_max == pos_center:
            print("[WARNING] : Two identical positions detected")
            input("=> Check carefully then press Enter to validate")

        MOTOR_LIMITS[motor_id] = {
            "min": pos_min,
            "max": pos_max,
            "center": pos_center
        }

        print(f"[INFO] Motor values {motor_id} recorded : min={pos_min} | max={pos_max} | center={pos_center}")

except KeyboardInterrupt:
    print("\n[INFO] END OF CALIBRATION")

