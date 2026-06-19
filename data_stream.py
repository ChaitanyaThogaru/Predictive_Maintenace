import time
import random
import math
from queue import Queue

def sensor_producer(data_queue: Queue):
    """
    Simulates high-frequency industrial sensor telemetry from an operational asset.
    Pushes real-time data packets into a thread-safe queue.
    """
    tick = 0
    while True:
        tick += 1
        
        base_temp = 65.0 + 5.0 * math.sin(tick * 0.05)
        temperature = base_temp + random.uniform(-0.8, 0.8)
        
        base_vib = 2.5 + 0.3 * math.cos(tick * 0.1)
        vibration = base_vib + random.uniform(-0.1, 0.1)
        
        base_press = 4.0 + 0.2 * math.sin(tick * 0.08)
        pressure = base_press + random.uniform(-0.1, 0.1)
        
        if random.random() > 0.98:
            fault_type = random.choice(["thermal", "vibration", "pressure"])
            if fault_type == "thermal":
                temperature += random.uniform(15.0, 25.0)
            elif fault_type == "vibration":
                vibration += random.uniform(2.0, 3.5)
            elif fault_type == "pressure":
                pressure += random.uniform(1.5, 2.5)

        data_packet = {
            "timestamp": time.time(),
            "temperature": round(temperature, 2),
            "vibration": round(vibration, 2),
            "pressure": round(pressure, 2)
        }
        
        data_queue.put(data_packet)
        time.sleep(0.1)