"""
-- AAP by Barth with SO-100 arm by LEROBOT --
last update 05/05/2025
program to record a movement and play it back later
             
"""
from feurt_driver import FEURTDriver
from config import MOTOR_LIMITS
#from core.fonctions import relax_all
from pynput import keyboard
from scipy.interpolate import UnivariateSpline
import pandas as pd
import numpy as np
import sys
import subprocess
import csv
import time
import os

DATA_FOLDER = "data"
driver = FEURTDriver()  


def relax():
    motor_ids = [1, 2, 3, 4, 5, 6]  # motor id

    print("[INFO] RELAX ALL : All enines will be released")

    for motor_id in motor_ids:
        driver.set_torque(motor_id, False)
        print(f"[INFO] Motor {motor_id} released")

    driver.reconnect()# reconnect driver to get position data

    print("[INFO] All  engines are released")

def traiter_csv(filepath, target_frequency=200, seuil_exces=50, smoothing=1):
    """
    processes a CSV file :
    - removes outliers
    - applies smooth interpolation
    - re-sampling
    - rebuilds timetamps
    - rewritten file
    """
    df = pd.read_csv(filepath)
    if "time" not in df.columns:
        raise ValueError("no time column detected.")

    motor_cols = [col for col in df.columns if col.startswith("motor_")]

    # removes outliers
    for col in motor_cols:
        diffs = np.abs(np.diff(df[col]))
        indices = np.where(diffs > seuil_exces)[0] + 1
        df.loc[indices, col] = np.nan
        df[col] = df[col].interpolate().bfill().ffill()

    # applies smooth interpolation
    df_interp = pd.DataFrame()
    df_interp["time"] = df["time"]
    for col in motor_cols:
        spline = UnivariateSpline(df["time"], df[col], s=smoothing)
        df_interp[col] = spline(df["time"])

    # re-sampling
    duration = df["time"].iloc[-1]  # original actual duration
    n_frames = int(duration * target_frequency)
    dt = 1.0 / target_frequency
    new_times = np.arange(n_frames) * dt  # uniform time

    df_final = pd.DataFrame()
    df_final["time"] = new_times
    for col in motor_cols:
        spline = UnivariateSpline(df["time"], df[col], s=0)
        df_final[col] = spline(new_times)

    # final rewritten
    df_final.to_csv(filepath, index=False)
    print(f"[INFO] rewritten : {filepath}")

def acquisition(driver, frequency=10.0, output_file="acquisition.csv"):
    """
    records engines data between two 'space' press.
    """
    print("[INFO] Press space to start recording...")
    started = False
    stopped = False

    def on_press(key):
        nonlocal started, stopped
        if key == keyboard.Key.space:
            if not started:
                print("[INFO] : Start of recording !")
                started = True
            elif started and not stopped:
                print("[INFO] : End of recording !")
                stopped = True
                return False

    # waiting for first press
    with keyboard.Listener(on_press=on_press) as listener:
        while not started:
            time.sleep(0.1)

    interval = 1.0 / frequency
    start_time = time.time()
    rows = []

    with keyboard.Listener(on_press=on_press) as listener:
        while not stopped:
            now = time.time()
            elapsed = now - start_time

            row = {"time": round(elapsed, 4)}
            for motor_id in MOTOR_LIMITS:
                try:
                    pos = driver.read_position(motor_id)
                    row[f"motor_{motor_id}"] = pos
                except RuntimeError:
                    row[f"motor_{motor_id}"] = None

            rows.append(row)
            time.sleep(interval)

    # Save
    os.makedirs("data", exist_ok=True)
    filepath = os.path.join("data", output_file)

    with open(filepath, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"[INFO] : Recorded movment: {filepath}")

def execution(driver, filepath):
    """
    Replay movment with csv file (time + motor position).
    """
    print(f"[INFO] : Reading movment's file : {filepath}")

    with open(filepath, mode="r") as f:
        reader = csv.DictReader(f)
        sequence = [row for row in reader]

    if not sequence:
        print("[ERROR] No data find.")
        return

    print(f"[INFO] {len(sequence)} steps loaded. Start movment...")

    start_time = time.time()

    for i, row in enumerate(sequence):
        target_time = float(row["time"])
        now = time.time()
        delay = target_time - (now - start_time)
        if delay > 0:
            time.sleep(delay)

        for key, value in row.items():
            if key.startswith("motor_") and value:
                motor_id = int(key.split("_")[1])
                driver.move_motor(motor_id, int(float(value)))

    print("[INFO] Movment completed.")

def list_recordings():
    """
    print list of files
    """
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    print("\n[INFO] : Recording available :")
    for f in files:
        print(f"  - {f}")
    return files

def main():
    """
    main function
    """

    while True:
        print("\n=== MAIN MENUE ===")
        print("1. Acquisition of a movement")
        print("2. Execution of a movement")
        print("3. Stop")

        choice = input("Choice : ").strip()

        if choice == "1":

            # 2. Relax with relax_all
            relax()
            

            # Acquisition
            while True:
                try:
                    hz = float(input("At what frequency (Hz) ?").strip())
                    break
                except ValueError:
                    print("[ERROR] : Enter valid number")

            # temp acquisition 
            temp_file = "temp_acquisition.csv"
            acquisition(driver, frequency=hz, output_file=temp_file)

            satis = input("Are you satisfeid ? (y/n) ").strip().lower()
            if satis != "y":
                print("[INFO] Restart")
                continue

            name = input("Name of movement :").strip()
            final_path = os.path.join(DATA_FOLDER, name + ".csv")
            os.rename(os.path.join(DATA_FOLDER, temp_file), final_path)
            #traiter_csv(final_path, target_frequency=hz, seuil_exces=50, smoothing=1)
            print(f"[INFO] Movmement saved as : {final_path}")

        elif choice == "2":
            # Exécution


            files = list_recordings()
            if not files:
                print("[INFO] No files found")
                continue

            name = input("Name of the movement to executed").strip()
            filepath = os.path.join(DATA_FOLDER, name)
            if not filepath.endswith(".csv"):
                filepath += ".csv"

            if not os.path.exists(filepath):
                print("File not found")
                continue

            execution(driver, filepath)

        elif choice == "3":
            print("[INFO]: End")
            break

        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

