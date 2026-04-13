import json
import time
import random
import requests
import pandas as pd

TRIPS_FILE = "Viajes_Gipuzkoa_25_PERCENT.csv"
POINTS_FILE = "gps_points_by_zone.csv"
OUTPUT_FILE = "Kepler_Final_Routes.geojson"
SAMPLE_SIZE = 200


print(f"Loading {SAMPLE_SIZE} trips...")
df_trips = pd.read_csv(TRIPS_FILE).head(SAMPLE_SIZE).copy()
df_pts = pd.read_csv(POINTS_FILE)

# Force string types to avoid matching issues between float/int/str
df_pts['zone_id'] = df_pts['zone_id'].astype(str)
df_trips['origen'] = df_trips['origen'].astype(str)
df_trips['destino'] = df_trips['destino'].astype(str)

# Build lookup dict: {'zone_id': [[lng, lat], ...]}
zone_pts = df_pts.groupby('zone_id')[['lng', 'lat']].apply(lambda x: x.values.tolist()).to_dict()

geojson = {"type": "FeatureCollection", "features": []}
success_count = 0

print("Fetching routes from OSRM...")

for idx, row in df_trips.iterrows():
    orig, dest = row["origen"], row["destino"]
    
    # Skip if we don't have mapping data for these zones
    if orig not in zone_pts or dest not in zone_pts:
        continue
        
    # Pick random points in the origin and destination zones
    lon1, lat1 = random.choice(zone_pts[orig])
    lon2, lat2 = random.choice(zone_pts[dest])
    
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    
    try:
        res = requests.get(url).json()
        
        if res.get("code") == "Ok":
            geojson["features"].append({
                "type": "Feature",
                "geometry": res["routes"]["geometry"],
                "properties": {
                    "trip_id": idx,
                    "origin": orig,
                    "destination": dest,
                    "purpose": str(row["actividad_destino"]),
                    "distance_km": row.get("viajes_km", 0)
                }
            })
            success_count += 1
            
    except Exception as e:
        print(f"API Error at index {idx}: {e}")
        
    # Rate limiting for OSRM public API (max 1 req/sec)
    time.sleep(1) 
    
    if (idx + 1) % 20 == 0:
        print(f"Processed {idx + 1}/{len(df_trips)}...")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(geojson, f)

print(f"Done. Exported {success_count} routes to {OUTPUT_FILE}")