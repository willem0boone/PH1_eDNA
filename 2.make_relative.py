import pandas as pd
from pathlib import Path

DATA_ABS = "output/step1b_summed_tables.csv"
OUT_FILE = "output/step2_data_rel.csv"

OUT_DIR = Path("output/per_date")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_ABS)

# Compute relative abundance per date
df["rel_abundance"] = df["density"] / df.groupby("date")["density"].transform("sum")

# Drop 'type' column
df = df.drop(columns=["type"])

print(df.head())

# Save full dataset
df.to_csv(OUT_FILE, index=False)

# 🔹 Save one CSV per date
for date, subdf in df.groupby("date"):
    safe_date = date.replace("/", "-")
    out_path = OUT_DIR / f"data_{safe_date}.csv"
    subdf.to_csv(out_path, index=False)

print(f"Saved per-date CSVs to: {OUT_DIR}")

print("-" * 50)
print("Checking relative abundance sums per date:")

# 🔍 Validation step
for csv_file in OUT_DIR.glob("*.csv"):
    df_check = pd.read_csv(csv_file)

    total = df_check["rel_abundance"].sum()

    print(f"{csv_file.name}: {total:.6f}")

