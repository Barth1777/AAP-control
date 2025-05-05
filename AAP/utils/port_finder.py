"""
-- AAP by Barth with SO-100 arm by LEROBOT --
last update 05/05/2025

program to find the port of the robot arm
"""
from serial.tools import list_ports

def list_all_ports():
    return set([port.device for port in list_ports.comports()])

def find_previous_port():
    print("leave the arm plugged in and press enter")
    input()
    ports_before = list_all_ports()

    print("Unplug the robot arm and press Enter.")
    input()
    ports_after = list_all_ports()

    removed_ports = ports_before - ports_after

    if len(removed_ports) == 0:
        raise RuntimeError("No missing ports. Check that you have unplugged the arm.")
    elif len(removed_ports) > 1:
        raise RuntimeError(f"Several missing ports: {removed_ports}")

    port = removed_ports.pop()
    print(f"[INFO] Port detects automatically : {port}")

    # Replace cu by tty        (useful for MacOS)
    if "/cu." in port:
        port = port.replace("/cu.", "/tty.")
    return port

#------------------------------------------------------------ automatic detection for ease of use ( adapt for your system)
def find_feurt_port():
    ports = list_ports.comports()
    for port in ports:
        if "usbserial" in port.device: #------------------------> change this line for your system
            tty_version = port.device.replace("/cu.", "/tty.")
            print(f"[INFO] FE-URT automatically detected on : {tty_version}")
            return tty_version
    raise RuntimeError("FE-URT not detected on USB ports.")