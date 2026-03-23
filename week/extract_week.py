import pandas as pd
import gc

print("Creation file week1")

# write the date
week_1 = [20250201, 20250202, 20250203, 20250204, 20250205, 20250206, 20250207]

# chunking for the RAM
chunks = []
for chunk in pd.read_csv("includes/flux_gipuzkoa_complet_02-2025.csv", 
                         chunksize=500000,
                         dtype={'origen': 'str', 'destino': 'str', 'viajes': 'float32', 'fecha': 'int32'}):
    
    # only week
    filtre = chunk[chunk['fecha'].isin(week_1)]
    chunks.append(filtre)
    del chunk
    gc.collect()

# save
df_week = pd.concat(chunks)
df_week.to_csv("flux_gipuzkoa_WEEK_01.csv", index=False)

print(f" Create file: {len(df_week):,} lines in 'flux_gipuzkoa_WEEK_01.csv'")