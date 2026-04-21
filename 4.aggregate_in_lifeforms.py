import pandas as pd

LOOKUP_TABLE = "output/step3_dia_dino_table.csv"
DATA = "output/step2_data_rel.csv"
LF1 = "Diatom"
LF2 = "Dinoflagellate"
OUT_FILE = "output/step4_monthly_lifeform_aggregates_dino_dia.csv"

# -------------------------
# 1. Load data
# -------------------------
lookup = pd.read_csv(LOOKUP_TABLE)
non_aggregated = pd.read_csv(DATA)

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
df = df[df['LifeformCategory'].isin([LF1, LF2])]

# -------------------------
# 4. Convert date to datetime and extract month
# -------------------------
df['date'] = pd.to_datetime(df['date'], dayfirst=True)
df['month'] = df['date'].dt.to_period('M')  # e.g. 2021-07

# -------------------------
# 5. Aggregate relative abundance
# -------------------------
monthly = (
    df.groupby(['month', 'LifeformCategory'])['rel_abundance']
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
monthly.to_csv(OUT_FILE, index=False)

print(monthly.head())



