import pandas as pd
import geopandas as gpd
import json
import gc

# hardcoded configs
INPUT_FILE = "14022025_Viajes_Gipuzkoa.csv"
OUTPUT_FILE = "gipuzkoa_kepler_14022025.json"
BASE_TS = 1739491200 

def prep_trips():
    print("step 1: pulling coordinates from shapefile...")
    gdf = gpd.read_file("includes/gipuzkoa_distritos.shp")
    
    # grabbing the center (centroid) of each district to use as start/end points
    gdf['lng'] = gdf.geometry.centroid.to_crs("EPSG:4326").x
    gdf['lat'] = gdf.geometry.centroid.to_crs("EPSG:4326").y
    coords = gdf.set_index('ID')[['lat', 'lng']].to_dict('index')

    print("step 2: chunking through the massive csv (24h data)...")
    chunks = []
    for chunk in pd.read_csv(INPUT_FILE, chunksize=100000):
        # clean up column names just in case they have weird spaces
        chunk.columns = chunk.columns.str.strip().str.lower()
        
        # ugly hack to find columns dynamically because the names keep changing in the raw data
        c_o = [c for c in chunk.columns if 'ori' in c]
        c_d = [c for c in chunk.columns if 'dest' in c]
        c_t = [c for c in chunk.columns if 'peri' in c or 'hor' in c]
        c_dist = [c for c in chunk.columns if 'dist' in c]
        c_v = [c for c in chunk.columns if 'viaj' in c and 'km' not in c]
        
        # smash the data together to save RAM
        agg = chunk.groupby([c_o, c_d, c_t, c_dist])[c_v].sum().reset_index()
        chunks.append(agg)
        
    # final group by after chunking is done
    df_final = pd.concat(chunks).groupby([c_o, c_d, c_t, c_dist])[c_v].sum().reset_index()
    df_final.columns = ['origen', 'destino', 'periodo', 'distancia', 'viajes']
    
    # rough guess of travel time in seconds based on distance brackets
    duration_map = {'0.5-2': 600, '2-10': 1200, '10-50': 2700, '>50': 4500}

    print("step 3: building the geojson with unix timestamps...")
    features = []
    for _, row in df_final.iterrows():
        o_id, d_id = str(row['origen']), str(row['destino'])
        
        # only process if we actually have coords for both origin and destination
        if o_id in coords and d_id in coords:
            # convert the hour of day to an actual unix timestamp
            t_start = BASE_TS + (int(row['periodo']) * 3600)
            t_end = t_start + duration_map.get(row['distancia'], 900) # default to 15 mins if unknown
            
            features.append({
                "type": "Feature",
                "properties": {"vol": float(row['viajes'])},
                "geometry": {
                    "type": "LineString",
                    # kepler trip layer magic format: [lon, lat, altitude, timestamp]
                    "coordinates": [
                        [coords[o_id]['lng'], coords[o_id]['lat'], 0, t_start],
                        [coords[d_id]['lng'], coords[d_id]['lat'], 0, t_end]
                    ]
                }
            })

    # dump everything to a file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({"type": "FeatureCollection", "features": features}, f)
    
    print(f"done! go drag {OUTPUT_FILE} into kepler.gl")

if __name__ == "__main__":
    prep_trips()