""""
-- AAP by Barth with SO-100 arm by LEROBOT --
last update 05/05/2025

Manual control of the motors.
Control motor one by one with keyboard.
WARNING : this code is currently not working
          waiting for update
"""
from feurt_driver import FEURTDriver
from config import MOTOR_LIMITS
from pynput import keyboard
import time

driver = FEURTDriver()

print("[INFO] Manuel control of the motors")
print("-------------------------------------------------")
print("Select motor : 1 / 2 / 3 / 4 / 5 / 6")
print("Movement : <= to decrease | => to increase")
print("STOP : espace")
print("-------------------------------------------------")

selected_motor = None
step = 2
delay = 0.03
moving_left = False
moving_right = False
running = True


def on_press(key):
    global selected_motor, running, moving_left, moving_right

    try:
        if hasattr(key, 'char') and key.char in '123456':
            selected_motor = int(key.char)
            print(f"[INFO] Motor selected : {selected_motor}")

            # Lock other motors
            for motor_id in [1, 2, 3, 4, 5, 6]:
                if motor_id != selected_motor:
                    try:
                        pos = driver.read_position(motor_id)
                        driver.set_torque(motor_id, True)
                        driver.move_motor(motor_id, pos)
                    except RuntimeError:
                        print(f"[WARNING] Impossible to communicate with {motor_id} motor")

    except Exception as e:
        print(f"[WARNING] Error : {e}")

    if key == keyboard.Key.left and selected_motor:
        moving_left = True

    if key == keyboard.Key.right and selected_motor:
        moving_right = True

    if key == keyboard.Key.space:
        running = False
        print("[INFO] End of the program")
        return False


def on_release(key):
    global moving_left, moving_right

    if key == keyboard.Key.left:
        moving_left = False
    if key == keyboard.Key.right:
        moving_right = False


listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

while running:
    if selected_motor:
        try:
            current = driver.read_position(selected_motor)
        except RuntimeError:
            time.sleep(0.05)
            continue

        limits = MOTOR_LIMITS[selected_motor]

        if moving_left:
            new_pos = max(limits['min'], current - step)
            driver.move_motor(selected_motor, new_pos)
            time.sleep(delay)

        if moving_right:
            new_pos = min(limits['max'], current + step)
            driver.move_motor(selected_motor, new_pos)
            time.sleep(delay)

    else:
        time.sleep(0.1)

listener.join()