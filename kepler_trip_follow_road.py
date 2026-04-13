import json
import time
import random
import requests
import pandas as pd

# --- Configuration ---
TRIPS_INPUT = "Viajes_Gipuzkoa_25_PERCENT.csv"
POINTS_INPUT = "gps_points_by_zone.csv"
OUTPUT_FILE = "Kepler_Final_Routes.geojson"
LIMIT = 200
# ---------------------

def clean_id(val):
    s = str(val)
    if '.' in s:
        s = s.split('.')
    return s.strip()

print("--- DEBUG START ---")
print("Reading files...")
df_trips = pd.read_csv(TRIPS_INPUT).head(LIMIT).copy()
df_pts = pd.read_csv(POINTS_INPUT)

df_pts['zone_id'] = df_pts['zone_id'].apply(clean_id)
df_trips['origen'] = df_trips['origen'].apply(clean_id)
df_trips['destino'] = df_trips['destino'].apply(clean_id)

zone_lookup = df_pts.groupby('zone_id')[['lng', 'lat']].apply(lambda x: x.values.tolist()).to_dict()

# --- ANALYSE DES ZONES DISPONIBLES ---
print(f"Total zones found in points file: {len(zone_lookup)}")
sample_zones = list(zone_lookup.keys())[:5]
print(f"Sample of IDs in mapping: {sample_zones}")

geojson = {"type": "FeatureCollection", "features": []}
success_count = 0

print(f"\nAnalyzing {len(df_trips)} trips one by one...")

for idx, row in df_trips.iterrows():
    orig, dest = row["origen"], row["destino"]
    
    # STEP 1: Check ID matching
    if orig not in zone_lookup or dest not in zone_lookup:
        reason = ""
        if orig not in zone_lookup: reason += f"Origin {orig} unknown. "
        if dest not in zone_lookup: reason += f"Dest {dest} unknown. "
        print(f"Row {idx}: FAILED - {reason}")
        continue
        
    # STEP 2: Pick points
    p1 = random.choice(zone_lookup[orig])
    p2 = random.choice(zone_lookup[dest])
    
    # STEP 3: API Request
    url = f"https://router.project-osrm.org/route/v1/driving/{p1},{p1};{p2},{p2}?overview=full&geometries=geojson"
    
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        data = r.json()
        
        if data.get("code") == "Ok":
            geojson["features"].append({
                "type": "Feature",
                "geometry": data["routes"]["geometry"],
                "properties": {
                    "id": idx, "origin": orig, "destination": dest,
                    "purpose": str(row.get("actividad_destino", "other"))
                }
            })
            success_count += 1
            print(f"Row {idx}: SUCCESS (Route found)")
        else:
            print(f"Row {idx}: OSRM ERROR - {data.get('code')}")
            
    except Exception as e:
        print(f"Row {idx}: CONNECTION ERROR - {e}")
        
    time.sleep(1.1) 

print(f"\n--- DEBUG END ---")
print(f"Final results: {success_count}/{len(df_trips)} successful.")