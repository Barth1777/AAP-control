"""
-- AAP by Barth with SO-100 arm by LEROBOT --
last update 09/05/2025
program to record a movement and play it back later
             
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feurt_driver import FEURTDriver
from config import MOTOR_LIMITS
from AAP.core.functions import relax_all, position_0
from pynput import keyboard
from scipy.interpolate import interp1d
import pandas as pd
import numpy as np
import csv
import time


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DATA_FOLDER = "data"
driver = FEURTDriver(command_delay=0)  

def traitement_csv(filepath, frequency):
    """
    Processes a CSV file containing 'time' and 'motor_X':
    - Smooth cubic interpolation
    - Resampling at a fixed frequency without changing the total duration
    - Rounding motor positions to the nearest unit
    - Saves and overwrites the data
    """

    # load CSV
    df = pd.read_csv(filepath)
    if "time" not in df.columns:
        raise ValueError("File must contain a time column.")

    motor_cols = [col for col in df.columns if col.startswith("motor_")]

    duration = df["time"].iloc[-1] - df["time"].iloc[0]
    n_frames = int(duration * frequency)
    dt = 1.0 / frequency
    new_times = np.linspace(0, duration, n_frames, endpoint=False)
    new_times = np.round(new_times, 3)

    df_interp = pd.DataFrame()
    df_interp["time"] = new_times

    # cubic interpolation
    for col in motor_cols:
        interp_func = interp1d(df["time"], df[col], kind="cubic", fill_value="extrapolate")
        interpolated = interp_func(new_times)
        df_interp[col] = np.round(interpolated).astype(int)

    # Save
    df_interp.to_csv(filepath, index=False)
    print(f"[INFO] : Fichier traité sauvegardé : {filepath}")
    return filepath

def acquisition(driver, output_file="acquisition.csv"):
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

    interval = 1.0 / 10 # limit motor : 10 Hz
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
    Replay a motor movement from a CSV file containing 'time' and 'motor_X' columns.
    """

    print(f"[INFO] : Reading movement file: {filepath}")

    # Load CSV content into memory
    with open(filepath, mode="r") as f:
        reader = csv.DictReader(f)
        sequence = [row for row in reader]

    if not sequence:
        print("[ERROR] No data found in the file.")
        return

    print(f"[INFO] {len(sequence)} steps loaded. Starting movement...")

    # Estimate the sampling interval
    t0 = float(sequence[0]["time"])
    t1 = float(sequence[1]["time"])
    dt = t1 - t0                       

    start_time = time.perf_counter()

    for i, row in enumerate(sequence):
       
        t_target = start_time + i * dt

        while time.perf_counter() < t_target:
            time.sleep(0.0002) 

        # Send motor positions 
        for key, value in row.items():
            if key.startswith("motor_") and value:
                motor_id = int(key.split("_")[1])
                position = int(float(value))
                driver.move_motor(motor_id, position)

    print("[INFO] Movement completed.")

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

            # preparation for acquisition
            position_0(driver)
            relax_all(driver)
            
            # Get frequency 
            while True:
                try:
                    hz = int(input("Restitution frequency (Hz) : "))
                    if hz <= 0 or hz > 800:
                        raise ValueError
                    break
                except ValueError:
                    print("Invalid input. Please enter a positive integer between 1 and 800.")

            # temp acquisition 
            temp_file = "temp_acquisition.csv"
            acquisition(driver, output_file=temp_file)

            satis = input("Are you satisfeid ? (y/n) ").strip().lower()
            if satis != "y":
                print("[INFO] Restart")
                continue

            name = input("Name of movement : ").strip()
            final_path = os.path.join(DATA_FOLDER, name + ".csv")
            os.rename(os.path.join(DATA_FOLDER, temp_file), final_path)
            traitement_csv(final_path, frequency=hz)
            print(f"[INFO] Movmement saved as : {final_path}")

        elif choice == "2":
            # Execution


            files = list_recordings()
            if not files:
                print("[INFO] No files found")
                continue

            name = input("Name of the movement to executed ").strip()
            filepath = os.path.join(DATA_FOLDER, name)
            if not filepath.endswith(".csv"):
                filepath += ".csv"

            if not os.path.exists(filepath):
                print("File not found")
                continue
            
            # preparation for execution
            position_0(driver)

            execution(driver, filepath)

        elif choice == "3":
            print("[INFO]: End")
            break

        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

