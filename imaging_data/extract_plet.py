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

# Convert the abundance columns to numeric (coerce invalid values)
df[lifeform_cols] = df[lifeform_cols].apply(pd.to_numeric, errors="coerce")

# Compute denominator using only diatom + dinoflagellate.
# Use the same sum semantics as before: if one is NaN and the other present,
# sum returns the present value (min_count=1). If both are NaN -> denom is NaN.
denom = df[["diatom", "dinoflagellate"]].sum(axis=1, min_count=1)

# Build output frame with selected columns and compute pairwise relative values.
relative_df = df[selected_cols].copy()
relative_df["diatom"] = df["diatom"] / denom
relative_df["dinoflagellate"] = df["dinoflagellate"] / denom

# Rows where denom is zero or NaN -> set both normalized columns to missing
mask_invalid = denom.isna() | (denom == 0)
relative_df.loc[mask_invalid, ["diatom", "dinoflagellate"]] = pd.NA

# Keep only rows where both relative values are available (same as before)
relative_df = relative_df.dropna(subset=["diatom", "dinoflagellate"])

# Round to 3 decimal places (same as you used before)
relative_df[["diatom", "dinoflagellate"]] = relative_df[["diatom", "dinoflagellate"]].round(3)


OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
relative_df.to_csv(OUT_FILE, index=False, sep=";", decimal=",")

print(f"Saved relative imaging table to: {OUT_FILE}")
print(relative_df.head(10))

