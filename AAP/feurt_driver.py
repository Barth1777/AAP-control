import serial
import time
from time import sleep
from utils.port_finder import find_feurt_port  # ou find_feurt_port
from config import MOTOR_LIMITS

class FEURTDriver:
    def __init__(self, baudrate=1_000_000):
        port = find_feurt_port()
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=0.1)
        print(f"[INFO] Connecté à {port} en {baudrate} bauds")

    def reconnect(self,baudrate=1_000_000):
        print("[INFO] Redémarrage du port série...")
        self.ser.close()
        time.sleep(0.5)
        port = find_feurt_port()
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=0.1)
        print("[INFO] Port série reconnecté.")

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
        sleep(0.01)

    def move_motor(self, motor_id, position):
        if not (0 <= position <= 65535):
            raise ValueError("Position invalide : doit être entre 0 et 65535")

        #  Zone morte pour éviter les oscillations du moteur de base (moteur 1)
        if motor_id == 1:
            current_pos = self.read_position(motor_id, message=False)
            threshold = 5  # ajustable si besoin
            if abs(position - current_pos) <= threshold:
                return  # Ne rien envoyer si la différence est négligeable

        # Envoi normal de la commande
        pos_l = position & 0xFF
        pos_h = (position >> 8) & 0xFF

        GOAL_POSITION_ADDR = 0x2A
        self.send_command(motor_id, 0x03, [GOAL_POSITION_ADDR, pos_l, pos_h])
    
    def read_position(self, motor_id, message=True):
        PRESENT_POSITION_ADDR = 0x38  # Adresse du registre position
        LENGTH_TO_READ = 2            # 2 bytes : LSB + MSB

        # Instruction = 0x02 (Read), params = [addr, length]
        self.send_command(motor_id, 0x02, [PRESENT_POSITION_ADDR, LENGTH_TO_READ])

        # Attente de la réponse
        response = self.ser.read(8)  # 8 = taille réponse attendue : Header(2) + ID(1) + Length(1) + Instruction(1) + Data(2) + Checksum(1)

        if len(response) < 8:
            raise RuntimeError("Réponse incomplète")

        pos_l = response[5]
        pos_h = response[6]
        position = pos_h << 8 | pos_l
        if message == True:
            print(f"[INFO] Moteur {motor_id}  Position actuelle = {position}")
        return position
    
    def set_torque(self, motor_id, enable):
        TORQUE_ENABLE_ADDR = 0x28  # Adresse Torque_Enable
        value = 1 if enable else 0
        self.send_command(motor_id, 0x03, [TORQUE_ENABLE_ADDR, value])
        print(f"[INFO] Moteur {motor_id} → Torque {'activé' if enable else 'désactivé'}")



    def convert_position(self,motor_id, virtual_position, virtual_max=4000):
        limits = MOTOR_LIMITS[motor_id]

        real_min = limits["min"]
        real_max = limits["max"]
        modulo = limits["modulo"]

        # Gestion du passage max < min
        if real_max >= real_min:
            travel = (real_max - real_min) % modulo
        else:
            travel = (real_max + modulo - real_min) % modulo

        # Calcul de la position réelle par interpolation linéaire
        ratio = virtual_position / virtual_max
        real_position = (real_min + ratio * travel) % modulo

        return int(real_position)
    
    
    
    def close(self):
        self.ser.close()