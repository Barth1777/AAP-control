
"""
-- AAP by Barth with SO-100 arm by LEROBOT --
last update 09/05/2025

module to control the FEURT motors 
low level
             
"""

import serial
import time
from time import sleep
from utils.port_finder import find_feurt_port  
from config import MOTOR_LIMITS

class FEURTDriver:
    def __init__(self, baudrate=1_000_000,command_delay=0.01):
        port = find_feurt_port()
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=0.1)
        self.command_delay = command_delay
        print(f"[INFO] connected to {port} in {baudrate} bauds")

    def reconnect(self,baudrate=1_000_000):
        print("[INFO] Serial port restart...")
        self.ser.close()
        time.sleep(0.5)
        port = find_feurt_port()
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=0.1)
        print("[INFO] Serial port reconnected.")

    def send_command(self, motor_id, instruction, params):
        packet = bytearray()
        packet.append(0xFF)  # Header 1
        packet.append(0xFF)  # Header 2
        packet.append(motor_id)
        packet.append(len(params) + 2)  # Length = params + instruction + checksum
        packet.append(instruction)
        packet.extend(params)
        checksum = ~(motor_id + len(params) + 2 + instruction + sum(params)) & 0xFF
        packet.append(checksum)
        self.ser.write(packet)

        if self.command_delay > 0:
            sleep(self.command_delay)    # wait for the command to be sent

    def move_motor(self, motor_id, position):
        if not (0 <= position <= 65535):
            raise ValueError("Position must be between 0 and 65535")


        pos_l = position & 0xFF
        pos_h = (position >> 8) & 0xFF

        GOAL_POSITION_ADDR = 0x2A
        self.send_command(motor_id, 0x03, [GOAL_POSITION_ADDR, pos_l, pos_h])
    
    def read_position(self, motor_id, message=True):
        PRESENT_POSITION_ADDR = 0x38  # Adress of the present position
        LENGTH_TO_READ = 2            # 2 bytes : LSB + MSB

        # Instruction = 0x02 (Read), params = [addr, length]
        self.send_command(motor_id, 0x02, [PRESENT_POSITION_ADDR, LENGTH_TO_READ])

       
        response = self.ser.read(8) 

        if len(response) < 8:
            raise RuntimeError("Incomplete response from motor")

        pos_l = response[5]
        pos_h = response[6]
        position = pos_h << 8 | pos_l
        if message == True:
            print(f"[INFO] Motor {motor_id}  Current position = {position}")
        return position
    
    def set_torque(self, motor_id, enable):
        TORQUE_ENABLE_ADDR = 0x28  # Adress Torque_Enable
        value = 1 if enable else 0
        self.send_command(motor_id, 0x03, [TORQUE_ENABLE_ADDR, value])
        print(f"[INFO] Motor {motor_id}  Torque {'ON' if enable else 'OFF'}")



    def convert_position(self,motor_id, virtual_position, virtual_max=4000):
        limits = MOTOR_LIMITS[motor_id]

        real_min = limits["min"]
        real_max = limits["max"]
        modulo = limits["modulo"]


        if real_max >= real_min:
            travel = (real_max - real_min) % modulo
        else:
            travel = (real_max + modulo - real_min) % modulo

        ratio = virtual_position / virtual_max
        real_position = (real_min + ratio * travel) % modulo

        return int(real_position)
    
    
    
    def close(self):
        self.ser.close()