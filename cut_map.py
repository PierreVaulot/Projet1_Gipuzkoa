import geopandas as gpd
import os

# --- PATHS ---
raw_roads_file = "road_pais_vasco_clean/road_pais_vasco_clean.shp"
gipuzkoa_mask_file = "includes/gipuzkoa_distritos.shp"
out_folder = "includes"

if not os.path.exists(out_folder):
    os.makedirs(out_folder)

print("====================================================")
print("Starting spatial clipping of the road network...")
print("====================================================")

print("[1/3] Loading Gipuzkoa boundary mask...")
gdf_mask = gpd.read_file(gipuzkoa_mask_file)

print("[2/3] Loading raw Basque Country roads (this may take a minute)...")
gdf_roads = gpd.read_file(raw_roads_file)
print(f"  -> Loaded {len(gdf_roads)} raw road segments.")

print("[3/3] Clipping roads to Gipuzkoa boundaries (Heavy computation)...")
# Ensure Coordinate Reference Systems (CRS) match before clipping
if gdf_roads.crs != gdf_mask.crs:
    print("  -> Aligning CRS...")
    gdf_roads = gdf_roads.to_crs(gdf_mask.crs)

# The spatial clip operation
gdf_clipped = gpd.clip(gdf_roads, gdf_mask)
print(f"  -> Kept {len(gdf_clipped)} road segments inside Gipuzkoa.")

output_path = os.path.join(out_folder, "road_pais_vasco_cropped.shp")
print(f"Exporting cropped shapefile to {output_path}...")
gdf_clipped.to_file(output_path)

print("====================================================")
print("Process completed successfully.")
print(f"File ready for GAMA: {output_path}")
print("====================================================")