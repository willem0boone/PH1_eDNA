import csv
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_FILE = BASE_DIR / "data" / "lifeform.csv"

# Keep the current pairwise export as the main imaging.csv output.
PAIRWISE_OUT_FILE = BASE_DIR / "output" / "imaging_relative_pairwise.csv"
# New export: diatom and dinoflagellate relative to total lifeform count.
TOTAL_OUT_FILE = BASE_DIR / "output" / "imaging_relative_total.csv"
# Original (no normalization) export
ORIG_OUT_FILE = BASE_DIR / "output" / "imaging_original.csv"

META_COLS = {"period", "numSamples", "abundanceType", "taxa used"}
FINAL_COLS = ["period", "diatom", "dinoflagellate", "num_samples"]


def build_output_frame(source_df: pd.DataFrame) -> pd.DataFrame:
	frame = source_df[["period", "numSamples", "diatom", "dinoflagellate"]].copy()
	frame = frame.rename(columns={"numSamples": "num_samples"})
	if "num_samples" not in frame.columns:
		frame["num_samples"] = pd.NA
	frame["period"] = frame["period"].astype(str)
	for col in FINAL_COLS:
		if col not in frame.columns:
			frame[col] = pd.NA
	return frame[FINAL_COLS]


def normalize_pairwise(source_df: pd.DataFrame) -> pd.DataFrame:
	denom = source_df[["diatom", "dinoflagellate"]].sum(axis=1, min_count=1)
	out = build_output_frame(source_df)
	out["diatom"] = source_df["diatom"] / denom
	out["dinoflagellate"] = source_df["dinoflagellate"] / denom
	mask_invalid = denom.isna() | (denom == 0)
	out.loc[mask_invalid, ["diatom", "dinoflagellate"]] = pd.NA
	out = out.dropna(subset=["diatom", "dinoflagellate"])
	out[["diatom", "dinoflagellate"]] = (out[["diatom", "dinoflagellate"]] * 100).round(3)
	return out


def normalize_total(source_df: pd.DataFrame, lifeform_cols: list[str]) -> pd.DataFrame:
	total = source_df[lifeform_cols].sum(axis=1, min_count=1)
	out = build_output_frame(source_df)
	out["diatom"] = source_df["diatom"] / total
	out["dinoflagellate"] = source_df["dinoflagellate"] / total
	mask_invalid = total.isna() | (total == 0)
	out.loc[mask_invalid, ["diatom", "dinoflagellate"]] = pd.NA
	out = out.dropna(subset=["diatom", "dinoflagellate"])
	out[["diatom", "dinoflagellate"]] = (out[["diatom", "dinoflagellate"]] * 100).round(3)
	return out


def save_csv(frame: pd.DataFrame, output_file: Path) -> None:
	output_file.parent.mkdir(parents=True, exist_ok=True)
	frame.to_csv(
		output_file,
		index=False,
		sep=",",
		decimal=".",
		quoting=csv.QUOTE_NONNUMERIC,
	)


df = pd.read_csv(SOURCE_FILE)
lifeform_cols = [col for col in df.columns if col not in META_COLS]

# Convert lifeform columns to numeric once, then reuse for both exports.
df[lifeform_cols] = df[lifeform_cols].apply(pd.to_numeric, errors="coerce")

# --- Save original (no normalization) ---
orig_df = build_output_frame(df)
# Drop rows where both diatom and dinoflagellate are missing/empty
orig_df = orig_df.dropna(subset=["diatom", "dinoflagellate"], how="all")
save_csv(orig_df, ORIG_OUT_FILE)
print(f"Saved original imaging table to: {ORIG_OUT_FILE}")
print(orig_df.head(10))

pairwise_df = normalize_pairwise(df)
total_df = normalize_total(df, lifeform_cols)

save_csv(pairwise_df, PAIRWISE_OUT_FILE)
save_csv(total_df, TOTAL_OUT_FILE)

print(f"Saved pairwise relative imaging table to: {PAIRWISE_OUT_FILE}")
print(pairwise_df.head(10))
print(f"Saved total-relative imaging table to: {TOTAL_OUT_FILE}")
print(total_df.head(10))
