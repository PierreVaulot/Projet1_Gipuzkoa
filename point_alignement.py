import pandas as pd
import geopandas as gpd
from pyproj import Transformer

# --- CONFIGURATION ---
fichier_csv = 'df_establishments.csv' 
fichier_shp = 'includes/gipuzkoa_distritos.shp' 
nom_sortie = 'points_region_prets.csv'

print("download files...")
df = pd.read_csv(fichier_csv)
map_region = gpd.read_file(fichier_shp)

# limits of the map
# bounds[0] = min_x, bounds[3] = max_y
bounds = map_region.total_bounds
print(f"limits of the map : {bounds}")

# convertisor GPS to meter 
crs_carte = map_region.crs
transformer = Transformer.from_crs("EPSG:4326", crs_carte, always_xy=True)

def calculer_coords(row):
    # GPS data
    ln = row.get('long', row.get('longitud', 0))
    lt = row.get('lat', row.get('latitud', 0))
    
    if lt == 0 or ln == 0:
        return pd.Series([None, None])
    
    # meter conversion
    x_m, y_m = transformer.transform(ln, lt)
    
    # gama data
    gama_x = x_m - bounds[0]
    gama_y = bounds[3] - y_m
    return pd.Series([gama_x, gama_y])

print("calcul (few minutes)...")
df[['gama_x', 'gama_y']] = df.apply(calculer_coords, axis=1)

# clean/save 
df_final = df.dropna(subset=['gama_x', 'gama_y'])
df_final[['gama_x', 'gama_y']].to_csv(nom_sortie, index=False)

print(f"finish, {len(df_final)} in {nom_sortie}")