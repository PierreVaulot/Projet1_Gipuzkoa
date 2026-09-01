import geopandas as gpd
import pandas as pd
import os

shapefile_path = "includes/gipuzkoa_distritos.shp"
csv_output_path = "mapping_comarcas.csv"

def create_mapping_template(shp_path, csv_path):
    try:
        print(f"Reading file: {shp_path}...")
        
        if not os.path.exists(shp_path):
            print(f" Error: The file {shp_path} was not found. Please check the path.")
            return

        gdf = gpd.read_file(shp_path)
        
        print("\nColumns found in the file:")
        print(gdf.columns.tolist())

        id_column = "ID" 

        if id_column not in gdf.columns:
            print(f"\n Error: The column '{id_column}' does not exist in the shapefile.")
            return

        df = pd.DataFrame(gdf.drop(columns='geometry'))
        df = df.drop_duplicates(subset=[id_column])
        df['COMARCA'] = ""

        remaining_columns = [col for col in df.columns if col not in [id_column, 'COMARCA']]
        df = df[[id_column, 'COMARCA'] + remaining_columns]

        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        print("\n" + "="*50)
        print(f"✅ SUCCESS! The file has been created: {csv_path}")

        
    except Exception as e:
        print(f"\n An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_mapping_template(shapefile_path, csv_output_path)