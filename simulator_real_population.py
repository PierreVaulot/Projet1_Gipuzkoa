import pandas as pd
import geopandas as gpd
import random
import os

# --- file configs ---
POP_FILE = "2873.csv"
FLOW_FILE = "14022025_Viajes_Gipuzkoa.csv"
SHP_FILE = "includes/gipuzkoa_distritos.shp"

# feb 14 2025 midnight unix timestamp
BASE_TS = 1739491200 
OUTPUT_FILE = "population_dynamique_reelle.csv"

def load_base_population(csv_path):
    print(f"loading base population from {csv_path}...")
    
    # reading the tab-separated file. 
    # forcing latin-1 encoding to prevent crashes on spanish special characters
    df_pop = pd.read_csv(csv_path, sep='\t', encoding='latin-1')
    df_pop.columns = df_pop.columns.str.strip()
    
    # extract the 5-digit municipality id using regex
    df_pop['id'] = df_pop['Municipalities'].str.extract(r'^(\d{5})')
    
    # strip commas from the thousand separators and cast to float
    df_pop['base_pop'] = df_pop['Total'].astype(str).str.replace(',', '').astype(float)
    
    # return a clean dictionary mapping id to base population
    return df_pop.dropna(subset=['id']).set_index('id')['base_pop'].to_dict()

def generate_population_timeline():
    # 1. load the initial population snapshot
    initial_pop = load_base_population(POP_FILE)

    # 2. grab the geographic coordinates for the districts
    print("extracting district centroids...")
    gdf_dist = gpd.read_file(SHP_FILE).to_crs("EPSG:4326")
    coords = gdf_dist.set_index('ID').geometry.centroid.apply(lambda p: (p.y, p.x)).to_dict()

    # 3. parse the flow data to build an event ledger
    print("processing mobility flows to build the event ledger...")
    events = []
    df_flows = pd.read_csv(FLOW_FILE)
    df_flows.columns = df_flows.columns.str.strip().str.lower()
    
    for _, row in df_flows.iterrows():
        travelers = float(row['viajes'])
        
        # add random jitter to match the trip animation logic
        t_dep = BASE_TS + (int(row['periodo']) * 3600) + random.randint(0, 3599)
        t_arr = t_dep + 1800 # assuming average 30 min trip
        
        # record departure (-) and arrival (+)
        events.append({'time': t_dep, 'id': str(row['origen']), 'delta': -travelers})
        events.append({'time': t_arr, 'id': str(row['destino']), 'delta': travelers})

    df_events = pd.DataFrame(events).sort_values('time')
    
    # 4. calculate real-time population at 10-minute intervals
    print("calculating real-time population balances (10-min intervals)...")
    timestamps = range(BASE_TS, BASE_TS + 86400, 600) 
    timeline_data = []

    for dist_id, (lat, lng) in coords.items():
        # start with the official census pop, or default to 0 if missing
        pop_start = initial_pop.get(str(dist_id), 0)
        dist_events = df_events[df_events['id'] == str(dist_id)]
        
        for ts in timestamps:
            # sum all +/- events that happened up to this timestamp
            net_change = dist_events[dist_events['time'] <= ts]['delta'].sum()
            
            timeline_data.append({
                'timestamp': ts,
                'district_id': dist_id,
                'lat': lat,
                'lng': lng,
                'population': int(pop_start + net_change)
            })

    # 5. export the timeline
    pd.DataFrame(timeline_data).to_csv(OUTPUT_FILE, index=False)
    print(f"done. dynamic population data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_population_timeline()