import pandas as pd
import numpy as np

print("[*] Loading mobility data...")
# 1. Load the original dataset
df = pd.read_csv('14022025_Viajes_Gipuzkoa.csv')

# 2. FILTER FOR PEAK HOUR ONLY (08:00 - 08:59)
TARGET_HOUR = 8
print(f"[*] Filtering data strictly for hour: {TARGET_HOUR}h...")
df = df[df['periodo'] == TARGET_HOUR].copy()
print(f"[+] Dataset optimized: Only {len(df)} records kept for this hour.")

# 3. Simulation parameters
AVG_SPEED_KMH = 40.0  # Estimated average network speed (adjustable)

print(f"[*] Calculating distances and durations (Speed: {AVG_SPEED_KMH} km/h)...")

# 4. Calculate average distance per trip for each record
df['dist_per_trip'] = np.where(df['viajes'] > 0, df['viajes_km'] / df['viajes'], 0)

# 5. Calculate estimated duration in minutes: (Distance / Speed) * 60
df['est_duration_min'] = (df['dist_per_trip'] / AVG_SPEED_KMH) * 60

print("[*] Generating randomized departure times...")

# 6. Create a clean base date from the 'fecha' column
df['base_date'] = pd.to_datetime(df['fecha'].astype(str), format='%Y%m%d')

# Generate random minutes and seconds ONLY for the filtered rows
random_minutes = np.random.randint(0, 60, size=len(df))
random_seconds = np.random.randint(0, 60, size=len(df))

# Construct departure datetime: Date + Hour(periodo) + random minutes/seconds
df['departure_datetime'] = df['base_date'] + \
                        pd.to_timedelta(df['periodo'], unit='h') + \
                        pd.to_timedelta(random_minutes, unit='m') + \
                        pd.to_timedelta(random_seconds, unit='s')

print("[*] Calculating expected arrival times...")

# 7. Construct arrival datetime: Departure Time + Estimated Duration
df['arrival_datetime'] = df['departure_datetime'] + pd.to_timedelta(df['est_duration_min'], unit='m')

# 8. Format cleanly as strings (HH:MM:SS) for the GAMA agent scheduler
df['departure_time'] = df['departure_datetime'].dt.strftime('%H:%M:%S')
df['arrival_time'] = df['arrival_datetime'].dt.strftime('%H:%M:%S')

# 9. Cleanup and Export
final_cols = [
    'fecha', 'periodo', 'origen', 'destino', 'viajes', 
    'dist_per_trip', 'est_duration_min', 'departure_time', 'arrival_time'
]
df_final = df[final_cols].copy()

# New output file name specifically for the 8h window
output_file = 'Flux_08h_GAMA_Ready.csv'
df_final.to_csv(output_file, index=False)

print(f"\n[+] Success! Highly optimized file exported as: {output_file}")