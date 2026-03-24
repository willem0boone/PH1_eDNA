import pandas as pd

print("-"*50)
otu = pd.read_csv("data/otu_Belgium_PLET.tsv", sep="\t")
print(otu.head())

print("-"*50)
taxo = pd.read_csv("data/taxonomy_belgium_PLET.tsv",
                   sep="\t",
                   usecols=("NCBI_Taxid", "scientificName", "scientificNameID"))
print(taxo.head())

print("-"*50)
dates = pd.read_csv("data/dates.csv")
print(dates.head())

print("-"*50)
# 1. Melt the OTU dataframe so that each sample column becomes a row
otu_long = otu.melt(id_vars="NCBI_Taxid", var_name="CODE", value_name="density")

# 2. Merge with dates to get the actual date
otu_long = otu_long.merge(dates[['CODE', 'date']], on='CODE', how='left')

# 3. Merge with taxonomy to get aphiaID and scientificName
otu_long = otu_long.merge(taxo, on='NCBI_Taxid', how='left')

# 4. Keep only the desired columns and rename
final_table = otu_long[['date', 'scientificNameID', 'scientificName', 'density']].rename(
    columns={'scientificNameID': 'aphiaID'}
)

# Optional: sort by date and aphiaID
final_table = final_table.sort_values(['date', 'aphiaID']).reset_index(drop=True)


# Save to a new CSV if needed
final_table.to_csv("output/non_aggregated_data.csv", index=False)

print("-"*50)
print(final_table.head())

