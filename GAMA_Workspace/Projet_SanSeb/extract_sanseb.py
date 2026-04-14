import pandas as pd
import geopandas as gpd
import os

def extract_donostia_all():
    print("[*] Starting extraction process for Donostia...")

    shp_file = "includes/gipuzkoa_distritos.shp"
    establishments_file = "df_establishments.csv"
    donostia_name = "Donostia / San Sebastián"
    donostia_code = "20069"

    # 1. MAP EXTRACTION (Spatial Clipping)
    if os.path.exists(shp_file):
        print("[*] Reading and extracting the base map...")
        gdf = gpd.read_file(shp_file)
        
        # Filter regions by ID starting with 20069 (Donostia area)
        gdf_donostia = gdf[gdf['ID'].astype(str).str.startswith(donostia_code)].copy()
        
        # Export the isolated district map
        gdf_donostia.to_file("donostia_distritos.shp")
        print("[+] Map 'donostia_distritos.shp' generated successfully.")
        
        # Retain the metric Coordinate Reference System (CRS) for alignment
        target_crs = gdf.crs 
    else:
        print("[-] Error: Base shapefile not found.")
        return

    # 2. ESTABLISHMENTS EXTRACTION & METRIC CONVERSION
    if os.path.exists(establishments_file):
        print("[*] Filtering establishments and converting coordinate system...")
        df_est = pd.read_csv(establishments_file)
        
        # Isolate data specific to Donostia
        df_don = df_est[df_est['MUNICIPIO'] == donostia_name].copy()

        # Convert raw GPS coordinates to geographic geometries (EPSG:4326)
        # Assuming column 13 is Longitude and 12 is Latitude based on original data structure
        gdf_pts = gpd.GeoDataFrame(
            df_don, 
            geometry=gpd.points_from_xy(df_don.iloc[:, 13], df_don.iloc[:, 12]),
            crs="EPSG:4326"
        )
        
        # Reproject points to match the map's metric coordinate system
        gdf_pts = gdf_pts.to_crs(target_crs)
        
        # Append the calculated metric coordinates to the dataframe
        df_don['x_metric'] = gdf_pts.geometry.x
        df_don['y_metric'] = gdf_pts.geometry.y
        
        # Export the processed dataset
        df_don.to_csv("establishments_donostia.csv", index=False)
        print(f"[+] Processed file 'establishments_donostia.csv' created ({len(df_don)} records).")
    else:
        print("[-] Error: Establishments dataset not found.")

    print("\n[+] Extraction complete. Please move the generated files to the 'includes' directory.")

if __name__ == "__main__":
    extract_donostia_all()