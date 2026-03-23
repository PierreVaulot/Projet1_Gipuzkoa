import pandas as pd
import gc
import os

# --- HARDCODED SETTINGS ---
INPUT_FILE = "includes/flux_gipuzkoa_complet_02-2025.csv"
TARGET_DATE = 20250214  # The date we care about (YYYYMMDD format)
OUTPUT_FILE = f"14022025_Viajes_Gipuzkoa.csv"

def extract_single_day():
    print(f"starting extraction for {TARGET_DATE}...")
    
    # nuke the output file if it already exists so we don't accidentally double our data
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    first_write = True
    total_rows_kept = 0

    try:
        # reading in chunks of 200k rows so we don't blow up our 4GB of RAM
        # sep=None makes pandas guess if it's commas or semicolons
        
        reader = pd.read_csv(INPUT_FILE, chunksize=200000, sep=None, engine='python')
        
        for i, chunk in enumerate(reader):
            # scrub the column names (lowercase, no trailing spaces) just to be safe
            chunk.columns = chunk.columns.str.strip().str.lower()
            
            # the raw data sometimes uses 'fecha', sometimes 'date'. catch both.
            date_col = 'fecha' if 'fecha' in chunk.columns else 'date'
            
            # keep only our target day
            filtered_chunk = chunk[chunk[date_col] == TARGET_DATE]
            
            if not filtered_chunk.empty:
                # append mode ('a') so we just keep tacking rows onto the end of the file
                filtered_chunk.to_csv(OUTPUT_FILE, mode='a', index=False, header=first_write)
                first_write = False
                total_rows_kept += len(filtered_chunk)
            
            # print a heartbeat every 10 chunks so we know it hasn't frozen
            if i % 10 == 0:
                print(f"  still alive, processing chunk {i}...")
            
            # manually begging python to free up memory before the next loop
            del chunk
            del filtered_chunk
            gc.collect()

        print(f"\ndone! extraction finished.")
        print(f"saved output to: {OUTPUT_FILE}")
        print(f"total rows extracted for the day: {total_rows_kept:,}")

    except Exception as e:
        print(f"well, something crashed: {e}")

if __name__ == "__main__":
    extract_single_day()