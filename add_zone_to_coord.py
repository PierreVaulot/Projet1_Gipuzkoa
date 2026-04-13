import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

print(" Loading data")

# Load the points (your file with lat and lng)
df_points = pd.read_csv("points_fixes.csv")

# Transform the simple dataframe into "Geometry" objects that Python understands
geometry = [Point(xy) for xy in zip(df_points['lng'], df_points['lat'])]

# Create a "GeoDataFrame" (a dataframe with a magical geometry column)
geo_points = gpd.GeoDataFrame(df_points, geometry=geometry, crs="EPSG:4326")


# Load the district map (Shapefile)
print(" Loading the district map")
# Replace with the correct path to your shapefile
districts = gpd.read_file("zonificacion_distritos/zonificacion_distritos.shp")

# Ensure both files speak the same spatial language (same projection)
if districts.crs != "EPSG:4326":
    print(" Reprojecting map to standard GPS format")
    districts = districts.to_crs("EPSG:4326")


# Spatial Join (Geographical intersection)
print(" Calculating intersections (Which points fall into which districts?)")
points_with_zones = gpd.sjoin(geo_points, districts, how="inner", predicate="within")

# Cleanup and Save
zone_name_column = "ID" 

final_file = points_with_zones[['lat', 'lng', zone_name_column]]
# Rename the column so our other script understands it
final_file = final_file.rename(columns={zone_name_column: "zone_id"})

output_name = "gps_points_by_zone.csv"
final_file.to_csv(output_name, index=False)

print(f"Success {len(final_file)} points have been mapped to their respective districts")
print(f"File saved as: {output_name}")