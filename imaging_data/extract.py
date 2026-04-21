from urllib.parse import parse_qs, urlparse

import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.fs as fs

import pandas as pd
import geopandas as gpd
import yaml
import re
import matplotlib.pyplot as plt

# ------------------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------------------
occurrence_data = "https://datalab.dive.edito.eu/data-explorer?source=https://s3.waw3-1.cloudferro.com/emodnet/emodnet_biology/12639/marine_biodiversity_observations_2026-02-26.parquet"

dasid = 4687
parameter = "WaterAbund (#/ml)"
MY_REGION = "SNS"

# ------------------------------------------------------------------------------
# PARSE URL
# ------------------------------------------------------------------------------
outer_url = urlparse(occurrence_data)
source_url = parse_qs(outer_url.query).get("source", [occurrence_data])[0]
parsed_url = urlparse(source_url)

host = parsed_url.hostname
bucket_name = parsed_url.path.split('/')[1]
key = '/'.join(parsed_url.path.split('/')[2:])

# ------------------------------------------------------------------------------
# LOAD DATASET (Arrow)
# ------------------------------------------------------------------------------
s3 = fs.S3FileSystem(endpoint_override=host, anonymous=True)
dataset_path = f"{bucket_name}/{key}"

dataset = ds.dataset(dataset_path, filesystem=s3, format="parquet")

# ------------------------------------------------------------------------------
# FILTER (Arrow level)
# ------------------------------------------------------------------------------
filter_expression = (
    (pc.field("parameter_imisdasid") == dasid) &
    (pc.field("parameter") == parameter) &
    (pc.field("eventtype") == "sample")
)

columns = [
    "parameter",
    "parameter_value",
    "event_id",
    "scientificname_accepted",
    "observationdate",
    "eventtype",
    "longitude",
    "latitude"
]

filtered_table = dataset.to_table(columns=columns, filter=filter_expression)

# ------------------------------------------------------------------------------
# CONVERT TO PANDAS
# ------------------------------------------------------------------------------
df = filtered_table.to_pandas()

# ------------------------------------------------------------------------------
# TRIP ACTION FILTER
# ------------------------------------------------------------------------------
trip_actions = pd.read_csv("lookup_tables/allTripActions_exp.csv")

df["TripActionID"] = (
    df["event_id"]
    .str.extract(r"(TripActionID\d+)")
    .iloc[:, 0]
    .str.replace("TripActionID", "", regex=False)
)

df["TripActionID"] = pd.to_numeric(df["TripActionID"], errors="coerce")

df = df[df["TripActionID"].isin(trip_actions["Tripaction"])]

# ------------------------------------------------------------------------------
# OSPAR REGION FUNCTIONS (Python equivalent of R sf code)
# ------------------------------------------------------------------------------

OSPAR_GEOJSON_URL = "https://odims.ospar.org/geoserver/odims/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=ospar_comp_au_2023_01_001&outputFormat=json"

def load_ospar_region(region_id="SNS"):
    gdf = gpd.read_file(OSPAR_GEOJSON_URL)
    region = gdf[gdf["ID"] == region_id]

    if region.empty:
        raise ValueError(f"Region ID {region_id} not found")

    return region


def filter_and_plot_region_selection(region_id, df, filename):
    # Load region polygon
    region = load_ospar_region(region_id)

    # Drop NA coordinates
    df_clean = df.dropna(subset=["longitude", "latitude"])

    # Convert to GeoDataFrame
    gdf_points = gpd.GeoDataFrame(
        df_clean,
        geometry=gpd.points_from_xy(df_clean["longitude"], df_clean["latitude"]),
        crs="EPSG:4326"
    )

    # Spatial join (equivalent to st_within)
    gdf_inside = gpd.sjoin(gdf_points, region, predicate="within", how="inner")

    # Plot
    fig, ax = plt.subplots(figsize=(8, 6))

    region.plot(ax=ax, edgecolor="blue", facecolor="lightblue", alpha=0.2)
    gdf_points.plot(ax=ax, color="gray", markersize=5, alpha=0.5)
    gdf_inside.plot(ax=ax, color="red", markersize=10, alpha=0.8)

    ax.set_title(
        f"Spatial Distribution\nRed: Inside {region_id} | Gray: All | Blue: Boundary"
    )

    plt.savefig(filename, dpi=300)
    plt.close()

    return pd.DataFrame(gdf_inside.drop(columns="geometry"))


# ------------------------------------------------------------------------------
# APPLY REGION FILTER
# ------------------------------------------------------------------------------
df = filter_and_plot_region_selection(
    MY_REGION,
    df,
    f"EDITO_dasid_4687_{MY_REGION}.png"
)

# ------------------------------------------------------------------------------
# SUBSET + FORMAT
# ------------------------------------------------------------------------------
df = df[[
    "parameter",
    "parameter_value",
    "observationdate",
    "scientificname_accepted",
    "eventtype",
    "event_id"
]].rename(columns={
    "parameter_value": "abundance",
    "event_id": "eventid"
})

df["abundance"] = pd.to_numeric(df["abundance"], errors="coerce")

df["Time"] = pd.to_datetime(df["observationdate"])
df["period"] = df["Time"].dt.to_period("M").astype(str)

# ------------------------------------------------------------------------------
# LIFEFORM CLASSIFICATION
# ------------------------------------------------------------------------------
with open("lookup_tables/lifeform_lookup_zooplankton.yaml") as f:
    lifeform_map = yaml.safe_load(f)

def classify_lifeform(species):
    for group, species_list in lifeform_map.items():
        if species in species_list:
            return group
    return None

df["lifeform"] = df["scientificname_accepted"].apply(classify_lifeform)

df = df.dropna(subset=["lifeform"])

# ------------------------------------------------------------------------------
# FILTER HOLO + MERO
# ------------------------------------------------------------------------------
df = df[df["lifeform"].isin(["holoplankton", "meroplankton"])]

# ------------------------------------------------------------------------------
# AGGREGATION
# ------------------------------------------------------------------------------
df_grouped = (
    df.groupby(["period", "lifeform", "eventid"], as_index=False)
    .agg(abundance=("abundance", "sum"))
)

df_grouped["num_samples"] = 1

df_grouped = (
    df_grouped.groupby(["period", "lifeform"], as_index=False)
    .agg(
        abundance=("abundance", "sum"),
        num_samples=("num_samples", "sum")
    )
)

df_grouped["abundance"] = df_grouped["abundance"] / df_grouped["num_samples"]

# ------------------------------------------------------------------------------
# WIDE FORMAT
# ------------------------------------------------------------------------------
wide_df = df_grouped.pivot_table(
    index="period",
    columns="lifeform",
    values="abundance",
    fill_value=0
).reset_index()

samples_df = (
    df_grouped.groupby("period", as_index=False)
    .agg(num_samples=("num_samples", "sum"))
)

wide_df = wide_df.merge(samples_df, on="period", how="left")

# reorder columns
cols = ["period"] + \
       [c for c in wide_df.columns if c not in ["period", "num_samples"]] + \
       ["num_samples"]

wide_df = wide_df[cols]

# ------------------------------------------------------------------------------
# SAVE OUTPUT
# ------------------------------------------------------------------------------
dest = f"EDITO_dasid_4687_{MY_REGION}_PH1_holo_mero.csv"
wide_df.to_csv(dest, index=False)

print("Finished ETL: wide-format CSV ready for PH1 analysis")