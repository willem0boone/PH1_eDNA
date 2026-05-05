import os
import csv
import pandas as pd

LOOKUP_TABLE = "output/step2_dia_dino_table.csv"
DATA = "output/step1b_summed_tables.csv"
LF1 = "Diatom"
LF2 = "Dinoflagellate"
OUT_FILE = "output/step3_monthly_lifeform_aggregates_dino_dia.csv"

# -------------------------
# 1. Load data
# -------------------------
lookup = pd.read_csv(LOOKUP_TABLE)
non_aggregated = pd.read_csv(DATA)

# Ensure aphiaID is int in both (if present)
if 'aphiaID' in lookup.columns:
    lookup['aphiaID'] = lookup['aphiaID'].astype(int)
if 'aphiaID' in non_aggregated.columns:
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
# 3. Convert date to datetime and extract month period
# -------------------------
df['date'] = pd.to_datetime(df['date'], dayfirst=True)
df['month'] = df['date'].dt.to_period('M')  # Period like 2021-07

# -------------------------
# 4. Aggregate relative abundance per month × LifeformCategory (all categories)
# -------------------------
monthly_all = (
    df.groupby(['month', 'LifeformCategory'])['density']
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)

# Ensure columns name cleaned
monthly_all.columns.name = None

# Ensure LF1 and LF2 columns exist in the full pivot
for lf in (LF1, LF2):
    if lf not in monthly_all.columns:
        monthly_all[lf] = 0.0

# -------------------------
# 5. Build pairwise-relative dataframe (LF1 / (LF1+LF2)) scaled to 100
# -------------------------
pairwise = monthly_all[['month', LF1, LF2]].copy()
denom_pair = pairwise[LF1] + pairwise[LF2]
nonzero_pair = denom_pair != 0
pairwise.loc[nonzero_pair, LF1] = pairwise.loc[nonzero_pair, LF1] / denom_pair[nonzero_pair]
pairwise.loc[nonzero_pair, LF2] = pairwise.loc[nonzero_pair, LF2] / denom_pair[nonzero_pair]
pairwise.loc[~nonzero_pair, [LF1, LF2]] = 0.0
# scale to percentages
pairwise[[LF1, LF2]] = (pairwise[[LF1, LF2]] * 100).round(6)

# -------------------------
# 6. Build total-relative dataframe (LFx / sum(all lifeforms)) scaled to 100
# -------------------------
lifeform_columns = [c for c in monthly_all.columns if c != 'month']
total = monthly_all[lifeform_columns].sum(axis=1, min_count=1)
total_relative = monthly_all[['month', LF1, LF2]].copy()
nonzero_total = total != 0
total_relative.loc[nonzero_total, LF1] = monthly_all.loc[nonzero_total, LF1] / total[nonzero_total]
total_relative.loc[nonzero_total, LF2] = monthly_all.loc[nonzero_total, LF2] / total[nonzero_total]
total_relative.loc[~nonzero_total, [LF1, LF2]] = 0.0
# scale to percentages
total_relative[[LF1, LF2]] = (total_relative[[LF1, LF2]] * 100).round(6)

# -------------------------
# 7. Compute num_samples per month (unique dates)
# -------------------------
num_samples = (
    df.groupby('month')['date']
    .nunique()
    .reset_index(name='num_samples')
)

# Merge num_samples into both frames
pairwise = pairwise.merge(num_samples, on='month', how='left')
pairwise['num_samples'] = pairwise['num_samples'].fillna(0).astype(int)

total_relative = total_relative.merge(num_samples, on='month', how='left')
total_relative['num_samples'] = total_relative['num_samples'].fillna(0).astype(int)

# -------------------------
# 8. Create 'period' as string and reorder to required columns
# -------------------------
pairwise['period'] = pairwise['month'].astype(str)
pairwise = pairwise[['period', LF1, LF2, 'num_samples']]

total_relative['period'] = total_relative['month'].astype(str)
total_relative = total_relative[['period', LF1, LF2, 'num_samples']]

# -------------------------
# 9. Save CSVs
# -------------------------
os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
pairwise.to_csv(
    OUT_FILE,
    index=False,
    sep=",",
    decimal=".",
    quoting=csv.QUOTE_NONNUMERIC
)

total_out = os.path.splitext(OUT_FILE)[0] + "_relative.csv"
total_relative.to_csv(
    total_out,
    index=False,
    sep=",",
    decimal=".",
    quoting=csv.QUOTE_NONNUMERIC
)

# -------------------------
# 10. Sanity prints
# -------------------------
print(f"Saved pairwise file: {OUT_FILE}")
print(pairwise.head(20))
print("Pairwise LF1 + LF2 (first rows):")
print((pairwise[LF1] + pairwise[LF2]).head(10))
print(f"Saved total-relative file: {total_out}")
print(total_relative.head(20))
print("Total-relative LF1 + LF2 (first rows):")
print((total_relative[LF1] + total_relative[LF2]).head(10))
