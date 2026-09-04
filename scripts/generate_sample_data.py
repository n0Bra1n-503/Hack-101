"""Generate sample AWS dataset files (temperature.csv, pressure.csv, humidity.csv)
matching the exact schema shown in AWS sensor monitoring.
"""

from pathlib import Path
import numpy as np
import pandas as pd


def generate_sample_aws_dataset(output_dir: Path = Path("data/raw")):
    """Generate realistic AWS datasets for temperature, pressure, and humidity."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    np.random.seed(42)

    # 4 realistic Automatic Weather Stations in Pune region
    stations = [
        {"id": "CWPRS campus", "lat": 18.446944, "lon": 73.785000, "elev_offset_t": 0.0, "elev_offset_p": 0.0},
        {"id": "Pashan AWS", "lat": 18.536200, "lon": 73.792800, "elev_offset_t": 0.2, "elev_offset_p": -0.8},
        {"id": "Shivajinagar AWS", "lat": 18.530800, "lon": 73.847400, "elev_offset_t": -0.3, "elev_offset_p": 0.5},
        {"id": "Lavale AWS", "lat": 18.542200, "lon": 73.738900, "elev_offset_t": 0.5, "elev_offset_p": -1.5},
    ]

    # Date range: 7 days with 5-minute sampling interval (2024-05-11 to 2024-05-17)
    timestamps = pd.date_range(start="2024-05-11 00:00:00", end="2024-05-17 23:55:00", freq="5min")
    n_points = len(timestamps)

    records_temp = []
    records_press = []
    records_humid = []

    hours = timestamps.hour.to_numpy() + timestamps.minute.to_numpy() / 60.0
    day_indices = np.array([(ts - timestamps[0]).total_seconds() / 86400.0 for ts in timestamps])

    for st in stations:
        st_id = st["id"]
        lat = st["lat"]
        lon = st["lon"]

        # Diurnal temperature cycle: min at 05:30 (approx hour 5.5), max at 14:30 (hour 14.5)
        # May summer weather in Pune: base ~24C at night, ~37C afternoon
        t_diurnal = 30.5 + 7.0 * np.sin((hours - 8.5) * (2 * np.pi / 24))
        # Daily synoptic weather variation
        t_synoptic = 1.5 * np.sin(day_indices * (2 * np.pi / 3.5))
        # Autoregressive noise
        noise_t = np.zeros(n_points)
        for i in range(1, n_points):
            noise_t[i] = 0.95 * noise_t[i - 1] + np.random.normal(0, 0.15)
        temp_values = np.array(t_diurnal + t_synoptic + st["elev_offset_t"] + noise_t, dtype=float)

        # Relative humidity: strong inverse diurnal correlation with temperature (~30% day, ~75% night)
        h_diurnal = 52.0 - 22.0 * np.sin((hours - 8.5) * (2 * np.pi / 24))
        h_synoptic = -3.0 * np.sin(day_indices * (2 * np.pi / 3.5))
        noise_h = np.zeros(n_points)
        for i in range(1, n_points):
            noise_h[i] = 0.95 * noise_h[i - 1] + np.random.normal(0, 0.4)
        humid_values = np.clip(h_diurnal + h_synoptic - (st["elev_offset_t"] * 2.0) + noise_h, 15.0, 95.0)

        # Atmospheric pressure: base ~952 hPa (Pune elevation ~560m)
        # Semi-diurnal atmospheric solar tide (12h cycle peak at 10:00 & 22:00, trough at 04:00 & 16:00)
        p_tide = 1.5 * np.sin((hours - 4.0) * (4 * np.pi / 24))
        p_synoptic = 2.0 * np.cos(day_indices * (2 * np.pi / 4.0))
        noise_p = np.zeros(n_points)
        for i in range(1, n_points):
            noise_p[i] = 0.96 * noise_p[i - 1] + np.random.normal(0, 0.08)
        press_values = np.array(952.0 + p_tide + p_synoptic + st["elev_offset_p"] + noise_p, dtype=float)

        # Inject some realistic exploratory quirks (data quality events)
        if st_id == "Lavale AWS":
            # Stuck / flatline reading for 12 consecutive samples on Day 3
            flat_idx = 600
            temp_values[flat_idx : flat_idx + 12] = temp_values[flat_idx]
            humid_values[flat_idx : flat_idx + 12] = humid_values[flat_idx]

        if st_id == "Pashan AWS":
            # Sudden transient spike in pressure
            spike_idx = 1120
            press_values[spike_idx] += 8.5

        if st_id == "CWPRS campus":
            # Sudden localized cold downdraft / precipitation cooling
            event_idx = 1450
            temp_values[event_idx : event_idx + 6] -= 6.0
            humid_values[event_idx : event_idx + 6] += 25.0

        for idx, ts in enumerate(timestamps):
            # Simulate a few missing records for Shivajinagar
            if st_id == "Shivajinagar AWS" and 800 <= idx <= 806:
                continue

            orig_time_str = ts.strftime("%d-%m-%Y %H:%M")
            iso_time_str = ts.strftime("%Y-%m-%d %H:%M:%S")

            base_meta = {
                "station_id": st_id,
                "latitude": lat,
                "longitude": lon,
                "original_time": orig_time_str,
                "timestamp": iso_time_str,
                "year": ts.year,
                "month": ts.month,
                "day": ts.day,
                "hour": ts.hour,
                "day_of_year": ts.dayofyear,
            }

            rec_t = dict(base_meta)
            rec_t["temperature"] = round(float(temp_values[idx]), 1)
            records_temp.append(rec_t)

            rec_p = dict(base_meta)
            rec_p["pressure"] = round(float(press_values[idx]), 2)
            records_press.append(rec_p)

            rec_h = dict(base_meta)
            rec_h["humidity"] = round(float(humid_values[idx]), 1)
            records_humid.append(rec_h)

    df_temp = pd.DataFrame(records_temp)
    df_press = pd.DataFrame(records_press)
    df_humid = pd.DataFrame(records_humid)

    df_temp.to_csv(output_dir / "temperature.csv", index=False)
    df_press.to_csv(output_dir / "pressure.csv", index=False)
    df_humid.to_csv(output_dir / "humidity.csv", index=False)

    print(f"Generated sample datasets in {output_dir}:")
    print(f"  - temperature.csv: {df_temp.shape[0]} rows, {df_temp.shape[1]} cols")
    print(f"  - pressure.csv:    {df_press.shape[0]} rows, {df_press.shape[1]} cols")
    print(f"  - humidity.csv:    {df_humid.shape[0]} rows, {df_humid.shape[1]} cols")


if __name__ == "__main__":
    generate_sample_aws_dataset()
