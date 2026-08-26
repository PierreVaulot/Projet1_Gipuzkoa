import pandas as pd
import geopandas as gpd
import random

print("1/4 Loading files...")
districts = gpd.read_file("includes/gipuzkoa_distritos.shp")
buildings = gpd.read_file("ERAIKINAK_EDIFICIOS/ERAIKINAK_EDIFICIOS_alignes.shp")
flows = pd.read_csv("includes/flux_gipuzkoa_final.csv")

print("2/4 Spatial join...")
if buildings.crs != districts.crs:
    buildings = buildings.to_crs(districts.crs)

buildings['interior_point'] = buildings.geometry.representative_point()
pts_gdf = gpd.GeoDataFrame(geometry=buildings['interior_point'], crs=buildings.crs)

bldgs_in_districts = gpd.sjoin(pts_gdf, districts[['ID', 'geometry']], how="inner", predicate="intersects")

dict_bldgs = bldgs_in_districts.groupby('ID').apply(
    lambda g: [[geom.x, geom.y] for geom in g.geometry]
).to_dict()

print("3/4 Filtering for 8h-9h and Assigning buildings...")
# LE FILTRE MAGIQUE POUR LA RAM : On ne garde que 8h du matin
flows = flows[flows['periodo'].astype(str) == '8'].copy()

minx, miny, maxx, maxy = districts.total_bounds

def get_edge_point():
    edge = random.choice(['top', 'bottom', 'left', 'right'])
    if edge == 'top':
        return [random.uniform(minx, maxx), maxy]
    elif edge == 'bottom':
        return [random.uniform(minx, maxx), miny]
    elif edge == 'left':
        return [minx, random.uniform(miny, maxy)]
    else:
        return [maxx, random.uniform(miny, maxy)]

def get_location(dist_id):
    if str(dist_id) in dict_bldgs:
        return random.choice(dict_bldgs[str(dist_id)])
    else:
        return get_edge_point()

print(" -> Processing coordinates...")
starts = flows['origen'].apply(get_location)
flows['start_x'] = [round(p[0], 2) for p in starts]
flows['start_y'] = [round(p[1], 2) for p in starts]

ends = flows['destino'].apply(get_location)
flows['end_x'] = [round(p[0], 2) for p in ends]
flows['end_y'] = [round(p[1], 2) for p in ends]

print("4/4 Saving...")
output_path = "includes/flux_gipuzkoa_wbatiment_8h.csv"
flows.to_csv(output_path, index=False)
print(f"Done! Lightweight file ready with {len(flows)} rows.")