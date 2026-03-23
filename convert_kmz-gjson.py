import geopandas as gpd
import fiona


fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['libkml'] = 'rw'

kmz_file = 'Errepideak 2024.kmz'

print("[*] Analyzing the KMZ file")
layers = fiona.listlayers(kmz_file)
print(f"[+] Layers found: {layers}")

final_gdf = None


for layer in layers:
    print(f"[*] Analyzing layer: '{layer}")
    try:
        temp_gdf = gpd.read_file(kmz_file, driver='KML', layer=layer)
        
        temp_gdf = temp_gdf.dropna(subset=['geometry'])
        
        if len(temp_gdf) > 0:
            print(f"[+] {len(temp_gdf)} routes found in layer '{layer}'.")
            final_gdf = temp_gdf
            break
        else:
            print(" |-> Empty layer or no geometry")
            
    except Exception as e:
        print(f" |-> Failed to read layer: {e}")


if final_gdf is not None:
    print("\n[*] Verifying and converting GPS coord")

    if final_gdf.crs is None or final_gdf.crs.to_epsg() != 4326:
        try:
            final_gdf = final_gdf.to_crs("EPSG:4326")
        except:
            final_gdf.set_crs("EPSG:4326", allow_override=True, inplace=True)
            
    output_file = 'Errepideak_2024.geojson'
    final_gdf.to_file(output_file, driver='GeoJSON')
    print(f"\n[+] Finish: {output_file}")
    
else:
    print("\n[-] ERROR: No routes were found in the entire KMZ file")