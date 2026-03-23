import tarfile
import pandas as pd
import os

# --- config ---
TAR_FILE = "202502_Viajes_distritos.tar" 
REGION_CODE = "20"
OUT_FOLDER = "includes"

print(f"starting optimized extraction from: {TAR_FILE}")

if not os.path.exists(TAR_FILE):
    print(f"error: couldn't find '{TAR_FILE}'. exiting.")
    exit()

if not os.path.exists(OUT_FOLDER):
    os.makedirs(OUT_FOLDER)

final_path = os.path.join(OUT_FOLDER, "flux_gipuzkoa_complet_balance.csv")

# clean up previous runs
if os.path.exists(final_path):
    os.remove(final_path)
    print("deleted old output file to start fresh.")

first_pass = True
days_processed = 0

try:
    with tarfile.open(TAR_FILE, "r") as tar:
        print("parsing and simplifying (mapping outside zones to 'Other')...")
        
        for member in tar.getmembers():
            if member.isfile() and (".csv" in member.name or ".txt" in member.name):
                print(f"\nprocessing {member.name}", end=" ")
                
                f = tar.extractfile(member)
                comp_type = 'gzip' if member.name.endswith('.gz') else None
                
                try:
                    reader = pd.read_csv(
                        f, 
                        sep='|', 
                        compression=comp_type,
                        dtype={'origen': str, 'destino': str},
                        chunksize=100000 
                    )

                    for chunk in reader:
                        # 1. keep rows where either origin or destination is in our region
                        filtered = chunk[
                            (chunk['origen'].str.startswith(REGION_CODE)) | 
                            (chunk['destino'].str.startswith(REGION_CODE))
                        ].copy() 
                        
                        if not filtered.empty:
                            # 2. simplify: if the code doesn't start with our region, replace with 'Other'
                            filtered.loc[~filtered['origen'].str.startswith(REGION_CODE), 'origen'] = 'Other'
                            filtered.loc[~filtered['destino'].str.startswith(REGION_CODE), 'destino'] = 'Other'

                            # 3. stream directly to disk
                            filtered.to_csv(
                                final_path, 
                                mode='a', 
                                index=False, 
                                header=first_pass 
                            )
                            first_pass = False
                            print(".", end="", flush=True)
                            
                    days_processed += 1
                    
                except Exception as file_err:
                    print(f"\nfailed to process {member.name}: {file_err}")

        print(f"\n\ndone. balanced file created at: {final_path}")

except Exception as e:
    print(f"something went wrong: {e}")