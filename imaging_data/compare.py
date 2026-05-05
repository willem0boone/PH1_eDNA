import pandas as pd
from pathlib import Path

# Define file paths
IMAGING_FILE = Path(__file__).resolve().parent / "dump.csv"  # imaging data with lat/lon and lifeform
EDNA_FILE = Path(__file__).resolve().parent.parent / "output" / "step4_monthly_lifeform_species_summary.csv"
LOOKUP_FILE = Path(__file__).resolve().parent.parent / "lookup_tables" / "export_phytoplankton_type.csv"
OUT_FILE = Path(__file__).resolve().parent / "comparison_imaging_vs_edna.csv"
STATS_FILE = Path(__file__).resolve().parent / "comparison_statistics.csv"

# -------------------------
# 1. Load all data
# -------------------------
print("Loading data...")
imaging_df = pd.read_csv(IMAGING_FILE)
edna_df = pd.read_csv(EDNA_FILE)
lookup_df = pd.read_csv(LOOKUP_FILE, encoding='latin1')

print(f"Imaging rows: {len(imaging_df)}")
print(f"eDNA rows: {len(edna_df)}")
print(f"Lookup rows: {len(lookup_df)}")

# -------------------------
# 2. Clean and prepare lookup table
# -------------------------
lookup_df.columns = lookup_df.columns.str.strip()
lookup_df['AphiaID'] = lookup_df['AphiaID'].astype(int)
lookup_df['PhytoplanktonType'] = lookup_df['PhytoplanktonType'].str.strip()

# Keep only Diatom and Dinoflagellate
lookup_df = lookup_df[lookup_df['PhytoplanktonType'].isin(['Diatom', 'Dinoflagellate'])]

# Create mapping
aphia_to_lifeform = dict(zip(lookup_df['AphiaID'], lookup_df['PhytoplanktonType']))

# -------------------------
# 3. Add lifeform to imaging data
# -------------------------
imaging_df['aphiaid'] = imaging_df['aphiaid'].astype(int)
imaging_df['lifeform'] = imaging_df['aphiaid'].map(aphia_to_lifeform)

# Keep only rows with known lifeform
imaging_df = imaging_df.dropna(subset=['lifeform'])

# Rename columns to standardize
imaging_df = imaging_df.rename(columns={
    'abundance': 'imaging_density',
    'aphiaid': 'aphiaID'
})

imaging_agg = imaging_df.groupby(['period', 'lifeform', 'aphiaID'])['imaging_density'].sum().reset_index()

# Normalize imaging density per period so each month sums to 1
imaging_period_totals = imaging_agg.groupby('period')['imaging_density'].transform('sum')
imaging_agg['imaging_density'] = (imaging_agg['imaging_density'] / imaging_period_totals).fillna(0)

print(f"\nImaging data with lifeform: {len(imaging_agg)} rows")
print(f"Imaging periods: {sorted(imaging_agg['period'].unique())}")
print(f"Imaging lifeforms: {imaging_agg['lifeform'].unique()}")
print("Imaging per-period sums (should be 1.0):")
print(imaging_agg.groupby('period')['imaging_density'].sum().round(6))

# -------------------------
# 4. eDNA data structure: period, lifeform, aphiaID, density
# -------------------------
print(f"\neDNA data: {len(edna_df)} rows")
print(f"eDNA columns: {edna_df.columns.tolist()}")
print(f"eDNA periods: {sorted(edna_df['period'].unique())}")
print(f"eDNA lifeforms: {edna_df['lifeform'].unique()}")

# -------------------------
# 5. Merge imaging and eDNA data
# -------------------------
comparison = imaging_agg.merge(
    edna_df[['period', 'lifeform', 'aphiaID', 'density']],
    on=['period', 'lifeform', 'aphiaID'],
    how='outer'
)

# Rename eDNA density column
comparison = comparison.rename(columns={'density': 'edna_density'})

# Fill missing values with 0 for comparison
comparison['imaging_density'] = comparison['imaging_density'].fillna(0)
comparison['edna_density'] = comparison['edna_density'].fillna(0)

# Drop rows where both densities are zero
comparison = comparison[~((comparison['imaging_density'] == 0) & (comparison['edna_density'] == 0))].copy()

# -------------------------
# 6. Sort for readability
# -------------------------
comparison = comparison.sort_values(['period', 'lifeform', 'aphiaID']).reset_index(drop=True)

# -------------------------
# 7. Save comparison
# -------------------------
comparison.to_csv(OUT_FILE, index=False)
print(f"\nSaved comparison to: {OUT_FILE}")
print(f"Total comparison rows: {len(comparison)}")
print("\nFirst 30 rows:")
print(comparison.head(30))

# -------------------------
# 8. Generate statistics
# -------------------------
stats_data = {
    'Metric': [
        'Total periods',
        'Periods in imaging',
        'Periods in eDNA',
        'Unique lifeforms',
        'Unique aphiaIDs (imaging)',
        'Unique aphiaIDs (eDNA)',
        'Total imaging density (sum)',
        'Total eDNA density (sum)',
        'Mean imaging density',
        'Mean eDNA density',
        'Max imaging density',
        'Max eDNA density',
        'Rows with both imaging & eDNA',
        'Rows imaging only',
        'Rows eDNA only'
    ],
    'Value': [
        len(comparison['period'].unique()),
        imaging_agg['period'].nunique(),
        edna_df['period'].nunique(),
        comparison['lifeform'].nunique(),
        imaging_agg['aphiaID'].nunique(),
        edna_df['aphiaID'].nunique(),
        f"{comparison['imaging_density'].sum():.6f}",
        f"{comparison['edna_density'].sum():.6f}",
        f"{comparison['imaging_density'].mean():.6f}",
        f"{comparison['edna_density'].mean():.6f}",
        f"{comparison['imaging_density'].max():.6f}",
        f"{comparison['edna_density'].max():.6f}",
        len(comparison[(comparison['imaging_density'] > 0) & (comparison['edna_density'] > 0)]),
        len(comparison[(comparison['imaging_density'] > 0) & (comparison['edna_density'] == 0)]),
        len(comparison[(comparison['imaging_density'] == 0) & (comparison['edna_density'] > 0)])
    ]
}

stats_df = pd.DataFrame(stats_data)
stats_df.to_csv(STATS_FILE, index=False)

print(f"\nSaved statistics to: {STATS_FILE}")
print("\nComparison Statistics:")
print(stats_df.to_string(index=False))

# -------------------------
# 9. Summary by period and lifeform
# -------------------------
print("\n\nSummary by Period and Lifeform (species_count = number of aphiaIDs):")
summary_by_group = (
    comparison.groupby(['period', 'lifeform'])
    .agg({
        'imaging_density': 'sum',
        'edna_density': 'sum',
        'aphiaID': 'count'
    })
    .reset_index()
    .rename(columns={'aphiaID': 'species_count'})
)
print(summary_by_group.to_string(index=False))








