import pandas as pd

INPUT_FILE = "output/step1b_summed_tables.csv"
PLET_LF_CAT = "lookup_tables/export_phytoplankton_type.csv"
COL_NAME = "PhytoplanktonType"
TYPE1 = "Diatom"
TYPE2 = "Dinoflagellate"
OUT_FILE = "output/step2_dia_dino_table.csv"

# -------------------------
# 1. Load merged tables
# -------------------------
otu_long = pd.read_csv(INPUT_FILE)

# Ensure aphiaID is integer
otu_long['aphiaID'] = otu_long['aphiaID'].astype(int)

# -------------------------
# 2. Load lifeform lookup table
# -------------------------
# the lookup table is manualy extracted from PLET masterlist

lookup = pd.read_csv(PLET_LF_CAT, encoding='latin1')

# Remove rows where duppl is True
lookup = lookup[lookup['duppl'] != True]

print(lookup.head(10))
print(len(lookup))

# Clean columns and string values
lookup.columns = lookup.columns.str.strip()
lookup['Taxon'] = lookup['Taxon'].str.strip()
lookup[COL_NAME] = lookup[COL_NAME].str.strip()

# Ensure AphiaID is integer
lookup['AphiaID'] = lookup['AphiaID'].astype(int)

# -------------------------
# 3. Create mapping: 
# -------------------------
aphia_to_habitat = dict(zip(lookup['AphiaID'], lookup[COL_NAME]))


# -------------------------
# 4. Function to assign category
# -------------------------
def categorize(aphia_id):
    habitat = aphia_to_habitat.get(aphia_id)
    if habitat == TYPE1:
        return TYPE1
    elif habitat == TYPE2:
        return TYPE2
    elif habitat is not None and habitat not in [TYPE1, TYPE2, '']:
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
final_table.to_csv(OUT_FILE, index=False)

# -------------------------
# 8. Print counts per category
# -------------------------
category_counts = final_table['LifeformCategory'].value_counts()
print("Counts per lifeform category:")
print(category_counts)
