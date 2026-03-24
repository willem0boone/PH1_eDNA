import pandas as pd

# -------------------------
# 1. Load data
# -------------------------
lookup = pd.read_csv("output/holo_mero_table.csv")
non_aggregated = pd.read_csv("output/non_aggregated_data.csv")

# Ensure aphiaID is int in both
lookup['aphiaID'] = lookup['aphiaID'].astype(int)
non_aggregated['aphiaID'] = non_aggregated['aphiaID'].astype(int)

# -------------------------
# 2. Merge to assign LifeformCategory
# -------------------------
df = non_aggregated.merge(
    lookup[['aphiaID', 'LifeformCategory']],
    on='aphiaID',
    how='left'
)

# -------------------------
# 3. Keep only holo/mero
# -------------------------
df = df[df['LifeformCategory'].isin(['Holoplankton', 'Meroplankton'])]

# -------------------------
# 4. Convert date to datetime and extract month
# -------------------------
df['date'] = pd.to_datetime(df['date'], dayfirst=True)
df['month'] = df['date'].dt.to_period('M')  # e.g. 2021-07

# -------------------------
# 5. Aggregate densities
# -------------------------
monthly = (
    df.groupby(['month', 'LifeformCategory'])['density']
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)

# -------------------------
# 6. Optional: rename columns
# -------------------------
monthly.columns.name = None  # remove multi-index name

# -------------------------
# 7. Save result
# -------------------------
monthly.to_csv("output/monthly_lifeform_aggregates.csv", index=False)

print(monthly.head())



