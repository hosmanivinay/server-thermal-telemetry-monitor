import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_sensor_data(num_rows=10500, num_nodes=48, seed=42):
    np.random.seed(seed)
    
    start_time = datetime(2026, 11, 1, 0, 0, 0)
    timestamps = [start_time + timedelta(seconds=15 * i) for i in range(num_rows)]
    nodes = [f"HPE-DL380-Node-{i:02d}" for i in range(1, num_nodes + 1)]
    
    assigned_nodes = np.random.choice(nodes, size=num_rows)
    
    # Power load between 45W (idle) and 250W (peak compute)
    power_watts = np.round(np.random.uniform(45.0, 250.0, size=num_rows), 1)
    
    # Normal CPU temp correlates with power load + ambient noise
    base_temp = 38.0 + (power_watts - 45.0) * 0.18 + np.random.normal(0, 2.5, size=num_rows)
    cpu_temp_c = np.round(np.clip(base_temp, 35.0, 82.0), 1)
    
    # Normal Fan RPM scales with CPU temperature
    base_rpm = 1800 + (cpu_temp_c - 35.0) * 65 + np.random.normal(0, 120, size=num_rows)
    fan_rpm = np.round(np.clip(base_rpm, 1500, 6500)).astype(int)
    
    df = pd.DataFrame({
        "timestamp": timestamps,
        "node_id": assigned_nodes,
        "power_load_w": power_watts,
        "cpu_temp_c": cpu_temp_c,
        "fan_speed_rpm": fan_rpm
    })
    
    # Inject ~2.5% critical thermal/cooling anomalies
    anomaly_indices = np.random.choice(df.index, size=int(num_rows * 0.025), replace=False)
    half = len(anomaly_indices) // 2
    
    # Fault Type 1: Overheating (>= 85°C under sustained load)
    df.loc[anomaly_indices[:half], "cpu_temp_c"] = np.round(np.random.uniform(85.0, 96.5, size=half), 1)
    df.loc[anomaly_indices[:half], "power_load_w"] = np.round(np.random.uniform(190.0, 250.0, size=half), 1)
    
    # Fault Type 2: Fan Stall (<= 1,200 RPM while power load > 150W)
    df.loc[anomaly_indices[half:], "fan_speed_rpm"] = np.random.randint(600, 1201, size=len(anomaly_indices) - half)
    df.loc[anomaly_indices[half:], "power_load_w"] = np.round(np.random.uniform(160.0, 250.0, size=len(anomaly_indices) - half), 1)
    df.loc[anomaly_indices[half:], "cpu_temp_c"] = np.round(np.random.uniform(78.0, 89.0, size=len(anomaly_indices) - half), 1)
    
    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "raw_sensor_telemetry.csv")
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} telemetry records across {num_nodes} nodes -> {output_path}")

if __name__ == "__main__":
    generate_sensor_data()