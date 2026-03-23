import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer
import json
import random
import os

# =================================================================
# MANUAL TWEAK AREA (NUDGE)
# =================================================================
# if the points map too LOW, increase LAT_NUDGE (e.g., 0.008)
# if the points map too far LEFT, increase LNG_NUDGE (e.g., 0.002)
LAT_NUDGE = 0.0085  
LNG_NUDGE = 0.0000
# =================================================================

POP_FILE = "2873.csv"
FLOW_FILE = "14022025_Viajes_Gipuzkoa.csv"
POI_FILE = "points_region_prets.csv"
SHP_FILE = "includes/gipuzkoa_distritos.shp"

OUT_TRIPS = "sim_trips_final.json"
OUT_POP = "sim_population_dynamique.csv"
OUT_POINTS = "points_fixes.csv"
OUT_BOUNDARIES = "limites_districts.json"

# feb 14 2025 midnight unix timestamp
BASE_TS = 1739491200 

def run_unified_simulation():
    print("starting the unified simulation engine...")

    # 1. LOAD POPULATION
    # forcing latin-1 encoding because the spanish raw data has weird characters that break utf-8
    df_pop = pd.read_csv(POP_FILE, sep='\t', encoding='latin-1')
    df_pop.columns = df_pop.columns.str.strip()
    
    # extract the 5-digit zip code/municipality id
    df_pop['id_5'] = df_pop['Municipalities'].str.extract(r'^(\d{5})')
    # clean the comma thousands separator and cast to float
    df_pop['val'] = df_pop['Total'].astype(str).str.replace(',', '').astype(float)
    pop_map = df_pop.dropna(subset=['id_5']).set_index('id_5')['val'].to_dict()

    # 2. SHAPEFILE ALIGNMENT (the tricky math part)
    print("aligning points of interest to the shapefile bounding box...")
    gdf_dist = gpd.read_file(SHP_FILE).to_crs("EPSG:4326")
    gdf_dist.to_file(OUT_BOUNDARIES, driver='GeoJSON') # dump for kepler
    
    # get the center of the bounding box (GPS coordinates)
    bounds = gdf_dist.total_bounds # [minx, miny, maxx, maxy]
    shp_lat_c = (bounds + bounds) / 2
    shp_lng_c = (bounds + bounds) / 2

    # convert GPS center to flat UTM metric system for accurate math
    
    gps_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True)
    target_x, target_y = gps_to_utm.transform(shp_lng_c, shp_lat_c)

    # fix POI coordinates (flip the Y axis and center them)
    df_p = pd.read_csv(POI_FILE)
    df_p['fx'], df_p['fy'] = df_p['gama_x'], -df_p['gama_y']
    p_xc = (df_p['fx'].min() + df_p['fx'].max()) / 2
    p_yc = (df_p['fy'].min() + df_p['fy'].max()) / 2

    # transform back from UTM to GPS
    utm_to_gps = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)
    lons, lats = utm_to_gps.transform(df_p['fx'] + (target_x - p_xc), 
                                      df_p['fy'] + (target_y - p_yc))
    
    # apply the manual hardcoded nudges if things are still visually off
    lats = [l + LAT_NUDGE for l in lats]
    lons = [ln + LNG_NUDGE for ln in lons]
    
    pois_gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lons, lats), crs="EPSG:4326")
    pd.DataFrame({'lat': lats, 'lng': lons}).to_csv(OUT_POINTS, index=False)

    # 3. BASE POPULATION DISTRIBUTION
    print("distributing base population across districts...")
    gdf_dist['id_5'] = gdf_dist['ID'].str[:5]
    counts = gdf_dist['id_5'].value_counts().to_dict()
    
    # divide the municipality population evenly among its sub-districts (default to 5k if unknown)
    pop_init = {str(r['ID']).strip(): pop_map.get(r['id_5'], 5000)/counts.get(r['id_5'], 1) 
                for _, r in gdf_dist.iterrows()}
    
    # calculate centroids for fallback routing
    gdf_utm = gdf_dist.to_crs("EPSG:25830")
    centroids = gdf_utm.geometry.centroid
    utm_to_gps = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)
    
    fallback_coords = {}
    for i, row in gdf_dist.iterrows():
        ln, lt = utm_to_gps.transform(centroids.iloc[i].x, centroids.iloc[i].y)
        fallback_coords[str(row['ID']).strip()] = (lt, ln)

    # 4. TRIPS AND EVENTS GENERATOR
    print("simulating trips and building population events ledger...")
    
    # figure out which POIs fall inside which district polygons
    
    pois_in_dist = gpd.sjoin(pois_gdf, gdf_dist, how="inner", predicate="within")
    
    poi_dict = pois_in_dist.groupby('ID').apply(lambda x: list(zip(x.geometry.y, x.geometry.x))).to_dict()
    poi_dict = {str(k).strip(): v for k, v in poi_dict.items()}

    df_flux = pd.read_csv(FLOW_FILE)
    df_flux.columns = df_flux.columns.str.strip().str.lower()
    
    trips = []
    events = [] # this acts as an accounting ledger for population (+/-)
    
    for _, row in df_flux.iterrows():
        o = str(row['origen']).strip()
        d = str(row['destino']).strip()
        
        # skip garbage data
        if o not in fallback_coords or d not in fallback_coords: 
            continue
        
        # add some random jitter to the departure time so they don't all leave at exactly XX:00:00
        t_start = BASE_TS + (int(row['periodo']) * 3600) + random.randint(0, 3599)
        t_end = t_start + 1800 # hardcoding 30 mins travel time for simplicity
        
        # pick a random POI in the district, or use the centroid if there are no POIs
        p_o = random.choice(poi_dict.get(o, [fallback_coords[o]]))
        p_d = random.choice(poi_dict.get(d, [fallback_coords[d]]))

        # store the trip geometry for the animation
        trips.append({
            "type": "Feature", 
            "properties": {"v": float(row['viajes'])},
            "geometry": {
                "type": "LineString", 
                "coordinates": [[p_o, p_o, 0, t_start], [p_d, p_d, 0, t_end]]
            }
        })
        
        # record someone leaving (-) and someone arriving (+)
        events.append({'t': t_start, 'id': o, 'v': -float(row['viajes'])})
        events.append({'t': t_end, 'id': d, 'v': float(row['viajes'])})

    # flush trips to disk
    with open(OUT_TRIPS, 'w') as f: 
        json.dump({"type": "FeatureCollection", "features": trips}, f)

    # 5. DYNAMIC POPULATION TIMELINE
    print("cranking out the 24h dynamic population timeline...")
    df_ev = pd.DataFrame(events).sort_values('t')
    pop_timeline = []
    
    # loop through the day in 10-minute (600s) increments
    for ts in range(BASE_TS, BASE_TS + 86400, 600):
        for d_id, base_pop in pop_init.items():
            # sum all the +/- events that happened before this timestamp
            net_change = df_ev[(df_ev['id'] == d_id) & (df_ev['t'] <= ts)]['v'].sum()
            lt, ln = fallback_coords[d_id]
            
            pop_timeline.append({
                'timestamp': ts, 
                'lat': lt, 
                'lng': ln, 
                'population': int(base_pop + net_change)
            })
    
    # save the final dynamic population data
    pd.DataFrame(pop_timeline).to_csv(OUT_POP, index=False)
    
    print("\ndone. all outputs successfully generated.")

if __name__ == "__main__":
    run_unified_simulation()