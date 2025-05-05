"""
-- AAP by Barth with SO-100 arm by LEROBOT --
last update 05/05/2025
basic functions allowing simplified use
list of functions :
                    - read_position
                    - move_motor_virtual
                    - relax_all
                    - lock_all
                    - center_all
                    - convert_position
                    - go_to
"""
from feurt_driver import FEURTDriver
from config import MOTOR_LIMITS
import time
from time import sleep



def read_position(driver: FEURTDriver, motor_id: int) -> int:
    """
    call read_position from driver and return current position
    """
    return driver.read_position(motor_id)

def move_motor_virtual(driver: FEURTDriver, motor_id: int, virtual_pos: int, virtual_max=4000):
    """
    move motor with the specific physical constraints of the arme. 
    Includes min, max, center and modulo of each motor.
    """
    limits = MOTOR_LIMITS[motor_id]
    real_min = limits["min"]
    real_max = limits["max"]
    modulo = limits["modulo"]
    travel = (real_max - real_min) % modulo
    real_pos = (real_min + (virtual_pos / virtual_max) * travel) % modulo
    driver.move_motor(motor_id, int(real_pos))

def relax_all(driver: FEURTDriver):
    """
    relax all motors and reconnect driver
    """
    for motor_id in MOTOR_LIMITS.keys():
        driver.set_torque(motor_id, False)
        print(f"[INFO] RELAX ALL : Engine {motor_id} released")
    print("[INFO] RELAX ALL : All engines released")
    driver.reconnect()
    
def lock_all(driver: FEURTDriver):
    """
    lock all motors and reconnect driver
    
    """
    for motor_id in MOTOR_LIMITS.keys():
        driver.set_torque(motor_id, True)
        print(f"[INFO] LOCK ALL : Engine {motor_id} locked")
    print("[INFO] LOCK ALL : All engines locked")
    driver.reconnect()

def center_all(self, step=50, delay=0.05):
        """
        centering of all motors
        """
        print("[INFO] Centering of all engines")

        for motor_id, limits in MOTOR_LIMITS.items():
            center = limits["center"]
            min_pos = limits["min"]
            max_pos = limits["max"]

            print("="*60)
            print(f"[INFO] Motor {motor_id} : center={center} | min={min_pos} | max={max_pos}")

            current = self.read_position(motor_id)
            print(f"[INFO] Current position: {current}")

            # Determine the direction of movement with max/min
            if current < center:
                step_value = abs(step)
            else:
                step_value = -abs(step)

            pos = current
            while True:
                pos += step_value

                if (step_value > 0 and pos >= center) or (step_value < 0 and pos <= center):
                    break

                if not (min_pos <= pos <= max_pos):
                    print(f"[WARNING] Position {pos} engine out of limit {motor_id}. stop")
                    break

                self.move_motor(motor_id, pos)
                time.sleep(delay)

            self.move_motor(motor_id, center)
            time.sleep(0.1)

        print("[INFO] Centering completed.")

def convert_position(motor_id, angle):
    """
    Convert an angle (-180° à 180°) on motor position
    Respect real range around min/max.
    """
    limits = MOTOR_LIMITS[motor_id]
    center = limits["center"]
    min_pos = limits["min"]
    max_pos = limits["max"]
    modulo = limits["modulo"]

    # Distance center to max (positiv)
    travel_pos = (max_pos - center) % modulo
    # Distance center to  min (negative)
    travel_neg = (center - min_pos) % modulo

    if angle >= 0:
        # travel between center and max
        target = center + (angle / 180) * travel_pos
    else:
        # Travel between center and min
        target = center + (angle / 180) * travel_neg

    # modulo
    target = target % modulo

    # Clamp final : respect min / max
    if target < min_pos:
        target = min_pos
    if target > max_pos:
        target = max_pos

    return int(target)

def go_to(driver, motor_id, angle, speed=50, delay=0.03):

    """
    moves a motor to the given angle within the limits
    and using a given speed
    """
    target = convert_position(motor_id, angle)
    current = driver.read_position(motor_id)

    print(f"[INFO] Motor {motor_id} :go to {angle} motor position{target}")

    if current < target:
        step = abs(speed)
    else:
        step = -abs(speed)

    pos = current
    while True:
        pos += step

        if (step > 0 and pos >= target) or (step < 0 and pos <= target):
            break

        limits = MOTOR_LIMITS[motor_id]
        if not (limits['min'] <= pos <= limits['max']):
            print(f"[WARNING] Engine limits exceeded {motor_id} : stop")
            break

        driver.move_motor(motor_id, pos)
        time.sleep(delay)

    driver.move_motor(motor_id, target)
    time.sleep(0.1)


