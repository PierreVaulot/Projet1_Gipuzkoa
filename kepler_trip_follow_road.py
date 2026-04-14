import json
import time
import random
import requests
import pandas as pd

# --- Configuration ---
TRIPS_FILE = "Viajes_Gipuzkoa_25_PERCENT.csv"
POINTS_FILE = "gps_points_by_zone.csv"
OUTPUT_FILE = "Kepler_Final_Routes.geojson"
SAMPLE_SIZE = 200
# ---------------------

def clean_id(val):
    """Safely extract the ID before the decimal point and trim spaces."""
    s = str(val)
    if '.' in s:
        s = s.split('.') # Take the part before the dot
    return s.strip()

print("--- STARTING DEBUG SESSION ---")

print("Reading data...")
df_trips = pd.read_csv(TRIPS_FILE).head(SAMPLE_SIZE).copy()
df_pts = pd.read_csv(POINTS_FILE)

# Normalize IDs to ensure matching works
df_pts['zone_id'] = df_pts['zone_id'].apply(clean_id)
df_trips['origen'] = df_trips['origen'].apply(clean_id)
df_trips['destino'] = df_trips['destino'].apply(clean_id)

# Create lookup: {zone_id: [[lng, lat], ...]}
zone_lookup = df_pts.groupby('zone_id')[['lng', 'lat']].apply(lambda x: x.values.tolist()).to_dict()

print(f"Mapping loaded: {len(zone_lookup)} unique zones available.")

geojson = {"type": "FeatureCollection", "features": []}
success_count = 0

print(f"\nAnalyzing {len(df_trips)} trips...")

for idx, row in df_trips.iterrows():
    orig, dest = row["origen"], row["destino"]
    
    # 1. DEBUG: Check if IDs exist in our GPS database
    if orig not in zone_lookup or dest not in zone_lookup:
        missing = []
        if orig not in zone_lookup: missing.append(f"Origin '{orig}'")
        if dest not in zone_lookup: missing.append(f"Dest '{dest}'")
        print(f"[{idx}] SKIP: ID not found in GPS file -> {', '.join(missing)}")
        continue
        
    # 2. Pick coordinates
    p1 = random.choice(zone_lookup[orig])
    p2 = random.choice(zone_lookup[dest])
    
    # 3. Build and test the URL (Longitude, Latitude)
    # Using http for better compatibility with the public demo server
    url = f"http://router.project-osrm.org/route/v1/driving/{p1},{p1};{p2},{p2}?overview=full&geometries=geojson"
    
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        
        if r.status_code != 200:
            print(f"[{idx}] HTTP ERROR {r.status_code} for URL: {url}")
            continue
            
        data = r.json()
        
        if data.get("code") == "Ok":
            geojson["features"].append({
                "type": "Feature",
                "geometry": data["routes"]["geometry"],
                "properties": {
                    "id": idx,
                    "origin": orig,
                    "destination": dest,
                    "purpose": str(row.get("actividad_destino", "other")),
                    "km": float(row.get("viajes_km", 0))
                }
            })
            success_count += 1
            # Only print success every 10 trips to avoid spamming
            if success_count % 10 == 0:
                print(f"Progress: {success_count} routes successfully calculated...")
                
        else:
            print(f"[{idx}] OSRM ERROR: {data.get('code')} for coordinates {p1} to {p2}")
            
    except Exception as e:
        print(f"[{idx}] CONNECTION ERROR: {e}")
        
    # Rate limit: 1.1s between requests
    time.sleep(1.1) 

# Final Save
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(geojson, f)

print(f"\n--- DEBUG SESSION FINISHED ---")
print(f"Exported {success_count} routes to {OUTPUT_FILE}")