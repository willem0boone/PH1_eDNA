import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_FILE = BASE_DIR / "data" / "lifeform.csv"
OUT_FILE = BASE_DIR / "output" / "imaging.csv"

df = pd.read_csv(str(SOURCE_FILE))

selected_cols = ["period", "numSamples", "diatom", "dinoflagellate"]
lifeform_cols = [
	col
	for col in df.columns
	if col not in {"period", "numSamples", "abundanceType", "taxa used"}
]

# Convert the abundance columns to numeric and treat missing values as 0 for
# the purpose of the row-wise normalization.
df[lifeform_cols] = df[lifeform_cols].apply(pd.to_numeric, errors="coerce")
row_total = df[lifeform_cols].sum(axis=1, min_count=1)

relative_df = df[selected_cols].copy()
for col in ["diatom", "dinoflagellate"]:
	relative_df[col] = df[col] / row_total

# Avoid dividing rows with no usable values; keep them as missing.
relative_df.loc[row_total.isna() | (row_total == 0), ["diatom", "dinoflagellate"]] = pd.NA

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
relative_df.to_csv(OUT_FILE, index=False)

print(f"Saved relative imaging table to: {OUT_FILE}")
print(relative_df.head(10))

