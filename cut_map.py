import geopandas as gpd
import matplotlib.pyplot as plt
import os

raw_shapefile = "zonificacion_distritos/zonificacion_distritos.shp" 
out_folder = "includes" 

# make sure the output dir exists so we don't crash at the very end
if not os.path.exists(out_folder):
    os.makedirs(out_folder)

print("loading the massive base map... hold on")
gdf = gpd.read_file(raw_shapefile)

print(f"total zones loaded: {len(gdf)}")
print("columns we have to work with:", gdf.columns.tolist())

# gipuzkoa postal codes start with 20. clipping out everything else.
# casting to string first just in case pandas read them as integers

gdf_gipuzkoa = gdf[gdf['ID'].astype(str).str.startswith('20')]

print(f"gipuzkoa zones only: {len(gdf_gipuzkoa)}")

# quick sanity check to make sure we actually kept the right region
gdf_gipuzkoa.plot(edgecolor='black', linewidth=0.5, color='lightgreen', figsize=(10, 8))
plt.title("sanity check: Gipuzkoa map")
plt.axis('off') 
plt.show()

# dump the clean sliced map for the other scripts
output_path = os.path.join(out_folder, "gipuzkoa_distritos.shp")
gdf_gipuzkoa.to_file(output_path)

print(f"done! sliced shapefile saved to: {output_path}")