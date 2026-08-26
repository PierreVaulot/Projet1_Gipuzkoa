import geopandas as gpd
import pandas as pd

def filtrer_et_couper_routes(input_roads, input_districts, output_shapefile):
    print(f"Load roads : {input_roads}...")
    try:
        gdf_roads = gpd.read_file(input_roads)
    except Exception as e:
        print(f"Error : {e}")
        return

    print(f"Load borders (Districts) : {input_districts}...")
    try:
        gdf_districts = gpd.read_file(input_districts)
    except Exception as e:
        print(f"Error : {e}")
        return

    print("CRS")
    if gdf_roads.crs != gdf_districts.crs:
        print(f"Alignement: {gdf_districts.crs}...")
        gdf_roads = gdf_roads.to_crs(gdf_districts.crs)

    print("Delete no used road")
    voies_a_exclure = [
        'footway', 'pedestrian', 'cycleway', 'steps', 
        'path', 'track', 'bridleway', 'service'
    ]
    
    # Ajout du .copy() pour s'assurer qu'on travaille sur un nouveau tableau indépendant
    gdf_voitures = gdf_roads[~gdf_roads['fclass'].isin(voies_a_exclure)].copy()
    print(f"Roads used: {len(gdf_voitures)}")

    print("Processing speed limits (maxspeed)...")
    if 'maxspeed' in gdf_voitures.columns:
        # Force la conversion en nombres
        gdf_voitures['maxspeed'] = pd.to_numeric(gdf_voitures['maxspeed'], errors='coerce')
        # Remplace les valeurs nulles par 50
        gdf_voitures['maxspeed'] = gdf_voitures['maxspeed'].fillna(50)
        # Remplace les valeurs inférieures ou égales à 0 par 50
        gdf_voitures.loc[gdf_voitures['maxspeed'] <= 0, 'maxspeed'] = 50
    else:
        print("Column 'maxspeed' not found. Creating it with default 50.")
        gdf_voitures['maxspeed'] = 50

    print("Clipping")
    gdf_gipuzkoa_roads = gpd.clip(gdf_voitures, gdf_districts)
    print(f"After clipping : {len(gdf_gipuzkoa_roads)}")

    # 4. SAUVEGARDE
    print(f"Save: {output_shapefile}...")
    gdf_gipuzkoa_roads.to_file(output_shapefile)
    
    print("Finish")

if __name__ == "__main__":
    fichier_routes_osm = r"C:\Users\pierr\Desktop\Simulation-MITMA-data\gis_osm_roads_free_1\gis_osm_roads_free_1.shp"
    
    fichier_districts = r"C:\Users\pierr\Desktop\Simulation-MITMA-data\includes\gipuzkoa_distritos.shp" 
    
    fichier_sortie = r"C:\Users\pierr\Desktop\Simulation-MITMA-data\road_pais_vasco_clean\road_pais_vasco_speedlimit.shp"
    
    filtrer_et_couper_routes(fichier_routes_osm, fichier_districts, fichier_sortie)