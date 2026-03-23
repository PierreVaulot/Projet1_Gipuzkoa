import pandas as pd
import geopandas as gpd
import gc

print("step 1: extracting district coordinates...")
# load the base map
gdf = gpd.read_file("includes/gipuzkoa_distritos.shp")

# convert to wgs84 (lat/lon) since kepler needs standard gps coordinates
gdf_gps = gdf.to_crs("EPSG:4326")

# calculate the center points (centroids) for each district
gdf_gps['lng'] = gdf_gps.geometry.centroid.x
gdf_gps['lat'] = gdf_gps.geometry.centroid.y
coords = gdf_gps.set_index('ID')[['lat', 'lng']].to_dict('index')

# list to hold our processed data chunks
chunks = []
print("step 2: processing mobility flows in chunks...")

# reading the file in chunks to keep ram usage reasonable
for chunk in pd.read_csv("14022025_Viajes_Gipuzkoa.csv", chunksize=200000):
    # scrub column names (lowercase, remove spaces) just to be safe
    chunk.columns = chunk.columns.str.strip().str.lower()
    
    # detect origin/destination columns dynamically
    c_o = 'origen' if 'origen' in chunk.columns else 'origin'
    c_d = 'destino' if 'destino' in chunk.columns else 'destination'
    
    # map gps coordinates to origin and destination ids
    chunk['lat_o'] = chunk[c_o].astype(str).map(lambda x: coords.get(x, {}).get('lat'))
    chunk['lng_o'] = chunk[c_o].astype(str).map(lambda x: coords.get(x, {}).get('lng'))
    chunk['lat_d'] = chunk[c_d].astype(str).map(lambda x: coords.get(x, {}).get('lat'))
    chunk['lng_d'] = chunk[c_d].astype(str).map(lambda x: coords.get(x, {}).get('lng'))
    
    # drop any trips where we couldn't match the coordinates
    chunk.dropna(subset=['lat_o', 'lat_d'], inplace=True)
    
    # aggregate right away to shrink the memory footprint
    agg = chunk.groupby(['lat_o', 'lng_o', 'lat_d', 'lng_d', 'periodo'])['viajes'].sum().reset_index()
    chunks.append(agg)
    
    # force garbage collection
    del chunk
    gc.collect()

print("step 3: merging and final formatting...")
# smash all the aggregated chunks together into the final dataframe
df_kepler = pd.concat(chunks).groupby(['lat_o', 'lng_o', 'lat_d', 'lng_d', 'periodo'])['viajes'].sum().reset_index()

# the magic line: format '8' to '08:00:00' so kepler recognizes it as a time for the playback slider
df_kepler['periodo'] = df_kepler['periodo'].apply(lambda x: f"{int(x):02d}:00:00")

# export
df_kepler.to_csv("gipuzkoa_kepler_14022025.csv", index=False)

print("\nall done! 'gipuzkoa_kepler_14022025.csv' is ready for kepler.")