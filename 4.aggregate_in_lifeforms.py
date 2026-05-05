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
# 6. Make sure LF columns exist and convert to relative proportions
# -------------------------
monthly.columns.name = None  # remove multi-index name

# Ensure columns for LF1 and LF2 exist (create as zeros if missing)
for lf in (LF1, LF2):
    if lf not in monthly.columns:
        monthly[lf] = 0.0

# Compute denominator and avoid division by zero
denom = monthly[LF1] + monthly[LF2]

# Where denominator is non-zero, convert to relative proportion
nonzero_mask = denom != 0
monthly.loc[nonzero_mask, LF1] = monthly.loc[nonzero_mask, LF1] / denom[nonzero_mask]
monthly.loc[nonzero_mask, LF2] = monthly.loc[nonzero_mask, LF2] / denom[nonzero_mask]

# Where denominator is zero, set both proportions to zero (or keep NaN if you prefer)
monthly.loc[~nonzero_mask, [LF1, LF2]] = 0.0

# Optional: create a 'period' column as string (e.g. '2021-07') if you want the same column name as earlier output
# This converts pandas Period to string; comment out if you prefer to keep the Period dtype in 'month'
monthly['period'] = monthly['month'].astype(str)

# Optional: reorder columns so 'period' appears first
cols = ['period'] + [c for c in monthly.columns if c not in ('period', 'month')]
monthly = monthly[cols]

# -------------------------
# 7. Save result
# -------------------------
# Change OUT_FILE at top if you want a different filename (e.g., "output/imaging.csv")
monthly.to_csv(OUT_FILE, index=False)

# Quick sanity prints
print(monthly.head())
# Check that LF1 + LF2 equals 1 (or 0 where denom was zero)
if LF1 in monthly.columns and LF2 in monthly.columns:
    print("Row-wise sums (should be 1.0 or 0.0 when denom==0):")
    print((monthly[LF1] + monthly[LF2]).head())


# -------------------------
# 6. Optional: rename columns
# -------------------------
monthly.columns.name = None  # remove multi-index name

# -------------------------
# 7. Save result
# -------------------------
monthly.to_csv(OUT_FILE, index=False)

print(monthly.head())



