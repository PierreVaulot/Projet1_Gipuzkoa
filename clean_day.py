import pandas as pd
import os

source_file = "20250214_Viajes_distritos.csv.gz" 
region_code = "20"  # gipuzkoa code
out_folder = "includes"

print(f"alright, processing {source_file}...")

if not os.path.exists(source_file):
    print(f"dude, the file '{source_file}' is missing. aborting.")
    exit()

# create the folder if it's not there
if not os.path.exists(out_folder):
    os.makedirs(out_folder)

try:
    print("reading and filtering in chunks so we don't kill the RAM...")
    kept_chunks = []
    
    # read this monster file piece by piece
    reader = pd.read_csv(
        source_file, 
        sep='|', 
        compression='gzip',
        dtype={'origen': str, 'destino': str}, 
        chunksize=100000
    )

    total_rows = 0
    for chunk in reader:
        # keep only rows where origin or destination starts with 20
        filtered = chunk[
            (chunk['origen'].str.startswith(region_code)) | 
            (chunk['destino'].str.startswith(region_code))
        ]
        
        if not filtered.empty:
            kept_chunks.append(filtered)
            total_rows += len(filtered)
            print(".", end="", flush=True) # cheap progress bar

    print("\n") # formatting 
    
    if kept_chunks:
        print("stitching it all together...")
        df_final = pd.concat(kept_chunks)
        
        final_file = "flux_gipuzkoa_final.csv"
        final_path = os.path.join(out_folder, final_file)
        
        # save the clean version
        df_final.to_csv(final_path, index=False)
        print(f"boom, file created: {final_path}")
        print(f"extracted a total of {total_rows} trips for gipuzkoa.")
    else:
        print("weird, didn't find any data for region 20 in there.")

except Exception as e:
    print(f"crap, something broke: {e}")