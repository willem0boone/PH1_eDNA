import pandas as pd

LOOKUP_TABLE = "output/step2_dia_dino_table.csv"
DATA = "output/step1b_summed_tables.csv"
OUT_FILE = "output/step4_monthly_lifeform_species_summary.csv"

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
df['period'] = df['date'].dt.to_period('M').astype(str)  # e.g., '2017-01'

# -------------------------
# 4. Aggregate density per period × LifeformCategory × aphiaID
# -------------------------
# Group by period, LifeformCategory, and aphiaID, then sum the density
summary = (
    df.groupby(['period', 'LifeformCategory', 'aphiaID'])['density']
    .sum()
    .reset_index()
)


# Rename 'LifeformCategory' to 'lifeform' for shorter column names
summary = summary.rename(columns={'LifeformCategory': 'lifeform'})

# -------------------------
# 5. Reorder columns to match requested output: period, lifeform, aphiaID, density
# -------------------------
summary = summary[['period', 'lifeform', 'aphiaID', 'density']]

# -------------------------
# 5b. Convert to relative densities per period
# -------------------------
period_totals = summary.groupby('period')['density'].transform('sum')
summary['density'] = (summary['density'] / period_totals).fillna(0).round(10)

# -------------------------
# 6. Sort by period, lifeform, aphiaID for readability
# -------------------------
summary = summary.sort_values(['period', 'lifeform', 'aphiaID']).reset_index(drop=True)

# -------------------------
# 7. Save to CSV
# -------------------------
summary.to_csv(OUT_FILE, index=False)

# -------------------------
# 8. Print sample output and statistics
# -------------------------
print(f"Saved summarized table to: {OUT_FILE}")
print(f"Total rows: {len(summary)}")
print("\nFirst 20 rows:")
print(summary.head(20))

# Quick check: each period should sum to 1 (or 0 if empty)
period_check = summary.groupby('period')['density'].sum().round(6)
print("\nPer-period density sums (should be 1.0):")
print(period_check)

print("\nSummary statistics:")
print(f"Unique periods: {summary['period'].nunique()}")
print(f"Unique lifeforms: {summary['lifeform'].unique()}")
print(f"Unique aphiaIDs: {summary['aphiaID'].nunique()}")
print(f"\nDensity range: {summary['density'].min():.6f} to {summary['density'].max():.6f}")

# -------------------------
# 9. Export summary statistics to CSV
# -------------------------
stats_out = OUT_FILE.replace('.csv', '_statistics.csv')
stats_data = {
    'Metric': [
        'Total rows',
        'Unique periods',
        'Unique lifeforms',
        'Unique aphiaIDs',
        'Min density',
        'Max density',
        'Mean density',
        'Median density'
    ],
    'Value': [
        len(summary),
        summary['period'].nunique(),
        ', '.join(summary['lifeform'].unique()),
        summary['aphiaID'].nunique(),
        f"{summary['density'].min():.6f}",
        f"{summary['density'].max():.6f}",
        f"{summary['density'].mean():.6f}",
        f"{summary['density'].median():.6f}"
    ]
}

stats_df = pd.DataFrame(stats_data)
stats_df.to_csv(stats_out, index=False)
print(f"\nSaved summary statistics to: {stats_out}")
print(stats_df.to_string(index=False))
