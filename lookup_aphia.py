import pandas as pd

# -------------------------
# 1. Load OTU table
# -------------------------
otu_long = pd.read_csv("output/non_aggregated_data.csv")  # must contain 'aphiaID' and 'scientificName'

# Ensure aphiaID is integer
otu_long['aphiaID'] = otu_long['aphiaID'].astype(int)

# -------------------------
# 2. Load lifeform lookup table
# -------------------------
lookup = pd.read_csv("lookup_tables/export_zoo_habitat.csv", encoding='latin1')  # handles special characters

# Clean columns and string values
lookup.columns = lookup.columns.str.strip()
lookup['Taxon'] = lookup['Taxon'].str.strip()
lookup['ZooHabitat'] = lookup['ZooHabitat'].str.strip()

# Ensure AphiaID is integer
lookup['AphiaID'] = lookup['AphiaID'].astype(int)

# -------------------------
# 3. Create mapping: AphiaID -> ZooHabitat
# -------------------------
aphia_to_habitat = dict(zip(lookup['AphiaID'], lookup['ZooHabitat']))

# -------------------------
# 4. Function to assign category
# -------------------------
def categorize(aphia_id):
    habitat = aphia_to_habitat.get(aphia_id)
    if habitat == 'Holoplankton':
        return 'Holoplankton'
    elif habitat == 'Meroplankton':
        return 'Meroplankton'
    elif habitat is not None and habitat not in ['Holoplankton', 'Meroplankton', '']:
        return 'Other'
    else:
        return 'Undefined'

# -------------------------
# 5. Apply categorization
# -------------------------
otu_long['LifeformCategory'] = otu_long['aphiaID'].apply(categorize)

# -------------------------
# 6. Create final table
# -------------------------
final_table = otu_long[['aphiaID', 'scientificName', 'LifeformCategory']].drop_duplicates()

# -------------------------
# 7. Save to CSV
# -------------------------
final_table.to_csv("output/holo_mero_table.csv", index=False)

# -------------------------
# 8. Print counts per category
# -------------------------
category_counts = final_table['LifeformCategory'].value_counts()
print("Counts per lifeform category:")
print(category_counts)