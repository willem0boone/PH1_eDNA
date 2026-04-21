import pandas as pd
import requests
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import plotly.express as px
from matplotlib import colors as mcolors

# ------------------------
# Config
# ------------------------
INPUT_DIR = Path("output/per_date")
OUTPUT_DIR = Path("plots/sunburst_per_date")
CACHE_FILE = Path("cache/aphia_cache.json")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

# ------------------------
# Load cache
# ------------------------
aphia_cache = {}
if CACHE_FILE.exists():
    try:
        with open(CACHE_FILE, "r") as f:
            aphia_cache = json.load(f)
    except Exception:
        aphia_cache = {}

cache_lock = threading.Lock()

# ------------------------
# WoRMS API
# ------------------------
def get_aphia_record(aphia_id):
    aphia_id = str(int(aphia_id))

    if aphia_id in aphia_cache:
        return aphia_cache[aphia_id]

    url = f"https://www.marinespecies.org/rest/AphiaRecordByAphiaID/{aphia_id}"

    try:
        print(f"Fetching {aphia_id}")
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        data = None

    with cache_lock:
        aphia_cache[aphia_id] = data

    return data

# ------------------------
# Build taxonomy
# ------------------------
def build_taxonomy(df, max_threads=10):
    results = []

    def worker(row):
        rec = get_aphia_record(row["aphiaID"])
        if not rec:
            return None

        taxonomy = [
            rec.get("kingdom"),
            rec.get("phylum"),
            rec.get("class"),
            rec.get("order"),
            rec.get("family"),
            rec.get("genus"),
        ]

        sci = rec.get("scientificname")
        if sci not in taxonomy:
            taxonomy.append(sci)
        else:
            taxonomy.append(None)

        return {
            "taxonomy": taxonomy,
            "count": row["rel_abundance"]
        }

    with ThreadPoolExecutor(max_workers=max_threads) as ex:
        futures = [ex.submit(worker, row) for _, row in df.iterrows()]
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    return results

# ------------------------
# Sunburst builder
# ------------------------
def build_sunburst_df(taxonomy_data):
    rows = []

    for rec in taxonomy_data:
        path = []
        for val in rec["taxonomy"]:
            if val is None:
                break
            path.append(val)

        value = rec["count"]

        for i, name in enumerate(path):
            node_id = "|".join(path[:i+1])
            parent = "" if i == 0 else "|".join(path[:i])
            val = value if i == len(path)-1 else 0

            rows.append({
                "id": node_id,
                "label": name,
                "parent": parent,
                "value": val
            })

    df = pd.DataFrame(rows)
    df = df.groupby(["id", "label", "parent"], as_index=False)["value"].sum()
    return df

# ------------------------
# Colors
# ------------------------
def assign_colors(df):
    base = "#033f69"
    rgb = mcolors.to_rgb(base)

    colors = []
    for _, row in df.iterrows():
        depth = len(row["id"].split("|")) - 1
        factor = 1 + depth * 0.18
        shaded = [min(1, c * factor) for c in rgb]
        colors.append(f"rgb({int(shaded[0]*255)}, {int(shaded[1]*255)}, {int(shaded[2]*255)})")

    return colors

# ------------------------
# MAIN
# ------------------------
if __name__ == "__main__":

    for csv_file in INPUT_DIR.glob("*.csv"):
        print(f"Processing {csv_file.name}")

        df = pd.read_csv(csv_file)

        # Aggregate per AphiaID
        df_agg = (
            df.groupby(["aphiaID", "scientificName"], as_index=False)
            ["rel_abundance"]
            .sum()
        )

        taxonomy_data = build_taxonomy(df_agg)

        df_sb = build_sunburst_df(taxonomy_data)
        colors = assign_colors(df_sb)

        fig = px.sunburst(
            df_sb,
            ids="id",
            names="label",
            parents="parent",
            values="value"
        )

        fig.update_traces(marker=dict(colors=colors))
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))

        out_file = OUTPUT_DIR / f"{csv_file.stem}.html"
        fig.write_html(out_file)

        print(f"Saved: {out_file}")

    # Save cache
    with open(CACHE_FILE, "w") as f:
        json.dump(aphia_cache, f, indent=2)

    print("Done.")


