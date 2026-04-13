import pandas as pd

print("Loading the large dataset into memory")
# Replace with the correct file path if your CSV is in another folder
df_full = pd.read_csv("14022025_Viajes_Gipuzkoa.csv")

print(f"Original number of rows: {len(df_full)}")

# frac=0.25 means we randomly keep 25% of the rows.
# random_state=42 ensures reproducibility (if you run the script again, it will pick the exact same 10%)
print("Performing 10% random sampling")
df_sample = df_full.sample(frac=0.25, random_state=42)

# Saving the new, lighter file
new_filename = "Viajes_Gipuzkoa_25_PERCENT.csv"
df_sample.to_csv(new_filename, index=False)

print(f"The new file contains {len(df_sample)} rows.")
print(f"Saved as: {new_filename}")