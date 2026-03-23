import geopandas as gpd

# hardcoded bounding box references for the entire gipuzkoa province.
# we use these to force the top-left corner to be the new (0,0) origin.
GIPUZKOA_MIN_X = 521750.5468
GIPUZKOA_MAX_Y = 4808904.8683

print("loading the original road network shapefile...")
roads = gpd.read_file('road_gipuzkoa/road_gipuzkoa.shp')

print("applying global spatial transformations...")

# step 1: shift everything left so min_x becomes 0
roads.geometry = roads.geometry.translate(xoff=-GIPUZKOA_MIN_X)

# step 2: flip the y-axis (standard GIS goes bottom-up, but screen coords go top-down)
roads.geometry = roads.geometry.scale(yfact=-1, origin=(0, 0))

# step 3: shift everything down so max_y becomes 0
roads.geometry = roads.geometry.translate(yoff=GIPUZKOA_MAX_Y)

output_file = 'roads_gipuzkoa_complet.shp'
roads.to_file(output_file)

print(f"done. transformed roads saved to: {output_file}")