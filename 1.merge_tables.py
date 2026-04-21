import pandas as pd

print("-" * 50)
# Load OTU table
otu = pd.read_csv("data/otu_Belgium_PLET.tsv", sep="\t")

# Drop rows where all sample columns are 0
otu = otu[(otu.drop(columns=["NCBI_Taxid"]) != 0).any(axis=1)]
print(otu.head())
print(f"Number of OTU rows after dropping all-zero rows: {len(otu)}")


print("-" * 50)
# Load taxonomy table
taxo = pd.read_csv(
    "data/taxonomy_belgium_PLET.tsv",
    sep="\t",
    usecols=("NCBI_Taxid", "scientificName", "scientificNameID")
)
print(taxo.head())


print("-" * 50)
# Load dates table
dates = pd.read_csv("data/dates.csv")

# Exclude sediment samples
dates = dates[dates["type"] != "sediment"]

print(dates.head())
print(f"Number of samples after removing sediment: {len(dates)}")


print("-" * 50)
# Melt OTU table (wide → long)
otu_long = otu.melt(
    id_vars="NCBI_Taxid",
    var_name="CODE",
    value_name="density"
)

# Merge with metadata (date, type, fraction)
otu_long = otu_long.merge(
    dates[['CODE', 'date', 'type', 'fraction']],
    on='CODE',
    how='left'
)

# Merge taxonomy
otu_long = otu_long.merge(
    taxo,
    on='NCBI_Taxid',
    how='left'
)

# Build working table
table = otu_long[
    ['date', 'type', 'fraction', 'scientificNameID', 'scientificName', 'density']
].rename(columns={'scientificNameID': 'aphiaID'})

print(table.head())


print("-" * 50)
# STEP 1: Average replicates (same date + type + fraction)
avg_table = (
    table
    .groupby(['date', 'type', 'fraction', 'aphiaID', 'scientificName'], as_index=False)
    ['density']
    .mean()
)

print("After replicate averaging:")
print(avg_table.head())


print("-" * 50)
# STEP 2: Sum across fractions (same date + type)
summed_table = (
    avg_table
    .groupby(['date', 'type', 'aphiaID', 'scientificName'], as_index=False)
    ['density']
    .sum()
)

print("After fraction summation:")
print(summed_table.head())


print("-" * 50)
# Sort outputs
avg_table = avg_table.sort_values(['date', 'aphiaID']).reset_index(drop=True)
summed_table = summed_table.sort_values(['date', 'aphiaID']).reset_index(drop=True)

avg_table.to_csv("output/step1a_averaged_tables.csv", index=False)
summed_table.to_csv("output/step1b_summed_tables.csv", index=False)

print("Files saved:")
print("- output/replicate_averaged.csv")
print("- output/aggregated_data.csv")
