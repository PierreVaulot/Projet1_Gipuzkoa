import pandas as pd
import numpy as np

print("loading the big mobility dataset... might take a sec")
df = pd.read_csv('14022025_Viajes_Gipuzkoa.csv')

# 1. grab only the 8am rush hour to save memory
TARGET_HOUR = 8
df = df[df['periodo'] == TARGET_HOUR].copy()

# 2. isolate san sebastian (code starts with 20069)
print("filtering out everything except donostia...")
mask_origen = df['origen'].astype(str).str.startswith('20069')
mask_destino = df['destino'].astype(str).str.startswith('20069')

# Option A: any trip touching the city (inbound, outbound, internal)
df_ss = df[mask_origen | mask_destino].copy()

# Option B: uncomment the line below if your RAM is crying (max survival mode)
# this keeps ONLY internal trips where both start and end are in the city
# df_ss = df[mask_origen & mask_destino].copy()

print(f"dataset shrank down to {len(df_ss)} rows for the 8am window.")

# 3. time math and route logic
AVG_SPEED_KMH = 30.0  # dropping speed to 30 km/h cause it's urban traffic

# calc distance per trip and how long it should take
df_ss['dist_per_trip'] = np.where(df_ss['viajes'] > 0, df_ss['viajes_km'] / df_ss['viajes'], 0)
df_ss['est_duration_min'] = (df_ss['dist_per_trip'] / AVG_SPEED_KMH) * 60

# randomize departure minutes/seconds so they don't all spawn at exactly 08:00:00
df_ss['base_date'] = pd.to_datetime(df_ss['fecha'].astype(str), format='%Y%m%d')
random_minutes = np.random.randint(0, 60, size=len(df_ss))
random_seconds = np.random.randint(0, 60, size=len(df_ss))

df_ss['departure_datetime'] = df_ss['base_date'] + \
                        pd.to_timedelta(df_ss['periodo'], unit='h') + \
                        pd.to_timedelta(random_minutes, unit='m') + \
                        pd.to_timedelta(random_seconds, unit='s')

# add the duration to get the arrival time
df_ss['arrival_datetime'] = df_ss['departure_datetime'] + pd.to_timedelta(df_ss['est_duration_min'], unit='m')

# format them nicely for gama
df_ss['departure_time'] = df_ss['departure_datetime'].dt.strftime('%H:%M:%S')
df_ss['arrival_time'] = df_ss['arrival_datetime'].dt.strftime('%H:%M:%S')

# 4. drop useless columns and export
final_cols = [
    'fecha', 'periodo', 'origen', 'destino', 'viajes', 
    'dist_per_trip', 'est_duration_min', 'departure_time', 'arrival_time'
]
df_final = df_ss[final_cols].copy()

output_file = 'Flux_08h_SanSebastian.csv'
df_final.to_csv(output_file, index=False)
print(f"all good! export saved as {output_file} and ready for gama")