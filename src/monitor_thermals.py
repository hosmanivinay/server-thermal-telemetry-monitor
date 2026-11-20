import os
import time
import pandas as pd
import matplotlib.pyplot as plt

# Threshold Constants
TEMP_CRITICAL_C = 85.0
FAN_STALL_RPM = 1200
HIGH_LOAD_W = 150.0

def run_telemetry_monitor(input_csv="data/raw_sensor_telemetry.csv"):
    start_time = time.perf_counter()
    
    # 1. Load sensor telemetry
    df = pd.read_csv(input_csv, parse_dates=["timestamp"])
    
    # 2. Vectorized threshold filtering
    overheating_mask = df["cpu_temp_c"] >= TEMP_CRITICAL_C
    fan_stall_mask = (df["fan_speed_rpm"] <= FAN_STALL_RPM) & (df["power_load_w"] >= HIGH_LOAD_W)
    
    df["alert_type"] = "NORMAL"
    df.loc[overheating_mask, "alert_type"] = "OVERHEATING"
    df.loc[fan_stall_mask, "alert_type"] = "FAN_STALL"
    df.loc[overheating_mask & fan_stall_mask, "alert_type"] = "CRITICAL_THERMAL_AND_FAN_FAILURE"
    
    alerts_df = df[df["alert_type"] != "NORMAL"].copy()
    
    # 3. Export CSV alert report
    os.makedirs("output", exist_ok=True)
    report_path = os.path.join("output", "thermal_alerts_report.csv")
    alerts_df.to_csv(report_path, index=False)
    
    # 4. Plot temperature trends & threshold breaches for top affected nodes
    top_nodes = alerts_df["node_id"].value_counts().head(4).index.tolist()
    plot_df = df[df["node_id"].isin(top_nodes)].sort_values("timestamp")
    
    plt.figure(figsize=(12, 6))
    for node in top_nodes:
        node_data = plot_df[plot_df["node_id"] == node]
        plt.plot(node_data["timestamp"], node_data["cpu_temp_c"], label=node, alpha=0.8, linewidth=1.2)
    
    plt.axhline(y=TEMP_CRITICAL_C, color="red", linestyle="--", linewidth=1.5, label=f"Critical Threshold ({TEMP_CRITICAL_C}°C)")
    plt.title("Server Node CPU Temperature Trends (Top 4 Alerting Nodes)")
    plt.xlabel("Timestamp")
    plt.ylabel("CPU Temperature (°C)")
    plt.legend(loc="upper right")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    
    chart_path = os.path.join("output", "node_temperature_trends.png")
    plt.savefig(chart_path, dpi=150)
    plt.close()
    
    elapsed = time.perf_counter() - start_time
    print(f"Processed {len(df):,} rows in {elapsed:.3f} seconds.")
    print(f"Flagged {len(alerts_df):,} anomalies -> Saved to {report_path}")
    print(f"Saved thermal trend visualization -> {chart_path}")

if __name__ == "__main__":
    run_telemetry_monitor()