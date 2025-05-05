"""
-- AAP by Barth with SO-100 arm by LEROBOT --
last update 05/05/2025
program to relax all motors from terminal
"""
from feurt_driver import FEURTDriver

driver = FEURTDriver()

motor_ids = [1, 2, 3, 4, 5, 6]  # motor id

print("[INFO] RELAX ALL : All enines will be released")

for motor_id in motor_ids:
    driver.set_torque(motor_id, False)
    print(f"[INFO] Motor {motor_id} released")

driver.reconnect()# reconnect driver to get position data

print("[INFO] All  engines are released")